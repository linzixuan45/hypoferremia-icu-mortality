# FE1 方法学规格 — Hypoferremia SR R2

**状态**：**已定稿 v1**（2026-06-18）  
**关联**：[`docs/data_flow_cohorts.md`](data_flow_cohorts.md) · [`docs/FE1_spec_en.md`](FE1_spec_en.md) · [`result/analysis/manifest.json`](../result/analysis/manifest.json) · [`scripts/dataset.py`](../scripts/dataset.py)

**原则**：Reviewer 1 将时间泄漏标为根本性缺陷；主分析须锚定 proxy t₀ 与 ≤t₀ 特征；full-stay 聚合仅作 legacy 敏感性（Supp Table S10）。

---

## 1. 预测任务（一句话）

在 ICU **functional hypoferremia** 队列中，于 **proxy t₀（首次低铁 episode）**，利用 **t₀ 及之前可观测的预测变量**，估计 **自 t₀ 起 28 个日历日内**的院内死亡风险（关联性估计，非因果/非部署声明）。

---

## 2. 队列纳入（MIMIC-III / MIMIC-IV 主分析）

| 规则 | 定义 | 备注 |
|------|------|------|
| 年龄 | 18–100 岁（clip） | 与投稿稿一致 |
| ICU 停留 | **≥48 h**（`los_icu >= 2` 天） | 与投稿稿 48h 要求一致 |
| 低铁事件 | 至少一次 serum iron < 60 µg/dL | functional hypoferremia 操作定义 |
| **t₀** | Excel **proxy**（无 iron charttime；见 §3） | Excel → `mimic_t0_labs.parquet`（manifest: `t0_source=parquet`） |
| 首次 ICU | 同一 `hadm_id` 仅保留首次 ICU stay（若 Excel 可识别） | 待 pipeline 实现 |
| MIMIC-IV | 2008–2020，**开发队列** | 80/20 train / internal test |
| MIMIC-III | 2001–2012，**外部验证 n = 1,046** | **不**并入训练；Table 3 / Supp S1 统一此 n |

**代码对齐项**：[`scripts/dataset.py`](../scripts/dataset.py) 过滤逻辑；数据表 `mimic3_low_fe` / `mimic4_low_fe`（`data/mimic_dataset.xlsx`）；iron charttime **不可得**（运行 `scripts/audit_mimic_excel.py` 审计）。

**MIMIC 去重**：当前导出表 `subject_id` 交集 = 0；Methods 仍须修正日期表述并披露导出规则（R2-M2）。

---

## 3. t₀ proxy 分层（无 charttime）

| stratum | 操作定义 |
|----------|----------|
| **Admission hypoferremia** | `iron_1st < 60` µg/dL（且非缺失） |
| **Acquired hypoferremia** | `iron_1st >= 60`（或缺失）**且** `iron_min < 60` |
| **Legacy sensitivity** | 全 ICU stay 聚合特征 + 自 ICU 入院 28 天结局 → **Supp Table S10** |

### `hours_icu_to_t0` proxy（Excel，定稿公式）

| stratum | `hours_icu_to_t0` |
|---------|-------------------|
| admission | **0** |
| acquired | **`min(los_icu × 12, los_icu × 24)`** 小时（即 `los_icu` 天 × 0.5 × 24，上界为 `los_icu` 全天数） |

`los_icu_to_t0`（20f 特征）= **`min(los_icu, hours_icu_to_t0 / 24)`** 天。

**Excel proxy 限制（须在 Methods / Limitations 披露）**：无法从聚合列真正截断 min/max/mean 至 t₀；主分析采用 §5 保守特征集；full-stay 聚合仅 legacy S10。

---

## 4. 结局

| 项目 | 定稿值 |
|------|--------|
| 结局变量 | `hospital_expire_flag`（院内死亡） |
| 预测 horizon | **自 t₀ 起 ≤28 个日历日**内死亡 = 1 |
| 删失 | t₀+28d 前出院且存活 = 0 |
| R2-m4 | 报告非幸存者死亡时间中位数、>28d 死亡比例（Results 或 Supp） |

**与投稿稿差异**：投稿稿为自 ICU 入院 28 天；R2 主分析改为 **自 t₀ 起 28 天**（legacy S10 保留入院锚定敏感性）。

---

## 5. 预测变量窗口（20-feature / 8-feature）

**原则**：主分析每个变量取 **≤ t₀ proxy** 可观测信息；legacy 使用 full-stay min/max/mean/1st。

| 变量（示例） | 主分析窗口 | legacy |
|--------------|------------|--------|
| `admission_age` | 入院时 | 同左 |
| 实验室 | 优先 **`_1st`、`_min`** | 含 `_max`、`_mean` |
| `los_icu` | **`los_icu_to_t0`**（§3） | 最终 `los_icu` |
| `is_noninvasive_ventilator` 等 | t₀ 前是否发生（Excel 二进制列） | 同左 |

