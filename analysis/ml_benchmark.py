"""Reproducible ML feasibility benchmark on read-only SQL aggregates.

Run: uv run python analysis/ml_benchmark.py
Labels are observed calibration activity, not confirmed churn or revenue.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (adjusted_rand_score, average_precision_score,
                             brier_score_loss, roc_auc_score, silhouette_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent
customers, labs = defaultdict(dict), defaultdict(dict)
section = ''
for line in (ROOT / 'ml_feasibility.txt').read_text().splitlines():
    if line in ('CUSTOMER_MONTH', 'LAB_WEEK', 'INTERVAL_DISTRIBUTION', 'DUPLICATE_CALIBRATION_INSTRUMENT_DAYS'):
        section = line
        continue
    p = line.split('|')
    if section == 'CUSTOMER_MONTH' and len(p) == 6 and len(p[0]) == 64:
        year, month = map(int, p[1].split('-'))
        customers[p[0]][(year-2024)*12+month-1] = list(map(int, p[2:]))
    elif section == 'LAB_WEEK' and len(p) == 3 and p[0].startswith('MR'):
        labs[p[0]][date.fromisoformat(p[1])] = int(p[2])

NAMES = ['log_volume_last3', 'log_volume_previous3', 'log_volume_current_month',
         'recency_months', 'active_months_last6', 'log_mean_monthly_volume',
         'log_observed_tenure', 'log_recent_group_breadth', 'month_sin', 'month_cos',
         'historical_active_month_fraction', 'median_active_month_gap',
         'active_month_gap_std', 'recency_relative_to_cadence', 'log_volume_momentum']

def features(v, t):
    counts = np.array([v.get(i,[0,0,0,0])[0] for i in range(t+1)],dtype=float)
    active = np.flatnonzero(counts)
    recency, tenure = t-active[-1], t-active[0]+1
    recent, previous = counts[t-2:t+1].sum(), counts[t-5:t-2].sum()
    gaps = np.diff(active)
    cadence = float(np.median(gaps))
    return [np.log1p(recent),np.log1p(previous),np.log1p(counts[t]),recency,
            np.count_nonzero(counts[t-5:t+1]),np.log1p(counts.sum()/tenure),
            np.log1p(tenure),np.log1p(max(v.get(i,[0,0,0,0])[2] for i in range(t-5,t+1))),
            np.sin(2*np.pi*t/12),np.cos(2*np.pi*t/12),len(active)/tenure,
            cadence,float(gaps.std()),recency/cadence,np.log1p(recent)-np.log1p(previous)]

X,Y,T = [],[],[]
for v in customers.values():
    for t in range(6,29):
        seen = [i for i in v if i<=t]
        if len(seen)<2 or min(seen)>t-5 or not any(t-11<=i<=t for i in seen):
            continue
        X.append(features(v,t))
        Y.append(int(any(i in v for i in range(t+1,t+4))))
        T.append(t)
X,Y,T = np.array(X),np.array(Y),np.array(T)

def classification_metrics(y,p):
    n = max(1,int(.1*len(y)))
    top = np.argsort(-p)[:n]
    return {'roc_auc':float(roc_auc_score(y,p)),
            'average_precision':float(average_precision_score(y,p)),
            'brier':float(brier_score_loss(y,p)),
            'top_decile_return_rate':float(y[top].mean()),
            'top_decile_lift':float(y[top].mean()/y.mean())}

customer_results = []
for label,tr,va,te in [
    ('Apr-Jun 2025',T<=11,T==12,(T>=15)&(T<=17)),
    ('Jan-May 2026',T<=17,(T>=20)&(T<=21),T>=24),
]:
    candidates = {
        'logistic':make_pipeline(StandardScaler(),LogisticRegression(C=.5,max_iter=1000)),
        'boosted_15leaves':HistGradientBoostingClassifier(max_leaf_nodes=15,max_iter=200,l2_regularization=10,early_stopping=False,random_state=42),
        'boosted_31leaves':HistGradientBoostingClassifier(max_leaf_nodes=31,max_iter=200,l2_regularization=10,early_stopping=False,random_state=42),
    }
    validation, outcomes = {},{}
    for name,model in candidates.items():
        model.fit(X[tr],Y[tr])
        validation[name] = float(roc_auc_score(Y[va],model.predict_proba(X[va])[:,1]))
        outcomes[name] = classification_metrics(Y[te],model.predict_proba(X[te])[:,1])
    selected = max(validation,key=validation.get)
    important = permutation_importance(candidates[selected],X[va],Y[va],scoring='roc_auc',n_repeats=3,random_state=42)
    ranking = np.argsort(-important.importances_mean)[:6]
    customer_results.append({'test_period':label,'train_rows':int(tr.sum()),'validation_rows':int(va.sum()),'test_rows':int(te.sum()),
        'return_prevalence':float(Y[te].mean()),'recency_baseline_auc':float(roc_auc_score(Y[te],-X[te,3])),
        'constant_rate_brier':float(brier_score_loss(Y[te],np.full(te.sum(),Y[tr].mean()))),
        'validation_auc':validation,'selected_using_validation':selected,'test_models':outcomes,
        'top_validation_features':[{'feature':NAMES[j],'auc_drop_when_shuffled':float(important.importances_mean[j])} for j in ranking]})

# Unsupervised behavior segmentation at a single historical snapshot.
CX = []
for v in customers.values():
    seen = [i for i in v if i<=23]
    if not seen:
        continue
    counts = np.array([v.get(i,[0,0,0,0])[0] for i in range(24)],dtype=float)
    positive = counts[counts>0]
    CX.append([np.log1p(counts.sum()),len(seen)/24,23-max(seen),np.log1p(positive.mean()),
               counts.std()/(counts.mean()+1),np.log1p(max(v[i][2] for i in seen))])
CZ = StandardScaler().fit_transform(CX)
segments = []
for k in (3,4,5,6):
    a = KMeans(n_clusters=k,n_init=10,random_state=42).fit(CZ)
    b = KMeans(n_clusters=k,n_init=10,random_state=7).fit(CZ)
    segments.append({'k':k,'customers':len(CZ),'cluster_sizes':np.bincount(a.labels_).tolist(),
        'sampled_silhouette':float(silhouette_score(CZ,a.labels_,sample_size=min(1500,len(CZ)),random_state=42)),
        'seed_stability_ari':float(adjusted_rand_score(a.labels_,b.labels_))})

# Lab demand forecasting; four-week outcomes, not capacity-utilization targets.
first,last = date(2024,1,1),date(2026,9,14)
weeks = [first+timedelta(days=7*i) for i in range((last-first).days//7+1)]
lab_names = sorted(labs)
FX,FY,FB,FD = [],[],[],[]
for li,lab in enumerate(lab_names):
    counts = np.array([labs[lab].get(w,0) for w in weeks],dtype=float)
    for t in range(12,len(counts)-4):
        FX.append([np.log1p(counts[t]),np.log1p(counts[t-3:t+1].mean()),np.log1p(counts[t-12:t+1].mean()),
            np.sin(2*np.pi*t/52),np.cos(2*np.pi*t/52)]+[int(li==j) for j in range(len(lab_names)-1)])
        FY.append(counts[t+1:t+5].mean())
        FB.append(counts[t-3:t+1].mean())
        FD.append(weeks[t])
FX,FY,FB = np.array(FX),np.array(FY),np.array(FB)
tr = np.array([d<=date(2025,6,30) for d in FD])
va = np.array([date(2025,9,1)<=d<=date(2025,10,27) for d in FD])
te = np.array([date(2026,1,5)<=d<=date(2026,8,17) for d in FD])
def wape(y,p):
    return float(np.abs(y-p).sum()/y.sum())
lab_validation,lab_test = {},{}
for name,regressor in {
    'ridge':make_pipeline(StandardScaler(),Ridge(alpha=5)),
    'boosted':HistGradientBoostingRegressor(max_leaf_nodes=15,max_iter=200,l2_regularization=10,early_stopping=False,random_state=42),
}.items():
    model = TransformedTargetRegressor(regressor=regressor,func=np.log1p,inverse_func=np.expm1).fit(FX[tr],FY[tr])
    lab_validation[name] = wape(FY[va],np.maximum(0,model.predict(FX[va])))
    lab_test[name] = wape(FY[te],np.maximum(0,model.predict(FX[te])))

report = {'customer_return_classification':customer_results,'customer_segmentation':segments,
    'lab_four_week_demand':{'labs':len(lab_names),'train_rows':int(tr.sum()),'validation_rows':int(va.sum()),'test_rows':int(te.sum()),
        'baseline_test_wape':wape(FY[te],FB[te]),'validation_wape':lab_validation,
        'selected_using_validation':min(lab_validation,key=lab_validation.get),'test_wape':lab_test},
    'limitations':['Aggregate calibration activity is not confirmed churn, sales revenue or productive capacity.',
        'Customer classification is restricted to established recurring customers; cold starts require a separate strategy.',
        'Temporal rows from the same customer and overlapping outcome windows are correlated.',
        'Completed history ends Sep 2026; latest customer outcome uses Aug 2026 to avoid incomplete September.',
        'Segmentation stability across random seeds does not establish business usefulness or stability over time.',
        'No current instrument snapshot or future due dates are used in historical classification features.',
        'These are feasibility benchmarks, not final model selection or 3/6/12-month forecast validation.']}
(ROOT/'ml_benchmark_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
