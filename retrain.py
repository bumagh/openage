"""
重新训练 OpenAge 模型并保存兼容当前 sklearn 版本的权重。
自动从 CDC 下载 NHANES 2017-2020 数据。
"""
import os
import urllib.request
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn import ensemble
from sklearn.model_selection import train_test_split
from joblib import dump

from openage.models.tree import STANDARD_21_FEATURES, EXTENDED_35_FEATURES, FEATURE_NAMES
from openage.evaluation.metrics import compute_age_metrics, print_metrics

# ── 1. 下载 NHANES 2017-2020 数据 ──────────────────────────────────────────
DATA_DIR = Path("nhanes_data/2017-2020")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018"
FILES = {
    "P_BIOPRO.XPT": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BIOPRO.xpt",
    "P_CBC.XPT":    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_CBC.xpt",
    "P_MCQ.XPT":    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.xpt",
    "P_TRIGLY.XPT": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_TRIGLY.xpt",
    "P_HDL.XPT":    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_HDL.xpt",
    "P_GHB.XPT":    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_GHB.xpt",
    "P_DEMO.XPT":   "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.xpt",
}

print("=== 下载 NHANES 数据 ===")
for fname, url in FILES.items():
    dest = DATA_DIR / fname
    if dest.exists():
        print(f"  已存在: {fname}")
        continue
    print(f"  下载: {fname} ...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"完成 ({dest.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"失败: {e}")

# ── 2. 加载并合并数据 ───────────────────────────────────────────────────────
print("\n=== 加载数据 ===")
df = None
for fname in FILES:
    path = DATA_DIR / fname
    if not path.exists():
        print(f"  跳过缺失文件: {fname}")
        continue
    try:
        tmp = pd.read_sas(str(path), format="xport")
        print(f"  {fname}: {len(tmp)} 行, {len(tmp.columns)} 列")
        if df is None:
            df = tmp
        else:
            df = df.merge(tmp, on="SEQN", how="outer")
    except Exception as e:
        print(f"  加载失败 {fname}: {e}")

print(f"\n合并后: {len(df)} 行, {len(df.columns)} 列")
df = df.fillna(df.mean(numeric_only=True))
print(f"年龄范围: {df['RIDAGEYR'].min():.0f} - {df['RIDAGEYR'].max():.0f} 岁")
print(f"平均年龄: {df['RIDAGEYR'].mean():.1f} 岁")

# ── 3. 训练 21 特征标准模型 ─────────────────────────────────────────────────
print("\n=== 训练 21 特征标准模型 ===")
avail = [f for f in STANDARD_21_FEATURES if f in df.columns]
missing = [f for f in STANDARD_21_FEATURES if f not in df.columns]
if missing:
    print(f"  缺失特征（用0填充）: {missing}")
    for f in missing:
        df[f] = 0.0

X = df[STANDARD_21_FEATURES].values
y = df["RIDAGEYR"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=3454)
print(f"训练集: {len(X_train):,}  测试集: {len(X_test):,}")

model_std = ensemble.GradientBoostingRegressor(
    n_estimators=4000, max_depth=8, min_samples_split=30,
    learning_rate=0.01, loss="squared_error",
)
print("训练中（约需几分钟）...")
model_std.fit(X_train, y_train)
metrics = compute_age_metrics(y_test, model_std.predict(X_test))
print_metrics(metrics, "21特征标准模型 — 测试集")

# ── 4. 训练 35 特征扩展模型 ─────────────────────────────────────────────────
print("\n=== 训练 35 特征扩展模型 ===")
for f in EXTENDED_35_FEATURES:
    if f not in df.columns:
        df[f] = 0.0

X_ext = df[EXTENDED_35_FEATURES].values
X_train_e, X_test_e, y_train_e, y_test_e = train_test_split(X_ext, y, test_size=0.3, random_state=3454)

model_ext = ensemble.GradientBoostingRegressor(
    n_estimators=6000, max_depth=10, min_samples_split=30,
    learning_rate=0.01, loss="squared_error",
)
print("训练中（约需几分钟）...")
model_ext.fit(X_train_e, y_train_e)
metrics_e = compute_age_metrics(y_test_e, model_ext.predict(X_test_e))
print_metrics(metrics_e, "35特征扩展模型 — 测试集")

# ── 5. 保存权重 ─────────────────────────────────────────────────────────────
WEIGHTS_DIR = Path("openage/models/weights")
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

dump(model_std, WEIGHTS_DIR / "standard_21feat.joblib")
print(f"\n已保存: {WEIGHTS_DIR}/standard_21feat.joblib")

dump(model_ext, WEIGHTS_DIR / "extended_35feat.joblib")
print(f"已保存: {WEIGHTS_DIR}/extended_35feat.joblib")

print("\n=== 完成，可以运行 test_age.py 了 ===")
