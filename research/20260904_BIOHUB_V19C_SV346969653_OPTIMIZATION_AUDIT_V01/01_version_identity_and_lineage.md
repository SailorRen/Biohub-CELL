# V19C ScriptVersionId 346969653 版本身份与来源边界

## 结论

`HOST_CONFIRMED`：用户给出的精确 URL 当前打开的是 `sailorren/biohub-v19c-public0939-sis14-only`，查询参数为 `scriptVersionId=346969653`。同一页面同时显示 `Version 1 of 1`，Edit 链接指向 `/edit/run/346969653`，0.939 的 Version 1 分数链接也回指同一个 ScriptVersionId。页面显示运行时 `31m 45s · GPU T4 x2`、日志 `1904.8 second run - successful` 和 307 个输出文件。上述三条页面内独立指针把 `346969653`、目标 ref、Version 1、运行结果与页面分数联系起来。

`HOST_CONFIRMED`：Kaggle API 对同一 ref 返回 kernel ID `132979728`、current version `1`、private notebook、GPU enabled、internet disabled、machine shape `NvidiaTeslaT4`；status API 返回 `KernelWorkerStatus.COMPLETE`。完整 source、runtime log 和 output inventory 的当前版本读取前都强制检查 `current_version_number == 1`。

因此，本任务对目标版本采用 `HOST_CONFIRMED_PAGE_PLUS_CURRENT_VERSION_1_GUARD`：页面直接暴露 ScriptVersionId，API 直接暴露 current Version 1，而源码与输出只在“当前版本仍等于 1”时读取。这足以审计当前唯一版本，但不是“API 响应中有一个独立 `script_version_id` 字段”的更强机器绑定。

## 固定版本 API 缺口

`UNKNOWN`：本机 Kaggle SDK 的 GetKernel 与 output 请求模型虽接受 `version_label`，但对 `version_label="1"` 的只读请求都返回 HTTP 404。CLI 把 `/1` 拼入 slug 的版本拉取方式此前也返回 HTTP 403。没有绕过这些限制，也没有把失败写成 Notebook 不存在或运行失败。

回退规则是 fail-closed：

1. 页面必须仍为精确 `scriptVersionId=346969653`，且显示 `Version 1 of 1`；
2. API 必须返回 `current_version_number=1`；
3. 当前 source 与 output 才允许读取；
4. 任一处出现 Version 2 或更高版本，本回退不得继续。

本轮回退读取出的 `.ipynb` 为 213,952 bytes，SHA-256 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`；完整日志为 111,209 bytes，SHA-256 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`。这两个哈希都与本仓库上一轮目标副本审计一致，是额外的一致性检查。

## 0.939 的绑定

`HOST_CONFIRMED`：本人 submissions 只读返回中，submission `55978992` 的 description 为 `Notebook biohub-v19c-public0939-sis14-only | Version 1`，状态 `SubmissionStatus.COMPLETE`，Public Score `0.939`，private score 未暴露。页面的 0.939 Version 1 链接又回指 `346969653`，因此本轮把 0.939 绑定到目标 Version 1 和该 submission。

这个结论的范围必须保持有限：读取时返回五条本人提交记录，0.939 是其中已完成记录的最高分；另一个不同 Notebook 的 submission `56002593` 当时为 `PENDING`。本任务未轮询、修改、重试或选择它。0.939 不是全球最高分声明，也不是 private/final leaderboard 结论。

## 时间字段冲突

Kaggle `kernels list` 的 `lastRunTime` 返回 `2026-09-03 09:54:55.453000`，与页面帮助文本 `Thu Sep 03 2026 17:54:53 GMT+0800` 和 submission 时间相互接近；GetKernel 元数据却返回 `2026-09-01 03:06:29.998000`。这些字段存在可见冲突，所以报告不以 GetKernel 的单一时间戳决定版本身份，而以 ScriptVersionId 页面指针、Version 1、source/log 哈希和 submission description 的组合证据为准。

## 复制来源与血缘

用户说明该方案来自公开代码区。当前目标 source 的 12/12 个有序 cell source，与仓库前序审计固定的公开 `alioman/biohub-v19c-public0939-sis14-only` Version 1 逐项哈希一致；本轮目标 source 的整文件哈希也与前序目标副本一致。它支持“内容相同”。

但平台血缘仍为 `UNKNOWN`：

- 当前页面显示 `Copied from private notebook (+0,-0)`，未暴露可识别父 Notebook；
- API 的 `kernel_sources=[]`；
- cell 0 自述为 Rishabh Roy 公开 `biohub-div45-stack` 的 fork；
- cell 1 后续又两次写“standalone notebook”；
- 当前接口没有给出一个可核验的 canonical parent ID。

因此不能把用户说明、Markdown 自述或逐 cell 内容相等升级成 Kaggle 已确认的 fork provenance。源码许可证也未由当前目标页面/API 明确暴露，完整 `.ipynb` 不进入 GitHub；仓库只保存哈希、逐 cell 结构和原创分析。

## 输入与运行环境

`HOST_CONFIRMED`：目标元数据列出比赛 `biohub-cell-tracking-during-development` 和三份 Dataset：DeepCenter center prior、TemporalUNet3D secondary seed、tracking support pack。模型 source 列表为空不表示运行没有加载模型；完整日志和 runtime integrity 回执实际记录了三份 checkpoint 哈希。反过来，这些运行哈希只证明本次加载的字节身份，不证明训练数据、训练代码执行、许可证或复现结果。

完整安全元数据保存在 `evidence/kernel_version_metadata.json`；其中不含 Cookie、Token、环境变量值或 Kaggle 签名下载 URL。
