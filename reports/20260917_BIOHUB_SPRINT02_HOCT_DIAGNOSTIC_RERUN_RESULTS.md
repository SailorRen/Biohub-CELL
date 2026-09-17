# HOCT 修复版云端配对诊断：运行中回执

## 结论

- **DIAGNOSTIC_RUNNING，整体 PARTIAL**。V2 已在 Kaggle 启动，尚未取得终态，不能称修复链路已经跑通。
- 可靠覆盖 C、选中 S、删边 D、正确结构变化、完整官方配对分数及原局部门槛：均 UNKNOWN/null。
- 本地最终图复算 NOT_RUN：新版本最终图尚未回收。没有把旧 V1 全回退结果作为本轮结果。
- 本轮 Public=null；生产 NOT_RUN；正式 submission=0；G1 已归档 Public 0.948 不变，最终选择未修改。

## 身份与读取边界

任务 BIOHUB_SPRINT02_HOCT_DIAGNOSTIC_RERUN_20260917，分支 codex/sprint02-hoct-20260917。
任务书 245f9b2b8615133d2919c4c619e15aead40eb5d4；环境补充 d186ede27518018c1890248068a54272334eb6ff。

MEASURED：Kaggle SDK 最新读取 `2026-09-17T09:16:33.191096+00:00`（UTC）；kernel **134683728**，**V2 / SV350526849**。
Save & Run 请求时间 2026-09-17 17:10:33 上海；平台回执 17:10:37。
SV 来源为原页面 Version History 的 Viewing Version 2 和对应 Edit 链接，不点击 Edit、不启动交互会话。页面默认渲染仍可显示 V1，已明确排除其输出。

完整回读 V2 全部 8 个代码单元，逐字匹配冻结启动副本。平台 JSON 哈希 `32450b220796b57014317a3493e0c2b671d956691a661ef7e6026290e2d2b0a0` 与本地文件哈希不同属于序列化差异；代码一致性单独核验。
当前未收集终态输出，分页完整性未通过，不能称输出清单完整；运行中空列表表示未取得，不能推断无输出或未运行。
原件、原合同、V1 账本、旧失败与修复报告保留原样。已读范围及固定模块/缓存核对见 source_preflight.json，不重做全仓审计。

## 最小修改与验证

SOURCE_CODE_VERIFIED：固定原件 SHA256 `1f4cbb3c98089bfb5f3fa0901922e87edb6cb88636e12af1dec6f645a919c729`。
启动副本 SHA256 `4edc1bf0b81d678444a0720015b298807fe1abcb5faff40c41c8369cd3a5aa21`。
预检源码 SHA256 `206d286218ccde5f17c74f35d77ac25ac733a9fe1ac5f268849de270add785fc`。

只在单元索引7的离线安装/版本保持断言之后、首次 worker 启动之前插入明确标记的环境检查块；其余单元源码逐字不变，输出为空、执行次数null。见 launch.diff、launch_receipt.json。
精确检查实际导入 tracksdata 的版本和三个安装源码文件，期望值来自固定修复回执；失败写 BLOCKED_ENVIRONMENT_MISMATCH 并抛错，不自动改库。worker 使用同一 sys.executable、继承环境，检查之后无依赖修改。

MEASURED：仅新增3项轻量测试通过：真实本地环境匹配、注入版本错误、注入源码错误；后两者模拟推断调用0。未运行真实模型。复用此前已通过的7 observer+4 guard测试及8缓存哈希回执，未重复未变化测试。云端环境是否通过仍UNKNOWN。
本次合同 SHA256 `b0f1a99bc0d990e803c1b7f76008a51911448924137fe2847106dafb31684f80`。合同机器验收未完成，不能用本地测试或Git交付替代云端结果。

## 固定科学范围与未完成事项

仍为原8视野、2胚胎的**非独立回归面板**；secondary训练包含8视野，primary谱系UNKNOWN。输入、HOCT权重、1/2/4分块、保护边、删边门和官方评分器均未改动。
逐视野未知字段保存在 results.json，未运行/未观察结果不填0。尚不能判断HOCT有无收益或给出生产建议。

仍待既有V2的终态日志、环境回执、真实覆盖/删边、全部最终图和官方配对评分；取得后才可本地复算与归属已知正确连接。任何环境或接口错误按固定源码停止，不创建第三版。

## 实际预算与交付

本轮 Save & Run **1/1**，底层 SaveKernel transport send_calls=1，重试0；Sprint02诊断累计2。
训练、生产、正式submission、Dataset写入、最终选择修改均0。

启动前固定提交 **ec891aecd41b2897da5fae86efe372855b0037ac** 已推送并回读 **21/21** 文件一致；见 prewrite_remote.json。
启动后的账本、源码绑定和本报告继续同步同一分支，最终交付commit与远端回读见本轮交付回执/最终回复。origin/main仍为 a123f0ad7f8808b44909d4c5fab48caf5147b50c。

本会话按任务书运行中分支停止，不承诺后台继续、不创建监控、不重发。当前不是诊断完成结论。

## 实际命令

```text
python3 experiments/BIOHUB_SPRINT02_HOCT_20260917/diagnostic_rerun/build_launch.py
downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python experiments/BIOHUB_SPRINT02_HOCT_20260917/diagnostic_rerun/test_env_guard.py
python3 experiments/BIOHUB_SPRINT02_HOCT_20260917/diagnostic_rerun/verify_remote.py --commit ec891aecd41b2897da5fae86efe372855b0037ac --output downloads/BIOHUB_SPRINT02_HOCT_20260917/rerun_prewrite_remote.json
python3 experiments/BIOHUB_SPRINT02_HOCT_20260917/diagnostic_rerun/save_once.py
python3 experiments/BIOHUB_SPRINT02_HOCT_20260917/diagnostic_rerun/read_run.py
```

启动入口已消费预算，不得再次用于写入。read_run.py仅只读；大型原件留在Git忽略目录，其本地位置及SHA256见diagnostic_platform.json。
