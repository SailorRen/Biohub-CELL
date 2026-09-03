# V19C Notebook 身份与血缘

## 结论

`SOURCE_CODE_VERIFIED`：本轮只读取得的目标是 Kaggle 私有 Notebook `sailorren/biohub-v19c-public0939-sis14-only`，当前版本为 Version 1，状态为 `COMPLETE`。拉取的 `.ipynb` 为 213,952 bytes，临时文件 SHA-256 为 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`。原始文件只在临时目录用于审计，没有提交到 GitHub。

`SOURCE_CODE_VERIFIED`：目标副本的 12 个 cell source 与 2026-09-03 已固定取得的公开 Notebook `alioman/biohub-v19c-public0939-sis14-only` Version 1 的 12 个 cell source 逐项一致；其中 10/10 个代码单元也逐项一致。该判断基于每个 cell 的 UTF-8 source 字节数和 SHA-256，不基于相似标题。

`UNKNOWN`：Kaggle 元数据中的 `kernel_sources` 是空数组，平台没有在当前可见字段中声明这个私有 Notebook 是公开 Notebook 的 fork。用户明确说明“从公开代码区复制”，且内容完全一致，因此可以记录为“用户说明复制、内容证据一致”；不能升级为“Kaggle 平台已证明 fork 血缘”。

## 目标 Notebook 身份

| 字段 | 只读观察值 | 证据分类 |
|---|---|---|
| ref | `sailorren/biohub-v19c-public0939-sis14-only` | `MEASURED` |
| title | `biohub-v19c-public0939-sis14-only` | `MEASURED` |
| kernel ID | `132979728` | `MEASURED` |
| current version | `1` | `MEASURED` |
| visibility | private | `MEASURED` |
| status | `COMPLETE` | `MEASURED` |
| type/language | notebook / Python | `MEASURED` |
| accelerator | Nvidia Tesla T4；GPU enabled | `MEASURED` |
| internet | disabled | `MEASURED` |
| ScriptVersionId | `UNKNOWN_NOT_EXPOSED` | `UNKNOWN` |

Kaggle `kernels list`、`kernels status`、`kernels pull` 和 GetKernel 只读结果相互支持 ref、Version 1、完成状态和源码大小。`kernels list` 返回的 `lastRunTime` 为 `2026-09-03 09:54:55.453000`，GetKernel 元数据却返回 `2026-08-31T17:09:53.551Z`。两者含义或更新机制没有被平台接口解释，因此本审计不把任一字段用作唯一运行身份或 submission 绑定依据。

## 公开内容基准

公开候选 `alioman/biohub-v19c-public0939-sis14-only` 已在前一日的初始研究中通过 Kaggle GetKernel 取得完整 Version 1 source：

- source response：213,952 bytes；
- source response SHA-256：`363139b1f15ebd4b822b286019c0ce46533d0e045cdb31a99a9ffe0d7c208fd9`；
- 12 cells：2 markdown、10 code；
- 10 个代码单元均已哈希和语义扫描；
- source 中没有保存的执行输出；
- 许可证字段未由已读接口暴露。

本轮再次直接读取公开 ref 时返回 HTTP 403。因此，本轮比较使用的是仓库中已经固定、哈希并通过初始研究验收的逐 cell 证据，而不是声称本轮重新成功下载了公开源码。

## 内容一致性方法

比较单位是按 cell 顺序排列的原始 `source` 文本。每个 cell 同时比较：

1. cell index；
2. cell type；
3. UTF-8 source bytes；
4. source SHA-256。

结果为 12/12 完全相等，没有发现新增、删除、重排或 source 文本差异。副本 `.ipynb` 文件 SHA 与公开 GetKernel source response SHA 不相同并不否定这一结果：两者是不同 API/序列化载体，包含的 Notebook 外层元数据和 JSON 表示可不同。本报告只把“cell source 内容完全一致”作为可验证结论，不把不同载体的整文件哈希写成相同。

逐单元结果见 `02_notebook_cell_audit.csv`。完整公开或副本 `.ipynb` 均未加入仓库。

## 数据源与运行依赖身份

Kaggle 元数据为目标 Version 1 列出三个 Dataset source：

- `pilkwang/biohub-deepcenter-unet3d-center-prior-v1`
- `pilkwang/biohub-temporal-unet3d-seed314159-v1`
- `pilkwang/biohub-tracking-support-pack-50ep-v1`

运行完整性回执进一步记录三份实际 materialized 权重的 SHA-256，以及支持代码仓库 13 个 Python 文件的逐文件哈希与汇总哈希。它支持“该次运行读取了哪些具体小模型/代码工件”的身份审计，但不证明这些 Dataset 的训练数据来源、训练过程、许可证或泛化质量。

## 许可与再分发边界

`UNKNOWN`：当前读到的公开 Notebook/API 元数据没有暴露可确认的源码许可证。为避免把可读取误写成可再分发，本仓库仅保存：

- Notebook 和 cell 的哈希、大小、结构与原创分析；
- 用户自己运行产生的小型日志和审计回执；
- Kaggle 元数据与 submission 绑定摘要。

仓库不保存完整 `.ipynb`、大段源码正文、模型权重、GEFF/Zarr 结果或 `submission.csv`。
