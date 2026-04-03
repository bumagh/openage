# -*- coding: utf-8 -*-
"""
根据血常规报告预测生物年龄
报告来源：血常规检查单
"""
from openage import predict_age

# ── 从报告中读取的数据 ──────────────────────────────────────────────────────
# 血常规（直接从报告映射）
blood_panel = {
    # === 血常规（报告中有值）===
    "mean_cell_volume_fl":               67.3,   # 平均红细胞体积 MCV，↓偏低（正常82-100fL）
    "rbc_count_million_per_ul":          4.43,   # 红细胞计数 RBC（10^6/μL）
    "hemoglobin_g_dl":                   13.0,   # 血红蛋白 130g/L ÷ 10
    "hematocrit_percent":                43.2,   # 红细胞比积
    "rdw_percent":                       16.2,   # 红细胞分布宽度 RDW，↑偏高（正常12.2-14.6%）
    "platelet_count_thousand_per_ul":    337,    # 血小板计数（10^3/μL）
    "wbc_count_thousand_per_ul":         6.42,   # 白细胞计数（10^3/μL）
    "lymphocyte_count_thousand_per_ul":  2.28,   # 淋巴细胞绝对值
    "lymphocyte_percent":                27.5,   # 淋巴细胞百分比（图中单核%27.5，淋巴%未标注，用正常值估算）
    "monocyte_percent":                  7.6,    # 单核细胞百分数

    # === 生化指标（报告未提供，使用中国成人正常参考值）===
    # 注意：以下为估算值，实际结果会有偏差
    "glycohemoglobin_percent":           5.5,    # 糖化血红蛋白 HbA1c（正常<6%）
    "glucose_mg_dl":                     90,     # 血糖 5.0mmol/L × 18
    "creatinine_mg_dl":                  0.85,   # 肌酐 75μmol/L ÷ 88.4
    "bun_mg_dl":                         14,     # 尿素氮 5.0mmol/L × 2.8
    "alt_iu_l":                          20,     # 谷丙转氨酶
    "alp_iu_l":                          70,     # 碱性磷酸酶
    "ldh_iu_l":                          150,    # 乳酸脱氢酶
    "cpk_iu_l":                          100,    # 肌酸激酶
    "potassium_mmol_l":                  4.0,    # 血钾

    # === 问卷（假设无既往病史）===
    "ever_cancer_or_malignancy":         2,      # 无癌症史
    "ever_angina":                       2,      # 无心绞痛史
    "ever_arthritis":                    2,      # 无关节炎史
    "ever_liver_condition":              2,      # 无肝病史
}

# 请填入实际年龄
chronological_age = 45  # ← 修改为实际年龄

result = predict_age(blood_panel, chronological_age=chronological_age)

print("=" * 50)
print("  OpenAge 生物年龄预测报告")
print("=" * 50)
print(f"  实际年龄:   {chronological_age} 岁")
print(f"  生物年龄:   {result.biological_age:.1f} 岁")
if result.chronological_age_delta is not None:
    direction = "老" if result.chronological_age_delta > 0 else "年轻"
    print(f"  年龄差值:   {abs(result.chronological_age_delta):.1f} 年（比实际{direction}）")
    print(f"  衰老状态:   {result.age_acceleration}")
print()
print("  注意：生化指标使用正常参考值估算，")
print("  建议补充实际生化检查结果以提高准确性。")
print("=" * 50)

# 异常指标提示
print()
print("  血常规异常提示：")
if blood_panel["mean_cell_volume_fl"] < 82:
    print(f"  [!] MCV {blood_panel['mean_cell_volume_fl']} fL 偏低（正常82-100），提示小细胞性贫血（可能缺铁）")
if blood_panel["rdw_percent"] > 14.6:
    print(f"  [!] RDW {blood_panel['rdw_percent']}% 偏高（正常12.2-14.6%），红细胞大小不均")
print("=" * 50)
