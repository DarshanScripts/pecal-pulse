"""Long-horizon demand backtests from previously verified SQL exports.

No current database connection is required. These targets are calibration
counts, not productive workload or capacity utilization.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json
from pathlib import Path
from datetime import date,timedelta
from collections import defaultdict
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).parent
monthly = np.zeros(32,dtype=float)
labs = defaultdict(dict)
section = ''
for line in (root/'ml_feasibility.txt').read_text().splitlines():
    if line in ('CUSTOMER_MONTH','LAB_WEEK','INTERVAL_DISTRIBUTION','DUPLICATE_CALIBRATION_INSTRUMENT_DAYS'):
        section = line
        continue
    p = line.split('|')
    if section=='CUSTOMER_MONTH' and len(p)==6 and len(p[0])==64:
        y,m = map(int,p[1].split('-'))
        i = (y-2024)*12+m-1
        if 0<=i<32:
            monthly[i] += int(p[2])
    elif section=='LAB_WEEK' and len(p)==3 and p[0].startswith('MR'):
        labs[p[0]][date.fromisoformat(p[1])] = int(p[2])

def wape(y,p):
    y,p = np.array(y),np.array(p)
    return float(np.abs(y-p).sum()/y.sum())

monthly_results = []
for horizon in (3,6,12,13):
    ys,flat,seasonal,trend = [],[],[],[]
    monthly_actuals,monthly_seasonal = [],[]
    for origin in range(11,len(monthly)-horizon):
        actual = monthly[origin+1:origin+horizon+1]
        predicted = []
        for k in range(1,horizon+1):
            idx = origin+k-12
            while idx>origin:
                idx -= 12
            predicted.append(monthly[idx])
        predicted = np.array(predicted)
        ratio = monthly[origin-2:origin+1].sum()/monthly[origin-14:origin-11].sum() if origin>=14 else 1.
        factor = np.clip(.5+.5*ratio,.5,1.5)
        ys.append(actual.sum())
        flat.append(monthly[origin-5:origin+1].mean()*horizon)
        seasonal.append(predicted.sum())
        trend.append(predicted.sum()*factor)
        monthly_actuals.extend(actual.tolist())
        monthly_seasonal.extend(predicted.tolist())
    monthly_results.append({'horizon_calendar_months':horizon,'overlapping_origins':len(ys),
        'maximum_disjoint_target_windows_after_one_year_context':(len(monthly)-12)//horizon,
        'total_horizon_wape_last6_mean':wape(ys,flat),
        'total_horizon_wape_last_year_seasonality':wape(ys,seasonal),
        'total_horizon_wape_shrunk_recent_trend':wape(ys,trend),
        'individual_month_wape_last_year_seasonality':wape(monthly_actuals,monthly_seasonal),
        'max_supervised_training_origins_at_latest_test_with_six_month_features':max(0,len(monthly)-2*horizon-5)})

# Per-lab approximate month horizons, expressed explicitly as weeks.
first,last = date(2024,1,1),date(2026,9,14)
weeks = [first+timedelta(days=7*i) for i in range((last-first).days//7+1)]
names = sorted(labs)
A = np.array([[labs[lab].get(w,0) for w in weeks] for lab in names],dtype=float)

def feature(a,t,li):
    recent = a[t-12:t+1]
    return [np.log1p(a[t]),np.log1p(a[t-3:t+1].mean()),np.log1p(recent.mean()),
        np.sin(2*np.pi*t/52),np.cos(2*np.pi*t/52)]+[int(li==j) for j in range(len(names)-1)]

weekly_results = []
for horizon in (13,26,52,56):
    actuals,flat,seasonal,model_y,model_p,model_seasonal = [],[],[],[],[],[]
    all_origins,ml_origins,train_counts = [],[],[]
    for origin in range(51,len(weeks)-horizon,4):
        all_origins.append(weeks[origin].isoformat())
        for li,a in enumerate(A):
            actuals.append(a[origin+1:origin+horizon+1].sum())
            flat.append(a[origin-12:origin+1].mean()*horizon)
            predicted=[]
            for k in range(1,horizon+1):
                idx=origin+k-52
                while idx>origin:
                    idx-=52
                predicted.append(a[idx])
            seasonal.append(sum(predicted))
        train_origins = list(range(12,origin-horizon+1,4))
        if len(train_origins)<6:
            continue
        tx,ty = [],[]
        for t in train_origins:
            for li,a in enumerate(A):
                tx.append(feature(a,t,li))
                ty.append(np.log1p(a[t+1:t+horizon+1].mean()))
        model = make_pipeline(StandardScaler(),Ridge(alpha=10)).fit(tx,ty)
        px=[feature(a,origin,li) for li,a in enumerate(A)]
        preds=np.maximum(0,np.expm1(model.predict(px)))*horizon
        model_p.extend(preds.tolist())
        model_y.extend(a[origin+1:origin+horizon+1].sum() for a in A)
        model_seasonal.extend(seasonal[-len(names):])
        ml_origins.append(weeks[origin].isoformat())
        train_counts.append(len(tx))
    lab_actual=np.array(actuals).reshape(-1,len(names))
    lab_seasonal=np.array(seasonal).reshape(-1,len(names))
    per_lab=[{'lab':lab,'seasonal_total_horizon_wape':float(np.abs(lab_actual[:,i]-lab_seasonal[:,i]).sum()/lab_actual[:,i].sum()) if lab_actual[:,i].sum()>0 else None} for i,lab in enumerate(names)]
    weekly_results.append({'horizon_weeks':horizon,'labs':len(names),
        'approximate_months':{13:3,26:6,52:12,56:13}[horizon],
        'overlapping_baseline_origins':len(all_origins),
        'baseline_total_horizon_wape_recent13_weeks':wape(actuals,flat),
        'baseline_total_horizon_wape_last_year':wape(actuals,seasonal),
        'seasonal_baseline_per_lab':per_lab,
        'supervised_rolling_origins':len(ml_origins),
        'supervised_train_rows_range':[min(train_counts),max(train_counts)] if train_counts else None,
        'supervised_total_horizon_wape':wape(model_y,model_p) if model_y else None,
        'seasonal_baseline_wape_on_same_supervised_origins':wape(model_y,model_seasonal) if model_y else None,
        'supervised_first_origin':ml_origins[0] if ml_origins else None,
        'supervised_last_origin':ml_origins[-1] if ml_origins else None})

report={'data':{'complete_calendar_months':len(monthly),'first_month':'2024-01','last_month':'2026-08',
        'weekly_lab_series':len(names),'complete_weeks':len(weeks)},
    'exact_calendar_month_aggregate_demand':monthly_results,
    'weekly_lab_demand':weekly_results,
    'caveats':['Calendar-month totals cover customer-attributed calibration records across all labs.',
        'Weekly lab horizons are approximations to calendar-month horizons.',
        'Demand-count forecasts do not validate productive-hour or utilization forecasts.',
        'Cumulative horizon errors conceal within-horizon peaks and lab-level bottlenecks.',
        'Long-horizon origins overlap heavily; only one disjoint annual target window is available after a year of context.',
        'Fixed ridge settings, no tuning on held-out targets; small long-horizon training sets remain inadequate for durable claims.',
        'Fresh SQL refresh failed during prelogin; analysis uses previously exported data.']}
(root/'horizon_feasibility_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
