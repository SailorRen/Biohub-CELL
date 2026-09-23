# Codex：重建依赖修正版 Notebook，完成本地验证与 GitHub 交付

任务ID：BIOHUB_CPU_MINFIX_REBUILD_20260923_V01
仓库：SailorRen/Biohub-CELL
执行／交付分支：codex/cpu-offline-chain-20260923
交接基点：cfb060290ad3e257a5c70cffc2e6bc142f0e516b
沿用目录：experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01

## 1. 目标和边界

最小源码修复已经在 GitHub：保留基础镜像 NumPy／PyTorch，覆盖 imagecodecs 为2026.3.6，提前获取补充wheels，并在安装前增加完整依赖解析预检。不要重新设计这份修复。

当前缺口：完整原始 Notebook 尚未实际重建；旧 prepare_batch/preparation_batch.ipynb 内嵌的仍是旧准备脚本。本轮在 Codex 的完整工作区实际重建、验证并同步可检索文件，而不只报告旁边的.py已经修改。

只授权本任务、必要的本地打包／验证及研究分支GitHub写入。新增 Kaggle 会话、Notebook创建／保存、Save & Run、Quick Save、模型推理、训练、正式提交、Dataset写入及共享修改全部0；不进入Colab，不购买，不启动CI云端计算代替本地检查。

不修改A/B生产源码、权重、参数、队友母版／副本／权限、原two-wave账本或最终选择。旧ERROR和NEEDS_HUMAN_REVIEW保留。本地打包通过不等于依赖安装成功。

## 2. 安全同步，读取已完成的修复

安全fetch原分支，确认包含交接基点。有后续更新先读取并排重；已有任务产物则核验复用，不退回旧版本。工作区有用户改动就用隔离worktree，不reset、stash、覆盖或强推，不合并main。

将本正文保存为：
tasks/CODEX_20260923_BIOHUB_CPU_MINFIX_REBUILD_V01.md
先推送并固定回读，再执行本地重建。本正文即完整任务，不以收到附件或ZIP为前提。

只读必要文件：

- AGENTS.md及本任务。
- reports/20260923_BIOHUB_CPU_DEPENDENCY_MINFIX.md。
- 本实验prepare_bundle.py。
- prepare_batch/rebuild_dependency_minfix.py、test_dependency_minfix.py、dependency_minfix_checks.json。
- prepare_batch/preparation_batch.ipynb、kernel-metadata.json。

旧Notebook必须取得完整文件并作为失败输入证据保留，不用搜索片段拼装，不覆盖原件。

## 3. 实际执行已有测试和重建器

在仓库根目录，用已有Python 3环境依次运行；本机命令为python3时只替换解释器名称：
```bash
python experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/prepare_batch/test_dependency_minfix.py
python experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/prepare_batch/rebuild_dependency_minfix.py
```

保存本轮真实退出码和输出。原7项测试使用mock subprocess，不能写成真实pip安装或依赖解析成功。

生成目录必须为：
experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/prepare_batch/dependency_minfix/

该目录应产生：

- preparation_batch.ipynb
- kernel-metadata.json
- rebuild_receipt.json

不执行Notebook的准备单元或子进程，不调用pip安装、模型转换或Kaggle上传命令。

已有不一致文件时不得强制覆盖，先核对来源。真实文件暴露出构建器的路径、转义或字段处理问题时，只允许针对已复现问题做最小修复并补回归测试；不能放宽来源哈希检查、修改其余算法payload或重写整套打包器。将修复后的新增.py与重新生成产物同步交付。

## 4. 必须补上完整真实Notebook的检查

不要只依赖构建器自报PASS。读取旧、新Notebook，对真实PAYLOAD独立核验，并将结果写为生成目录下local_validation.json：

1. 来源与替换：旧内嵌prepare_bundle.py预期SHA256为3819b84aa9ecb4335a5cf84c0be315ec1ee95a029fdab8b42e775f0b3abd9785；新内嵌内容须与当前修复后的prepare_bundle.py逐字节相同。来源不符先对账，不能删掉保护继续。
2. 改动范围：PAYLOAD文件数保持原来的15；只替换prepare_bundle.py，其余14个文件内容／哈希不变。模型、样本、数值容差及推理流程不改。
3. 完整性：独立重算全部PAYLOAD对应HASHES及SOURCE_DIGEST；用AST/literal_eval提取数据，在本地临时空目录按受控相对路径写出全部文件，核验落盘哈希、所有.py语法及.json可解析。禁止执行整本Notebook或启动准备程序来做这个检查。
4. 修复生效：确认新脚本不再从support自动固定imagecodecs2026.6.26，而是覆盖为2026.3.6；镜像NumPy／PyTorch保留；三个补充wheel先获取，随后完整dry-run，再实际安装。安装不能用--no-deps跳过依赖；固定wheel下载使用--no-deps与安装阶段区分。
5. 元数据：id仍为sailorren/biohub-cpu-small-probe-20260923，code_file指向新目录的preparation_batch.ipynb；Private、GPU/TPU关闭、Internet on、比赛和Primary V10输入保持原请求配置。不新增平台版本或伪造Version/SV。
6. 可重复性：再运行一次同一重建命令，确认生成的Notebook、metadata和重建回执字节不变；旧Notebook和所有历史错误回执未修改。

新Notebook的outputs为空、execution_count为空。本地检查只证明打包及静态一致性，完整依赖解析、ABI、真实图像读取、IR转换与离线推理仍未验证。

本轮不分配新平台request ID，不派发旧CPU-BATCH-PREP-01。生成Notebook中继承的旧TASK/request_id不能被当作新执行证据；未来若授权云端运行，须在派发前另行冻结当批身份和唯一意图。

## 5. 同步最少必要产物

将任务、上述生成文件、local_validation.json及必要修复／测试同步同一研究分支。更新原：
reports/20260923_BIOHUB_CPU_DEPENDENCY_MINFIX.md
追加本轮真实结果，保留旧“未重建”记录并说明已由本轮结果更新，不删除历史。

报告明确区分：mock回归测试、完整真实Notebook本地重建／展开检查、真实依赖解析、Kaggle执行。后两项本轮为NOT_RUN／NOT_VERIFIED。

不增加另一套合同或治理框架。不要把临时展开目录、wheels、模型、原始视频、诊断CSV、凭据或ZIP全量入库；历史平台预算不清零、不添加虚假运行记录。

推送后，从固定commit逐一回读本轮新增／修改的小文件及完整新Notebook，核对字节和SHA256，并检查remote HEAD和worktree。只执行一次最终回读验收，不循环自证。

## 6. 停点和最终回复

通过时写REBUILT_LOCAL_VERIFIED_NOT_RUN；未通过则说明具体文件、错误、已完成步骤和未完成项。不得自动推进Kaggle准备运行、离线链或正式提交，也不因本地PASS清除NEEDS_HUMAN_REVIEW。

最终回复给出：

- 新Notebook、metadata和报告的固定GitHub路径。
- 本轮实际测试数、真实PAYLOAD验证数、原／新脚本哈希及新Notebook哈希。
- 固定commit、远端回读实际一致数和worktree状态。
- 明确“修复已打入Notebook；云端依赖安装与运行尚未验证；本轮新增Kaggle请求0”。

任务完成标志是可从GitHub取到经过真实文件检查的修正版Notebook，不是云端运行或提分成功。
