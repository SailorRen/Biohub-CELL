# V19C submission 与 0.939 分数绑定

## 绑定结论

`MEASURED`：Kaggle 本人 submission 历史的只读记录将以下四项绑定在同一条记录上：

| 字段 | 值 |
|---|---|
| submission ID | `55978992` |
| description | `Notebook biohub-v19c-public0939-sis14-only | Version 1` |
| status | `COMPLETE` |
| Public Score | `0.939` |
| file name | `submission.csv` |
| date（CLI 原样） | `2026-09-03 09:54:56.607000` |

因此，用户截图中的 0.939 不再只是卡片或页面残留值；它已绑定至目标 Notebook ref 所述的 Version 1 和一个具体 submission 记录。

## 与 Notebook 身份的交叉核对

目标 Notebook 的只读元数据同时显示：

- ref 为 `sailorren/biohub-v19c-public0939-sis14-only`；
- current version 为 `1`；
- status 为 `COMPLETE`；
- source 已完整取得并审计。

submission description 与这些字段一致。Kaggle 当前接口没有暴露可独立记录的 ScriptVersionId，因此绑定强度是“submission ID + description 中 notebook ref/Version 1 + 当前 Version 1 source”，而不是 ScriptVersionId 级绑定。ScriptVersionId 记录为 `UNKNOWN_NOT_EXPOSED`。

## 分数范围

截图显示的四条记录中，0.939 高于 0.938、0.938 和 0.885。本轮 CLI 也返回四条本人 submission 记录，目标记录的 Public Score 最高。因此可以说“在本轮读取到的本人四条 submission 中，V19C 的当前可见 Public Score 最高”。

不能据此说：

- 它是整个比赛 global leaderboard 的最高分；
- 它是 final/private leaderboard 的最高分；
- 未来评分补丁或重评分后仍保持相同；
- 它相对 0.938 的 `+0.001` 是某个单一代码改动造成。

## 截图与 API 的证据角色

用户截图哈希为 `2d6e2b21bfc6d01ac45bab4d1ec2251e7d2e884cd26f6ae1fdbac79e5a4c069e`，清楚显示目标描述、Succeeded、Version 1 和 0.939。截图用于保存用户当时看到的界面状态。

机器绑定以 Kaggle submissions 只读返回的 submission ID、description、status 和 publicScore 为准。两类证据相互一致，但只有 API 记录补齐了截图中不可见的 submission ID。

## 本轮外部动作边界

本轮没有创建或重试 submission，也没有选择最终 submission。`55978992` 是用户请求之前已经存在的记录，本任务只读取其状态。Kaggle submission 创建计数为 0。
