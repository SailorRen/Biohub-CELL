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
