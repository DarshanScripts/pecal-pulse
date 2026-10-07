"""MR7 EDA, chronological forecasting and censored recurrence benchmark.

Run with uv run python analysis/train_capacity_models.py after the SQL export.
Produces a small, anonymous payload for the standalone HTML planner.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import json
from pathlib import Path
from collections import defaultdict,Counter
from datetime import date,timedelta,datetime,timezone
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor,HistGradientBoostingClassifier
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss

ROOT=Path(__file__).parent/'mr7'
LAB='MR7'
rng=np.random.default_rng(42)
def load(name):
    return json.loads((ROOT/f'{name}.json').read_text())
def day(s):
    return date.fromisoformat(s[:10])
def monday(d):
    return d-timedelta(days=d.weekday())
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(np.floating,)):return float(v) if np.isfinite(v) else None
    if isinstance(v,(np.ndarray,)):return clean(v.tolist())
    return v

meta={r['dataset']:r['last_date'] for r in load('source_metadata')}
cal_cutoff=day(meta['calibrations'])
last_cal_week=monday(cal_cutoff)-timedelta(days=7)
first=date(2024,1,1)
weeks=[first+timedelta(days=7*i) for i in range((last_cal_week-first).days//7+1)]
labs=sorted({r['lab'] for r in load('weekly_calibrations') if r['lab'] and r['lab'].startswith('MR')})
mi=labs.index(LAB)

def series(name,value,datekey='week'):
    by=defaultdict(dict)
    for r in load(name):
        if r['lab'] in labs:
            w=monday(day(r[datekey]))
            if r[value] is not None:
                by[r['lab']][w]=by[r['lab']].get(w,0)+float(r[value])
    a=np.full((len(labs),len(weeks)),np.nan)
    for li,lab in enumerate(labs):
        if not by[lab]:continue
        lo,hi=min(by[lab]),max(by[lab])
        for t,w in enumerate(weeks):
            if lo<=w<=hi:a[li,t]=by[lab].get(w,0)
    return a

counts=series('weekly_calibrations','calibrations')
work=series('weekly_workload','standard_hours')
attendance=series('actual_capacity','attendance_hours','day')
att_end=monday(day(meta['actual_capacity']))-timedelta(days=7)
for t,w in enumerate(weeks):
    if w>att_end:attendance[:,t]=np.nan

def feature(a,t,li):
    prior=np.array(a[t-13:t],dtype=float)
    recent=float(np.nanmean(prior[-4:]))
    previous=float(np.nanmean(prior[-8:-4]))
    year=a[t-52] if t>=52 else np.nan
    return [np.log1p(a[t-1]),np.log1p(recent),np.log1p(np.nanmean(prior)),
        np.log1p(year),np.log1p(recent)-np.log1p(previous),
        np.sin(2*np.pi*t/52.18),np.cos(2*np.pi*t/52.18)]+[int(li==j) for j in range(len(labs)-1)]

def metrics(y,p):
    return {'wape':float(np.abs(y-p).sum()/y.sum()),'mae':float(np.abs(y-p).mean()),
        'bias':float((p-y).sum()/y.sum()),'rows':len(y)}

def fit_forecast(a,label):
    X,Y,D,L,IDX=[],[],[],[],[]
    for li in range(len(labs)):
        for t in range(13,len(weeks)):
            if not np.isfinite(a[li,t]) or not np.all(np.isfinite(a[li,t-13:t])):continue
            X.append(feature(a[li],t,li));Y.append(a[li,t]);D.append(weeks[t]);L.append(li);IDX.append(t)
    X,Y,L,IDX=np.array(X),np.array(Y),np.array(L),np.array(IDX)
    tr=np.array([d<=date(2025,6,30) for d in D])
    va=np.array([date(2025,7,1)<=d<=date(2025,9,30) for d in D])
    te=np.array([date(2025,10,1)<=d for d in D])
    candidates={
        'Recent 4-week mean':None,'Seasonal 52-week baseline':None,
        'Ridge regression':make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),Ridge(alpha=10)),
        'Gradient boosted trees':HistGradientBoostingRegressor(max_leaf_nodes=15,max_iter=180,l2_regularization=10,early_stopping=False,random_state=42),
    }
    def predict(name,model,mask):
        if name=='Recent 4-week mean':return np.expm1(X[mask,1])
        if name=='Seasonal 52-week baseline':return np.where(np.isfinite(X[mask,3]),np.expm1(X[mask,3]),np.expm1(X[mask,1]))
        return np.maximum(0,np.expm1(model.predict(X[mask])))
    rows=[]
    fitted={}
    validation={}
    for name,model in candidates.items():
        if model is not None:model.fit(X[tr],np.log1p(Y[tr]));fitted[name]=model
        vmask=va&(L==mi);tmask=te&(L==mi)
        vp=predict(name,model,vmask);tp=predict(name,model,tmask)
        validation[name]=metrics(Y[vmask],vp)['wape']
        rows.append({'name':name,'validation':metrics(Y[vmask],vp),'test':metrics(Y[tmask],tp)})
    selected=min(validation,key=validation.get)
    model=fitted.get(selected)
    tmask=te&(L==mi);vmask=va&(L==mi)
    tp=predict(selected,model,tmask);vp=predict(selected,model,vmask)
    residuals=Y[tmask]-tp
    past_errors=list(Y[vmask]-vp)
    holdout=[];covered=[]
    for d,y,p in zip(np.array(D)[tmask],Y[tmask],tp):
        qlo,qhi=np.quantile(past_errors[-26:],[.1,.9])
        lower,upper=max(0,float(p+qlo)),max(0,float(p+qhi))
        covered.append(lower<=y<=upper)
        holdout.append({'week':d.isoformat(),'actual':float(y),'predicted':float(p),'lower':lower,'upper':upper})
        past_errors.append(float(y-p))
    coverage=float(np.mean(covered))
    # Refit only after the untouched test benchmark has been captured.
    if model is not None:model.fit(X,np.log1p(Y))
    hist=a[mi].copy()
    finite=np.flatnonzero(np.isfinite(hist))
    start=finite[-1]+1
    hist=hist[:start].tolist()
    forecast=[]
    final_week=date(2027,10,25)
    final_index=(final_week-first).days//7
    for t in range(start,final_index+1):
        f=np.array(feature(hist,t,mi),dtype=float)
        if selected=='Recent 4-week mean':p=np.expm1(f[1])
        elif selected=='Seasonal 52-week baseline':p=np.expm1(f[3]) if np.isfinite(f[3]) else np.expm1(f[1])
        else:p=max(0,float(np.expm1(model.predict([f])[0])))
        hist.append(float(p));forecast.append({'week':(first+timedelta(days=7*t)).isoformat(),'value':float(p)})
    print(label,selected,'MR7 test WAPE',round(metrics(Y[tmask],tp)['wape']*100,2),flush=True)
    return {'target':label,'selected':selected,'models':rows,'train_rows':int(tr.sum()),'validation_rows':int(va.sum()),
        'test_rows':int(te.sum()),'mr7_test_rows':int(tmask.sum()),'validation_start':'2025-07-01','validation_end':'2025-09-30',
        'test_start':'2025-10-01','test_end':max(np.array(D)[tmask]).isoformat(),
        'holdout':holdout,'forecast':forecast,'residuals':residuals.tolist(),'weekly_interval_coverage':coverage,
        'weekly_interval_nominal':.8,'pooled_labs':len(labs)},hist

forecast_counts,_=fit_forecast(counts,'Calibration count')
forecast_work,_=fit_forecast(work,'Standard workload hours')
forecast_attendance,_=fit_forecast(attendance,'Attendance hours')

months=[f'{2026+(9+i)//12:04d}-{(9+i)%12+1:02d}' for i in range(13)]
def month_values(forecast,errors=None):
    result={m:0. for m in months}
    for i,row in enumerate(forecast):
        w=day(row['week']);value=max(0,row['value']+(errors[i] if errors is not None else 0))
        for k in range(7):
            key=(w+timedelta(days=k)).isoformat()[:7]
            if key in result:result[key]+=value/7
    return result

def boot_months(f):
    rs=np.array(f['residuals']);samples=[]
    n=len(f['forecast'])
    for _ in range(300):
        errors=[]
        while len(errors)<n:
            begin=rng.integers(max(1,len(rs)-3));errors.extend(rs[begin:begin+4])
        samples.append(list(month_values(f['forecast'],errors[:n]).values()))
    return np.quantile(np.array(samples),[.1,.9],axis=0)

cm,wm,am=month_values(forecast_counts['forecast']),month_values(forecast_work['forecast']),month_values(forecast_attendance['forecast'])
wband=boot_months(forecast_work);aband=boot_months(forecast_attendance)
month_forecasts=[{'month':m,'count':cm[m],'workload':wm[m],'workload_low':float(wband[0,i]),'workload_high':float(wband[1,i]),
    'attendance':am[m],'attendance_low':float(aband[0,i]),'attendance_high':float(aband[1,i])} for i,m in enumerate(months)]

print('Building recurrence records',flush=True)
instruments=load('instruments');events=load('calibration_events')
eventmap=defaultdict(list)
for r in events:
    eventmap[r['instrument']].append(day(r['day']))
for key in eventmap:eventmap[key]=sorted(set(eventmap[key]))
groups=Counter(r['equipment_group'] or 'Unknown' for r in events)
common=[g for g,_ in groups.most_common(20)]
group_code={g:i+1 for i,g in enumerate(common)}
instrument_group={r['instrument']:r['equipment_group'] or 'Unknown' for r in instruments}
missing=[r for r in instruments if not r['due_date']]
selected_ids=sorted(eventmap)
if len(selected_ids)>24000:selected_ids=[selected_ids[i] for i in rng.choice(len(selected_ids),24000,replace=False)]
HX,HY,HD,HG=[],[],[],[]
for key in selected_ids:
    dates=eventmap[key]
    g=group_code.get(instrument_group.get(key,'Unknown'),0)
    for j,start in enumerate(dates):
        returned=j+1<len(dates)
        end=dates[j+1] if returned else cal_cutoff
        duration=(end-start).days
        observed_bins=(duration+29)//30 if returned else duration//30
        previous=(start-dates[j-1]).days/365 if j else np.nan
        for b in range(min(observed_bins,34)):
            interval_end=min(start+timedelta(days=30*(b+1)),end) if returned else start+timedelta(days=30*(b+1))
            mid=start+timedelta(days=30*b+15)
            HX.append([b,previous,min(j+1,5),g,np.sin(2*np.pi*mid.month/12),np.cos(2*np.pi*mid.month/12)])
            HY.append(int(returned and b==observed_bins-1));HD.append(interval_end);HG.append(g)
HX,HY,HG=np.array(HX,dtype=np.float32),np.array(HY),np.array(HG)
htr=np.array([d<=date(2025,6,30) for d in HD]);hva=np.array([date(2025,7,1)<=d<=date(2025,12,31) for d in HD]);hte=np.array([date(2026,1,1)<=d<=date(2026,8,31) for d in HD])
hazard=HistGradientBoostingClassifier(max_leaf_nodes=15,max_iter=120,l2_regularization=20,categorical_features=[3],early_stopping=False,random_state=42)
hazard.fit(HX[htr],HY[htr])
hcal=np.array([date(2025,7,1)<=d<=date(2025,9,30) for d in HD])
hselect=np.array([date(2025,10,1)<=d<=date(2025,12,31) for d in HD])
rawcal=hazard.predict_proba(HX[hcal])[:,1]
rawselect=hazard.predict_proba(HX[hselect])[:,1]
rawtest=hazard.predict_proba(HX[hte])[:,1]
def logits(p):return np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6))).reshape(-1,1)
sigmoid=LogisticRegression(C=100,max_iter=1000).fit(logits(rawcal),HY[hcal])
isotonic=IsotonicRegression(out_of_bounds='clip').fit(rawcal,HY[hcal])
cal_scores={'Raw':brier_score_loss(HY[hselect],rawselect),
    'Sigmoid':brier_score_loss(HY[hselect],sigmoid.predict_proba(logits(rawselect))[:,1]),
    'Isotonic':brier_score_loss(HY[hselect],isotonic.predict(rawselect))}
calibration=min(cal_scores,key=cal_scores.get)
def calibrate(p):
    if calibration=='Sigmoid':return sigmoid.predict_proba(logits(p))[:,1]
    if calibration=='Isotonic':return isotonic.predict(p)
    return p
hp=calibrate(rawtest)
base=np.full(hte.sum(),HY[htr].mean())
recurrence={'target':'Calibration during a 30-day risk interval, conditional on no earlier return',
    'train_rows':int(htr.sum()),'validation_rows':int(hva.sum()),'test_rows':int(hte.sum()),'sampled_instruments':len(selected_ids),
    'test_events':int(HY[hte].sum()),'event_rate':float(HY[hte].mean()),
    'roc_auc':float(roc_auc_score(HY[hte],hp)),'average_precision':float(average_precision_score(HY[hte],hp)),
    'brier':float(brier_score_loss(HY[hte],hp)),'constant_brier':float(brier_score_loss(HY[hte],base)),
    'raw_brier':float(brier_score_loss(HY[hte],rawtest)),
    'probability_calibration':calibration,'calibration_selection_brier':cal_scores,
    'features':['Elapsed time since last calibration','Previous observed interval','Number of prior calibrations','Equipment group','Season'],
    'caveats':['Risk rows for the same instrument are correlated; this is a temporal prototype, not independent-subject validation.',
        'Latest equipment group is used as a static proxy; historical reassignment could bias the benchmark.',
        'A 30-day hazard is not an official due date or a calibrated customer booking probability.',
        'No-return tails are right-censored; observations do not imply the instrument is lost.']}
print('Recurrence AUC',round(recurrence['roc_auc'],3),'test positives',recurrence['test_events'],flush=True)
hazard.fit(HX,HY)
# Instrument-level output is contextual, never added to the aggregate forecast.
reference=date(2026,10,1)
eligible=[];unsupported=0;stopped=0
for r in missing:
    if r['due_stopped']:
        stopped+=1;continue
    ds=eventmap.get(r['instrument'],[])
    last=ds[-1] if ds else (day(r['last_calibration']) if r['last_calibration'] else None)
    age=(reference-last).days/30 if last else None
    if age is None or age<0 or age>33:
        unsupported+=1;continue
    eligible.append((age,(ds[-1]-ds[-2]).days/365 if len(ds)>=2 else np.nan,min(max(len(ds),1),5),group_code.get(r['equipment_group'] or 'Unknown',0)))
E=np.array(eligible,dtype=np.float32)
survive=np.ones(len(E));monthly_missing=[]
for i,m in enumerate(months):
    month=int(m[-2:]);xs=np.c_[E[:,0]+i,E[:,1:],np.full(len(E),np.sin(2*np.pi*month/12)),np.full(len(E),np.cos(2*np.pi*month/12))]
    support=xs[:,0]<=33
    hazards=np.zeros(len(E))
    if support.any():hazards[support]=calibrate(hazard.predict_proba(xs[support])[:,1])
    p=survive*hazards
    monthly_missing.append({'month':m,'expected_first_returns':float(p.sum()),'supported_instruments':int(support.sum())})
    survive*=1-hazards

due_months=Counter()
for r in instruments:
    if r['due_date'] and not r['due_stopped']:
        key=r['due_date'][:7]
        if key in months:due_months[key]+=1

capacity_month=defaultdict(lambda:defaultdict(float))
for name in ['actual_capacity','planned_capacity']:
    for r in load(name):
        if r['lab']==LAB:
            month=r['day'][:7];row=capacity_month[(name,month)]
            for k in ['attendance_hours','sick_hours','vacation_hours','other_hours','total_hours']:
                row[k]+=r[k] or 0
capacity_history=[dict(source=s,month=m,**v) for (s,m),v in sorted(capacity_month.items())]
monthly_history=[r for r in load('monthly_calibrations') if r['lab']==LAB and r['month']<'2026-09']
weekly_history=[]
for t,w in enumerate(weeks):
    weekly_history.append({'week':w.isoformat(),'count':float(counts[mi,t]) if np.isfinite(counts[mi,t]) else None,
        'workload':float(work[mi,t]) if np.isfinite(work[mi,t]) else None,
        'attendance':float(attendance[mi,t]) if np.isfinite(attendance[mi,t]) else None})
drivers=load('workload_drivers')
driver_hours=sum(r['standard_hours'] or 0 for r in drivers)
for r in drivers:r['share']=(r['standard_hours'] or 0)/driver_hours if driver_hours else 0
wl=[r for r in load('weekly_workload') if r['lab']==LAB]
data_quality={
    'instruments':len(instruments),'missing_due':len(missing),'missing_due_pct':len(missing)/len(instruments),
    'calibration_events':len(events),'instruments_with_history':len(eventmap),
    'missing_due_with_repeated_history':sum(len(eventmap.get(r['instrument'],[]))>=2 for r in missing),
    'missing_due_supported_now':len(eligible),'missing_due_unsupported_now':unsupported,'missing_due_stopped':stopped,
    'workload_services':sum(r['services'] for r in wl),'workload_matched_services':sum(r['matched_services'] for r in wl),
    'time_match_pct':sum(r['matched_services'] for r in wl)/sum(r['services'] for r in wl),
    'due_dates_after_2040':sum(bool(r['due_date']) and r['due_date'][:4]>'2040' for r in instruments),
    'actual_attendance_null_rows':sum(r['lab']==LAB and r['attendance_hours'] is None for r in load('actual_capacity')),
}
for f in [forecast_counts,forecast_work,forecast_attendance]:
    f.pop('residuals',None)
payload=clean({'lab':LAB,'generated_at':datetime.now(timezone.utc).isoformat(),'source_metadata':meta,
    'history':weekly_history,'monthly_history':monthly_history,'capacity_history':capacity_history,'forecasts':month_forecasts,
    'models':{'count':forecast_counts,'workload':forecast_work,'attendance':forecast_attendance},
    'recurrence':recurrence,'missing_due_forecast':monthly_missing,'recorded_due_counts':dict(due_months),
    'drivers':drivers,'quality':data_quality,
    'assumptions':{'default_productive_share':.8,'productive_share_measured':False,'forecast_month_allocation':'Weekly forecasts prorated over seven calendar days',
        'long_horizon_uncertainty':'Four-week residual block bootstrap; historical variability, not a calibrated annual guarantee',
        'driver_allocation':'Historical service-workload shares Sep 2025–Aug 2026; assumes the mix persists',
        'recurrence_aggregation':'Missing-date first-return signals are contextual and are not added to the aggregate forecast',
        'capacity_meaning':'Standard-work-hour equivalent; attendance is converted by a manager-controlled assumption'}})
(ROOT/'planner_data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False))
print('Saved planner_data.json',json.dumps(data_quality),flush=True)
