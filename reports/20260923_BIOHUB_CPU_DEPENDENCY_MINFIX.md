# CPU 依赖最小修复：源码已修，云端未重跑

来源：`a9829ed2ba4336ed1db8657007879c0ed2763c6b`；分支：`codex/cpu-offline-chain-20260923`。
授权范围：用户“做最小修复”。本轮只修改代码并做本地测试，不新增任何 Kaggle 保存、会话、准备运行或正式提交。

## 已修改

- `prepare_bundle.py`：保留基础镜像 NumPy／PyTorch 版本；只覆盖 imagecodecs 为 `2026.3.6`。OpenVINO 与 telemetry 仍是已有固定版本。
- 将兼容 imagecodecs 和原有两个补充 wheel 提前下载；首次离线解析同时搜索 support 与补充目录，避免旧 `imagecodecs==2026.6.26` 约束残留。
- 首次真实安装前增加同一完整请求的 `pip install --dry-run --report`。解析失败立即停止，不以 `--no-deps` 安装绕过依赖。`--no-deps` 仅用于获取三个固定 wheel 文件，随后的预检和两次安装均执行依赖解析。
- 打包时允许已核验的本地补充目录，并避免把已有 wheel 复制给自己；锁文件显式包含兼容 imagecodecs。

官方元数据：<https://pypi.org/pypi/imagecodecs/2026.3.6/json> 声明 `numpy>=2.0`、Python `>=3.11`，并列有 `cp311-abi3-manylinux_2_28_x86_64` wheel。这仅证明两包声明约束兼容，不证明整个 CPU 环境可运行。

## Notebook 内嵌脚本：必须重建，不能直接重跑旧文件

已读取原提交 Notebook 的 `PAYLOAD`／`HASHES`／`SOURCE_DIGEST` 布局。它内嵌的旧脚本 SHA256 是 `3819b84aa9ecb4335a5cf84c0be315ec1ee95a029fdab8b42e775f0b3abd9785`。只修改旁边的 `.py` 不会自动修改旧 Notebook。

本轮保留旧 `prepare_batch/preparation_batch.ipynb` 作为失败输入证据，新增 `prepare_batch/rebuild_dependency_minfix.py`。从已同步的完整仓库执行：

```bash
python experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/prepare_batch/rebuild_dependency_minfix.py
```

该命令只在本地生成 `prepare_batch/dependency_minfix/` 下的新 Notebook、匹配 metadata 和回执，不调用 Kaggle、不安装依赖。构建器验证原内嵌哈希及已审阅旧脚本，替换唯一准备脚本并更新摘要；其他 payload 不变。遇到未审阅漂移或不同的已生成文件即停止，不覆盖。

**本轮未在完整原始 Notebook 上执行该重建命令**：当前执行容器无法下载 GitHub 原始文件，连接器仅获得了它的结构和相关片段。已在对应结构的测试夹具上验证重建、哈希、幂等及拒绝漂移。不得声称新自包含 Notebook 已在 GitHub 或 Kaggle 生成。下次操作应先在 Codex 完整工作区执行上述命令、检查回执并同步生成文件，再根据新增运行授权派发；不得重复旧 request ID 或直接提交旧 Notebook。

## 实际验证与限制

本地 `test_dependency_minfix.py` 7项回归测试通过：约束覆盖、补充文件先于组合解析、预检失败停止、补充文件打包无同文件复制、拒绝陌生文件来源、Notebook重建保留其他payload及幂等、拒绝未审阅脚本漂移。

这些测试使用临时目录及模拟 subprocess，不安装真实 wheels、不加载模型，不能当成完整 pip 解析、ABI、图像读取或 Kaggle 运行成功。当前容器网络不可用，完整目标依赖集合也未挂载，因此完整依赖解析 `NOT_VERIFIED`；新代码中的完整预检需要在下一次获授权的目标准备环境实际执行。

GPU／Kaggle新运行／正式提交均0；原A/B、队友母版、权限、旧运行账本、错误回执、模型和阈值未改。云端仍以已有 V2/SV352083775 的 ERROR 为最后已观测状态，`NEEDS_HUMAN_REVIEW`不清除。


## 2026-09-23 完整工作区重建交付

任务 `BIOHUB_CPU_MINFIX_REBUILD_20260923_V01`，来源基点 `cfb060290ad3e257a5c70cffc2e6bc142f0e516b`。任务先以 `d4dfabc363776197a2b91ce2e877472fa6b16064` 推送并固定字节回读，再执行本地重建。上文“未在完整原始Notebook执行重建”为历史记录，现由本节实际结果更新。

状态 **REBUILT_LOCAL_VERIFIED_NOT_RUN**。Python3.11.14实际执行已有测试：7/7通过，subprocess均为mock，不是pip安装或真实解析。保留已有sha助手的ResourceWarning，未作无关修复。原构建器第一次运行退出0，完整216207字节旧Notebook已读取并保留；新文件生成于 `experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/prepare_batch/dependency_minfix/`。本轮无需修复原构建器或测试代码。

独立AST/literal_eval检查新旧完整Notebook，15/15 PAYLOAD哈希、SOURCE_DIGEST及临时空目录展开验证通过；所有Python语法和JSON解析通过。只替换prepare_bundle.py，其余14份payload及其他单元、非payload启动代码不变。两个代码单元均无执行计数和输出。独立校验首次遇到macOS临时路径 `/var` 到 `/private/var` 的别名，规范化临时根路径后通过；没有放宽来源保护。

静态检查确认imagecodecs覆盖为2026.3.6、基础NumPy/PyTorch锁定来源仍为镜像，三个固定补充wheel下载早于完整dry-run、dry-run早于安装；安装不带--no-deps。元数据逐字段等于原请求：同一Kernel、Private、GPU/TPU关闭、Internet on、比赛和Primary V10，code_file在新目录内解析为新Notebook。未创建Version/SV。

第二次同一重建命令退出0；Notebook、metadata、rebuild_receipt三文件字节完全不变。对交接基点已有75个本实验／two-wave文件逐字节比较全部不变，包括旧Notebook、历史错误回执、A/B源码与原账本。

SHA256：

- 原内嵌脚本：`3819b84aa9ecb4335a5cf84c0be315ec1ee95a029fdab8b42e775f0b3abd9785`。
- 新内嵌脚本：`a45316f4671be1c339f49755ddaa82414380b4b5ddcf5b78b4b2156324bcf756`，与当前prepare_bundle.py逐字节相同。
- 新Notebook：`de5b881652019984ba6d6e26dfbc9fea03294341c0bd2a08945097945739467c`。

实际命令退出码、完整stdout/stderr、逐PAYLOAD哈希及可重复性结果见新目录 `local_validation.json`，构建器回执见 `rebuild_receipt.json`。

修复已打入Notebook；真实依赖解析／安装NOT_RUN，ABI、真实图像读取、IR转换及离线推理NOT_VERIFIED。本轮新增Kaggle请求0、未运行模型、未启动CI云端计算。旧V2/SV352083775 ERROR及NEEDS_HUMAN_REVIEW保留。继承的TASK/request_id只是历史代码，不是本轮执行证据；未来云端派发前必须另行冻结批次身份和唯一意图。最终固定commit、远端回读数量与clean状态在交付回复中列明，不将本地打包成功写为云端成功。
