# 低铁项目：Legacy R1 队列数据流

> 历史文件：当前 Round 2 使用 MIMIC-III n=799（140 events）的 LOS 一致性时间敏感性队列，且结局锚定住院日。

**代码映射**：`run_pipeline.py` · `train_models.py` · `supplementary_analysis.py`  
**用途**：Methods / 脚注 / 分析口径说明  
**关联**：[`FE1_spec.md`](FE1_spec.md) · [`FE1_spec_en.md`](FE1_spec_en.md) · [`reference/manifest.json`](../reference/manifest.json)

---

## 1. 队列划分（FE1）

| 层级 | 含义 |
|------|------|
| **MIMIC-IV train** | 开发集（80%，class_weight balanced） |
| **MIMIC-IV internal test** | 内部验证（20%） |
| **MIMIC-III external** | 时间外部验证（全队列 n ≈ 1,046） |
| **F3 / NH** | 中国探索性外验（选项 β） |

---

## 2. 代码与文稿对齐状态

| 项目 | 状态 |
|------|------|
| ICU ≥48h | ✅ `LOS_ICU_MIN_DAYS = 2` |
| 主分析不平衡 | ✅ `class_weight='balanced'` |
| t₀ | ✅ Excel proxy → `prepare_t0_labs_parquet.py` → `mimic_t0_labs.parquet`（manifest: `t0_source=parquet`）；SQL 为可选升级 |
| 结局 | ✅ 28-day from t₀ (`outcome_28d_t0`) |

---

## 3. 预测文件与队列对应

| pkl | 队列 |
|-----|------|
| `preds/8_features/test_preds.pkl` | MIMIC-IV internal test |
| `preds/8_features/external_preds.pkl` | MIMIC-III external |
| `preds/8_features/F3_preds.pkl` | 湘雅三院 |
| `preds/8_features/NH_preds.pkl` | 南华 |

---

## 4. 分析输出目录

```
result/analysis/
├── manifest.json
├── cohorts/
├── preds/
├── tables/
└── figures/
```
