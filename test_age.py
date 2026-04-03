from openage import predict_age

blood_panel = {
    # 血常规
    "mean_cell_volume_fl": 93,
    "rbc_count_million_per_ul": 4.52,
    "platelet_count_thousand_per_ul": 245,
    "lymphocyte_percent": 28.5,
    "lymphocyte_count_thousand_per_ul": 2.1,
    "monocyte_percent": 6.2,
    "rdw_percent": 12.8,

    # 生化
    "glycohemoglobin_percent": 5.4,
    "glucose_mg_dl": 95,
    "creatinine_mg_dl": 0.80,
    "bun_mg_dl": 15,
    "alt_iu_l": 22,
    "alp_iu_l": 68,
    "ldh_iu_l": 138,
    "cpk_iu_l": 132,
    "potassium_mmol_l": 4.0,
    "hdl_cholesterol_mg_dl": 55,

    # 问卷（1=是，2=否）
    "ever_cancer_or_malignancy": 2,
    "ever_angina": 2,
    "ever_arthritis": 2,
    "ever_liver_condition": 2,
}

result = predict_age(blood_panel, chronological_age=45)
print(result.summary())
print(f"\n生物年龄: {result.biological_age:.1f} 岁")
print(f"与实际年龄差: {result.chronological_age_delta:+.1f} 年")
print(f"衰老状态: {result.age_acceleration}")
