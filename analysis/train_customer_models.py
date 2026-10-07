"""Actual chronological activity/volume benchmarks and live behavior clustering.
Run after export_customer_data.py. Only complete months through August 2026.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,silhouette_score,adjusted_rand_score
from sklearn.inspection import permutation_importance

ROOT=Path(__file__).parent; OUT=ROOT/'customers'; OUT.mkdir(exist_ok=True)
customers=defaultdict(dict)
for row in json.loads((OUT/'monthly_history.json').read_text()):
 y,m=map(int,row['month'].split('-'));t=(y-2024)*12+m-1
 if t<=31:customers[row['customer']][t]=[row['calibrations'],row['instruments'],row['equipment_groups'],row['labs']]
names=['Recent 3-month volume','Previous 3-month volume','Latest-month volume','Months since activity','Active months in last 6','Mean monthly volume','Observed tenure','Maximum monthly group breadth in last 6','Seasonal sine','Seasonal cosine','Historical active-month fraction','Median gap between active months','Gap variability','Recency / observed cadence','Volume momentum']
def feature(v,t):
 a=np.array([v.get(i,[0]*4)[0] for i in range(t+1)],float);active=np.flatnonzero(a);rec=t-active[-1];ten=t-active[0]+1;gaps=np.diff(active);cad=float(np.median(gaps));r=a[max(0,t-2):t+1].sum();p=a[max(0,t-5):t-2].sum()
 return [np.log1p(r),np.log1p(p),np.log1p(a[t]),rec,np.count_nonzero(a[t-5:t+1]),np.log1p(a.sum()/ten),np.log1p(ten),np.log1p(max(v.get(i,[0]*4)[2] for i in range(t-5,t+1))),np.sin(2*np.pi*t/12),np.cos(2*np.pi*t/12),len(active)/ten,cad,float(gaps.std()),rec/cad,np.log1p(r)-np.log1p(p)]
def eligible(v,t):
 seen=[i for i in v if i<=t]
 return len(seen)>=2 and min(seen)<=t-5 and any(t-11<=i<=t for i in seen)
X,Y,V,T,B=[],[],[],[],[]
for v in customers.values():
 for t in range(6,29):
  if not eligible(v,t):continue
  X.append(feature(v,t));vol=sum(v.get(i,[0]*4)[0] for i in range(t+1,t+4));Y.append(int(vol>0));V.append(vol);T.append(t)
  B.append([sum(v.get(i,[0]*4)[0] for i in range(t-2,t+1)),sum(v.get(i,[0]*4)[0] for i in range(max(0,t-11),t+1))/4,sum(v.get(i,[0]*4)[0] for i in range(t-11,t-8)) if t>=11 else sum(v.get(i,[0]*4)[0] for i in range(t-2,t+1))])
X,Y,V,T,B=map(np.array,(X,Y,V,T,B));tr=T<=17;cal=T==20;va=T==21;te=T>=24
def cm(y,p):return {'auc':float(roc_auc_score(y,p)),'ap':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p))}
models={'Logistic regression':make_pipeline(StandardScaler(),LogisticRegression(C=.5,max_iter=1200)),'Boosted trees':HistGradientBoostingClassifier(max_leaf_nodes=15,max_iter=180,l2_regularization=10,early_stopping=False,random_state=42)}
classified={};calibrators={};validation={};test={}
for name,m in models.items():
 m.fit(X[tr],Y[tr]);pc=m.predict_proba(X[cal])[:,1];iso=IsotonicRegression(out_of_bounds='clip').fit(pc,Y[cal]);calibrators[name]=iso
 for method in ['raw','isotonic']:
  pv=m.predict_proba(X[va])[:,1];pt=m.predict_proba(X[te])[:,1]
  if method=='isotonic':pv=iso.predict(pv);pt=iso.predict(pt)
  key=name+' / '+method;validation[key]=cm(Y[va],pv);test[key]=cm(Y[te],pt);classified[key]=(m,iso if method=='isotonic' else None)
selected=min(validation,key=lambda k:validation[k]['brier']);classifier,calibrator=classified[selected]
print('Activity model:',selected,test[selected],flush=True)
pt=classifier.predict_proba(X[te])[:,1];pt=calibrator.predict(pt) if calibrator else pt
reliability=[]
for lo in np.arange(0,1,.1):
 mask=(pt>=lo)&(pt<(lo+.1 if lo<.89 else 1.00001))
 if mask.sum():reliability.append({'predicted':float(pt[mask].mean()),'observed':float(Y[te][mask].mean()),'n':int(mask.sum())})
important=permutation_importance(classifier,X[va],Y[va],scoring='roc_auc',n_repeats=3,random_state=42)
importance=[{'name':names[j],'auc_drop':float(important.importances_mean[j])} for j in np.argsort(-important.importances_mean)[:8]]
baseline={'auc':float(roc_auc_score(Y[te],-X[te,3])),'brier':float(brier_score_loss(Y[te],np.full(te.sum(),Y[tr].mean())))}
def vm(y,p):return {'wape':float(np.abs(y-p).sum()/y.sum()),'mae':float(np.abs(y-p).mean()),'bias':float((p-y).sum()/y.sum())}
volume_models={'Boosted count regression':HistGradientBoostingRegressor(loss='poisson',max_leaf_nodes=15,max_iter=200,l2_regularization=20,early_stopping=False,random_state=42),'Boosted squared-error regression':HistGradientBoostingRegressor(max_leaf_nodes=15,max_iter=200,l2_regularization=20,early_stopping=False,random_state=42)}
vv={};vt={}
for j,name in enumerate(['Previous 3 months','Previous 12 months / 4','Same 3 months last year']):vv[name]=vm(V[va],B[va,j]);vt[name]=vm(V[te],B[te,j])
for name,m in volume_models.items():
 m.fit(X[tr],V[tr]);vv[name]=vm(V[va],np.maximum(0,m.predict(X[va])));vt[name]=vm(V[te],np.maximum(0,m.predict(X[te])))
volselected=min(vv,key=lambda k:vv[k]['wape']);print('Volume model:',volselected,vt[volselected],flush=True)
ids=sorted(customers);counts=np.array([[customers[c].get(i,[0]*4)[0] for i in range(32)] for c in ids]);CX=[]
for c,a in zip(ids,counts):
 b=a[-24:];pos=b[b>0];active=np.flatnonzero(a)
 CX.append([np.log1p(b.sum()),np.count_nonzero(b)/24,31-active[-1],np.log1p(pos.mean() if len(pos) else 0),float(b.std()/(b.mean()+1)),np.log1p(max(customers[c][i][2] for i in customers[c]))])
Z=StandardScaler().fit_transform(CX);candidate_segments=[];clusters={}
for k in [3,4,5,6]:
 km=KMeans(n_clusters=k,n_init=10,random_state=42).fit(Z);km2=KMeans(n_clusters=k,n_init=10,random_state=7).fit(Z)
 candidate_segments.append({'k':k,'silhouette':float(silhouette_score(Z,km.labels_,sample_size=min(1600,len(Z)),random_state=42)),'seed_ari':float(adjusted_rand_score(km.labels_,km2.labels_))});clusters[k]=km
k=max(candidate_segments,key=lambda r:r['silhouette'])['k'];labels=clusters[k].labels_;print('Segments:',candidate_segments,flush=True)
industry={r['customer']:r['industry'] for r in json.loads((OUT/'industry.json').read_text())};groups=defaultdict(list)
for r in json.loads((OUT/'groups.json').read_text()):groups[r['customer']].append({'group':r['equipment_group'],'count':r['calibrations']})
segments=[]
for j in range(k):
 mask=labels==j;a=counts[mask];rec=np.array(CX)[mask,2];meanv=a[:,-24:].sum(axis=1).mean();active=(a[:,-24:]>0).sum(axis=1).mean()
 name='Frequent, high-volume' if active>=10 else ('Long inactive' if rec.mean()>=12 else 'Occasional, low-volume' if meanv<20 else 'Intermittent batches')
 if any(s['name']==name for s in segments):name+=' '+str(j+1)
 segments.append({'id':j,'name':name,'customers':int(mask.sum()),'mean_24m_volume':float(meanv),'mean_active_months':float(active),'mean_recency':float(rec.mean()),'mean_monthly':a.mean(axis=0).tolist()})
live=[];eligibleids=[c for c in ids if eligible(customers[c],31)];LX=np.array([feature(customers[c],31) for c in eligibleids]);prob=classifier.predict_proba(LX)[:,1];prob=calibrator.predict(prob) if calibrator else prob
if volselected in volume_models:vp=np.maximum(0,volume_models[volselected].predict(LX))
else:
 j=['Previous 3 months','Previous 12 months / 4','Same 3 months last year'].index(volselected)
 vp=np.array([sum(customers[c].get(i,[0]*4)[0] for i in (range(29,32) if j==0 else range(20,32) if j==1 else range(20,23)))/(4 if j==1 else 1) for c in eligibleids])
prediction={c:(float(p),float(v)) for c,p,v in zip(eligibleids,prob,vp)}
explanations={}
if hasattr(classifier,'named_steps'):
 contributions=classifier.named_steps['standardscaler'].transform(LX)*classifier.named_steps['logisticregression'].coef_[0]
 for c,row in zip(eligibleids,contributions):
  explanations[c]=[{'feature':names[j],'log_odds_contribution':float(row[j])} for j in np.argsort(-np.abs(row))[:4]]
peer_counts=defaultdict(lambda:defaultdict(int));peer_n=defaultdict(int)
for c in ids:
 if groups[c]:
  ind=industry.get(c,'Unknown');peer_n[ind]+=1
  for g in groups[c]:peer_counts[ind][g['equipment_group'] if 'equipment_group' in g else g['group']]+=1
for n,c in enumerate(ids):
 a=counts[n];v=customers[c];active=np.flatnonzero(a);rec=int(31-active[-1]);recent=int(a[-3:].sum());previous=int(a[-6:-3].sum());cad=float(np.median(np.diff(active))) if len(active)>1 else None
 expected=float(a[-15:-3].sum()/4);deficit=max(0,(expected-recent)/expected) if expected else 0;late=max(0,min(1,(rec/(cad or 1)-1)/2)) if cad else 0
 deviation=max(deficit,late);priority=float(deviation*np.log1p(expected));flags=[]
 if expected>=5 and deficit>=.5:flags.append('Recent volume ≥50% below previous-year quarterly average')
 if cad and rec>1.5*cad and rec>=2:flags.append('Inactivity exceeds 1.5× observed median cadence')
 pred=prediction.get(c);seg=int(labels[n]);top=sorted(groups[c],key=lambda r:-r['count'])[:6]
 ind=industry.get(c,'Unknown');own={g['group'] for g in groups[c]};opportunities=[]
 if peer_n[ind]>=20 and ind not in ['Unknown','Sonstiges'] and own:
  for group,n in sorted(peer_counts[ind].items(),key=lambda x:-x[1]):
   if group not in own and n/peer_n[ind]>=.25:opportunities.append({'group':group,'peer_fraction':n/peer_n[ind],'peers':peer_n[ind]})
 live.append({'id':'C-'+c[:10],'segment':seg,'industry':ind,'months':a.tolist(),'recency':rec,'cadence':cad,'recent3':recent,'previous3':previous,'normal3':expected,'volume24':int(a[-24:].sum()),'active24':int((a[-24:]>0).sum()),'probability':pred[0] if pred else None,'forecast3':pred[1] if pred else None,'deviation':deviation,'priority':priority,'flags':flags,'groups':top,'group_count':len(groups[c]),'review':bool(flags),'explanations':explanations.get(c,[]),'opportunities':opportunities[:2],'status':'Model-supported' if pred else 'Insufficient recurring history / inactive >12 months'})
live.sort(key=lambda r:-r['priority']);industries=[]
for name in sorted(set(r['industry'] for r in live)):
 rr=[r for r in live if r['industry']==name];industries.append({'name':name,'customers':len(rr),'volume12':sum(sum(r['months'][-12:]) for r in rr),'flagged':sum(r['review'] for r in rr),'predicted3':sum(r['forecast3'] or 0 for r in rr),'supported':sum(r['probability'] is not None for r in rr),'groups':len(set(g['group'] for r in rr for g in r['groups']))})
industries.sort(key=lambda r:-r['volume12']);cohorts=[]
for t in range(24,29):
 m=T[te]==t;cohorts.append({'month':f'2026-{t-23:02d}','customers':int(m.sum()),'auc':float(roc_auc_score(Y[te][m],pt[m])),'observed':float(Y[te][m].mean()),'predicted':float(pt[m].mean())})
data={'asof':'2026-08-31','target_window':'September–November 2026','customers':live,'segments':segments,'segmentation_candidates':candidate_segments,'selected_k':k,'industries':industries,'monthly_total':counts.sum(axis=0).tolist(),'monthly_active':(counts>0).sum(axis=0).tolist(),'model':{'selected':selected,'validation':validation,'test':test,'baseline':baseline,'reliability':reliability,'importance':importance,'cohorts':cohorts,'test_prevalence':float(Y[te].mean()),'train_rows':int(tr.sum()),'calibration_rows':int(cal.sum()),'validation_rows':int(va.sum()),'test_rows':int(te.sum()),'volume_selected':volselected,'volume_validation':vv,'volume_test':vt},'quality':{'historical_customers':len(ids),'model_supported':len(eligibleids),'flagged':sum(r['review'] for r in live),'unknown_industry':sum(r['industry']=='Unknown' for r in live),'conflicting_industry':json.loads((OUT/'industry_duplicates.json').read_text())[0]['customers_with_conflicting_industry'],'full_months':32,'calibrations':int(counts.sum())},'definitions':{'probability':'Probability of at least one observed calibration at this provider in the next three full calendar months. Not churn probability.','volume':'Total calibration records expected next three months, including zero-activity outcomes. Not orders or revenue.','priority':'max(quarterly volume deficit, cadence deviation) × log(1 + historical quarterly calibration volume); review only when a flag exists. A transparent rule, not estimated outreach benefit.','model_lifecycle':'Frozen training through June 2025; optional isotonic map fitted September 2025. Candidate/map selection on October 2025, evaluated January–May 2026. Live August features use the same frozen model. No test-set refit.'}}
(OUT/'dashboard_data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False));print('Saved dashboard data:',data['quality'],flush=True)
