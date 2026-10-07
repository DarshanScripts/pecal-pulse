"""Exploratory temporal baselines on aggregate data, not production models."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import json
from datetime import date, timedelta
from collections import defaultdict
from pathlib import Path
import numpy as np

root = Path(__file__).parent
customers = defaultdict(dict)
labs = defaultdict(dict)
section = ''
for line in (root / 'ml_feasibility.txt').read_text().splitlines():
    if line in ('CUSTOMER_MONTH', 'LAB_WEEK', 'INTERVAL_DISTRIBUTION', 'DUPLICATE_CALIBRATION_INSTRUMENT_DAYS'):
        section = line
        continue
    parts = line.split('|')
    if section == 'CUSTOMER_MONTH' and len(parts) == 6 and len(parts[0]) == 64:
        year, month = map(int, parts[1].split('-'))
        customers[parts[0]][(year - 2024) * 12 + month - 1] = list(map(int, parts[2:]))
    elif section == 'LAB_WEEK' and len(parts) == 3 and parts[0].startswith('MR'):
        labs[parts[0]][date.fromisoformat(parts[1])] = int(parts[2])

def auc(y, scores):
    order = np.argsort(scores, kind='stable')
    sorted_scores = scores[order]
    ranks = np.empty(len(y))
    _, starts, counts = np.unique(sorted_scores, return_index=True, return_counts=True)
    for start, n in zip(starts, counts):
        ranks[order[start:start+n]] = start + (n + 1) / 2
    positive = int(y.sum())
    return float((ranks[y == 1].sum() - positive * (positive + 1) / 2) / (positive * (len(y) - positive)))

def average_precision(y, scores):
    order = np.argsort(-scores, kind='stable')
    ys, ss = y[order], scores[order]
    ends = np.r_[np.flatnonzero(np.diff(ss)), len(ss)-1]
    tp = np.cumsum(ys)[ends]
    recall = tp / y.sum()
    precision = tp / (ends + 1)
    return float(np.sum(np.diff(np.r_[0, recall]) * precision))

def month_features(v, t):
    counts = np.array([v.get(i, [0, 0, 0, 0])[0] for i in range(t+1)], dtype=float)
    active = np.flatnonzero(counts)
    recency = t - active[-1]
    recent, previous = counts[max(0,t-2):t+1].sum(), counts[max(0,t-5):t-2].sum()
    tenure = t - active[0] + 1
    return [np.log1p(recent), np.log1p(previous), np.log1p(counts[t]),
            recency, np.count_nonzero(counts[max(0,t-5):t+1]),
            np.log1p(counts.sum()/tenure), np.log1p(tenure),
            np.log1p(max(v.get(i,[0,0,0,0])[2] for i in range(max(0,t-5),t+1))),
            np.sin(2*np.pi*t/12), np.cos(2*np.pi*t/12)]

X, Y, cutoffs = [], [], []
for customer, v in customers.items():
    for t in range(6, 29):  # Jul 2024 to May 2026; outcome ends no later than Aug 2026.
        seen = [i for i in v if i <= t]
        if len(seen) < 2 or min(seen) > t-5 or not any(t-11 <= i <= t for i in seen):
            continue
        X.append(month_features(v,t))
        Y.append(int(any(i in v for i in range(t+1,t+4))))
        cutoffs.append(t)
X, Y, cutoffs = np.array(X), np.array(Y), np.array(cutoffs)
train = cutoffs <= 17  # Jun 2025; training outcomes finish Sep 2025.
valid = (cutoffs >= 20) & (cutoffs <= 21)  # Sep-Oct 2025; outcomes finish Jan 2026.
test = cutoffs >= 24  # Jan-May 2026; all outcomes fully observed.
mean, scale = X[train].mean(0), X[train].std(0)
scale[scale == 0] = 1
Z = np.c_[np.ones(len(X)), (X-mean)/scale]
beta = np.zeros(Z.shape[1])
moment, velocity = np.zeros_like(beta), np.zeros_like(beta)
for iteration in range(1,401):
    pred = 1/(1+np.exp(-np.clip(Z[train]@beta,-30,30)))
    penalty = 0.01 * beta
    penalty[0] = 0
    grad = Z[train].T@(pred-Y[train])/train.sum() + penalty
    moment = .9*moment+.1*grad
    velocity = .999*velocity+.001*grad**2
    beta -= .04*(moment/(1-.9**iteration))/(np.sqrt(velocity/(1-.999**iteration))+1e-8)
prob = 1/(1+np.exp(-np.clip(Z[test]@beta,-30,30)))
yt = Y[test]
recency_score = -X[test,3]
top = np.argsort(-prob)[:max(1,int(.1*len(prob)))]
customer_report = dict(train_rows=int(train.sum()), validation_rows=int(valid.sum()), test_rows=int(test.sum()),
    test_return_rate=float(yt.mean()), model_auc=auc(yt,prob), recency_baseline_auc=auc(yt,recency_score),
    model_average_precision=average_precision(yt,prob), recency_average_precision=average_precision(yt,recency_score),
    model_brier=float(np.mean((prob-yt)**2)), constant_train_rate_brier=float(np.mean((Y[train].mean()-yt)**2)),
    top_decile_return_rate=float(yt[top].mean()), top_decile_lift=float(yt[top].mean()/yt.mean()))

# Unsupervised customer behavior segments, using only information through Dec 2025.
CX = []
for v in customers.values():
    seen = [i for i in v if i <= 23]
    if not seen:
        continue
    counts = np.array([v.get(i,[0,0,0,0])[0] for i in range(24)],dtype=float)
    positive = counts[counts>0]
    CX.append([np.log1p(counts.sum()),len(seen)/24,23-max(seen),
               np.log1p(positive.mean()),float(counts.std()/(counts.mean()+1)),
               np.log1p(max(v[i][2] for i in seen))])
CX = np.array(CX)
CM, CS = CX.mean(0), CX.std(0)
CS[CS==0] = 1
CZ = (CX-CM)/CS
rng = np.random.default_rng(42)
centers = CZ[rng.choice(len(CZ),4,replace=False)].copy()
for _ in range(50):
    labels = ((CZ[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
    updated = np.array([CZ[labels==k].mean(0) if np.any(labels==k) else centers[k] for k in range(4)])
    if np.allclose(updated,centers):
        break
    centers = updated
segments = [dict(customers=int((labels==k).sum()),mean_total_calibrations=float(np.expm1(CX[labels==k,0]).mean()),
                 mean_active_months=float((CX[labels==k,1]*24).mean()),mean_months_since_last_activity=float(CX[labels==k,2].mean())) for k in range(4)]

# Weekly lab demand: next-four-week mean, time split; features contain only prior/current weeks.
first, last = date(2024,1,1), date(2026,9,14)
weeks = [first+timedelta(days=7*i) for i in range((last-first).days//7+1)]
lab_names = sorted(labs)
FX,FY,FD,FB = [],[],[],[]
for li, lab in enumerate(lab_names):
    a = np.array([labs[lab].get(w,0) for w in weeks],dtype=float)
    for t in range(12,len(a)-4):
        onehot = [int(li==j) for j in range(len(lab_names)-1)]
        FX.append([np.log1p(a[t]),np.log1p(a[t-3:t+1].mean()),np.log1p(a[t-12:t+1].mean()),
                   np.sin(2*np.pi*t/52),np.cos(2*np.pi*t/52)]+onehot)
        FY.append(a[t+1:t+5].mean())
        FB.append(a[t-3:t+1].mean())
        FD.append(weeks[t])
FX,FY,FB = np.array(FX),np.array(FY),np.array(FB)
ft = np.array([d<=date(2025,11,24) for d in FD])
fe = np.array([date(2026,1,5)<=d<=date(2026,8,17) for d in FD])
fm,fs = FX[ft].mean(0),FX[ft].std(0)
fs[fs==0]=1
FZ = np.c_[np.ones(len(FX)),(FX-fm)/fs]
reg = np.eye(FZ.shape[1])*5
reg[0,0]=0
coef = np.linalg.solve(FZ[ft].T@FZ[ft]+reg,FZ[ft].T@np.log1p(FY[ft]))
fp = np.maximum(0,np.expm1(FZ[fe]@coef))
lab_report = dict(labs=len(lab_names),train_rows=int(ft.sum()),test_rows=int(fe.sum()),
                 last_four_week_baseline_wape=float(np.abs(FB[fe]-FY[fe]).sum()/FY[fe].sum()),
                 pooled_ridge_wape=float(np.abs(fp-FY[fe]).sum()/FY[fe].sum()))
report = dict(customer_month_count=sum(len(v) for v in customers.values()),customers=len(customers),
              customer_prediction=customer_report, exploratory_customer_segments=segments,lab_four_week_prediction=lab_report,
              caveats=['Customer target is any calibration in next three complete months, not confirmed churn.',
                       'Customer sample requires two historical active months and at least six months since first observation.',
                       'Customer classification uses calibration history, not sales revenue or open orders.',
                       'Lab target is calibration count, not productive hours or utilization.',
                       'Repeated customers and overlapping forecast windows create dependent rows.',
                       'Small exploratory models; no hyperparameter search, confidence intervals, or causal interpretation.'])
(root/'ml_probe_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