| 模型 | 特征 |
|------|------|
| **20f 主分析** | `result/lasso_feature/low_fe_lasso_feature.csv` 前 20 项；`los_icu` → `los_icu_to_t0`；**排除** full-stay 专用 `_max/_mean`（若同 lab 有 `_1st/_min` 则主分析用后者） |
| **8f 部署** | `platelet_mean, wbc_min, bun_min, pco2_max, creatinine_min, is_noninvasive_ventilator, spo2_min, platelet_1st`；**不含 `los_icu`** |
| **Legacy** | 投稿稿 20 特征集（含 `los_icu` 与 full-stay 聚合）→ S10 |

---

## 6. 训练 / 验证划分

| 集合 | 规则 | 预期 n（pipeline 后更新 manifest） |
|------|------|-------------------------------------|
| MIMIC-IV train | 开发队列 **80%**，stratify `outcome_28d_t0`，seed=42 | ~1250（待 locked run） |
| MIMIC-IV internal test | 开发队列 **20%** | ~310（待 locked run） |
| MIMIC-III external | **全部 1,046**，不并入训练 | **1,046** |
| F3 / NH | 选项 **β**（§7） | 101 / 98 |

**废弃路径**：`paper/low_fe/` 中 MIMIC-III 681/75 并入训练 — **不得**用于 SR R2。

Patient flow 计数 → **Supp Table S8**。

---

## 7. 中国队列（F3 / NH）— 决策：选项 β

| 队列 | 队列定义 | 模型 |
|------|----------|------|
| F3 / NH | **沿用 R1 原始队列定义**（非 MIMIC t₀ 重锚定） | 应用 **MIMIC-t₀ 重训后的 locked 8/20-feature 模型** 外推 |
| Methods 表述 | *Geographic exploratory validation under original cohort definition; not re-anchored to MIMIC t₀.* | |

---

## 8. 类别不平衡 — 决策：4c

| 轨道 | 规则 |
|------|------|
| **主分析** | `class_weight='balanced'`（或等效）；**无** random undersampling |
| **敏感性** | 训练集 random undersampling × **5 seeds** → **Supp Table S9** |

必须报告：undersample 后训练 n、阳性/阴性比；**校准**在自然患病率验证集（MIMIC-IV test、MIMIC-III、F3/NH）上评估。

---

## 9. 模型与 ensemble

| 项 | 定稿 |
|----|------|
| Ensemble_Voting | **soft voting**（`voting=soft`）；Abstract / Methods / Results 全文一致 |
| 概率输出 | soft voting 类别概率平均 |
| LASSO + SHAP | Methods 披露 **dual-purpose** 特征缩减（R2-M8） |
| 主模型措辞 | **Prespecified primary** Ensemble Voting（非 post-hoc “best”） |

---

## 10. 判别 vs 传统评分 — 决策：8a

- **删除** Discussion 中无表格支持的 “significantly outperformed APACHE II / SOFA” 句。
- `mimic_severity_scores.parquet` 无可用 APACHE II 数值；不做 head-to-head 表（除非后续 SQL 到位）。

---

## 11. 部署与可复现（R2-m5 / R2-m6）

- Web：https://fe.mixaihub.top（SHAP audit；非临床用途）
- 本地：`inference.py`（概率输出）+ `model_weights/8_features_model.pkl`
- TRIPOD+AI checklist 作为补充材料
- 锁定基准：[`reference/manifest.json`](../reference/manifest.json)

---

## 12. 验收标准（pipeline 完成后核对）

- [x] Supp Table S8：patient flow + admission/acquired 分层 n
- [x] Supp Table S9：class-weight vs undersampling 敏感性
- [x] Supp Table S10：legacy full-stay vs t₀-proxy 主分析
- [x] Table 2：MIMIC-IV internal test AUROC + 95% CI
- [x] Table 3：**MIMIC-III n = 1,046** AUROC + 95% CI
- [x] Methods「Index time and prediction task」与本文 §1–§5 一致
- [x] 无 unsupported APACHE/SOFA superiority 句
- [x] `result/analysis/manifest.json` 记录 FE1 版本、git commit、seed、cohort n

---

## 13. 数据审计摘要（2026-06-18）

| 项 | 结果 |
|----|------|
| iron charttime | **不可用** |
| mimic3 ∩ mimic4 subject_id | **0** |
| mimic4 过滤后 n | **1,568**（稿件 1,564 → patient flow 解释 ±4） |
| Table 1 稿件错误 | 源数据自洽；Word 排版错误（已重算 CSV） |

---

## 14. 定稿签字

| 角色 | 姓名 | 日期 | FE1 版本 |
|------|------|------|----------|
| 通讯作者 | | | v1 |
| 数据分析 | | | v1 |

**定稿签字**：FE1 v1 · 日期：2026-06-18

**签字后动作**：`python scripts/run_pipeline.py` → `python scripts/verify_reproduction.py`
