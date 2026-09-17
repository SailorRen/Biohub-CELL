# HOCT 接入错误修复：本地验收报告

## 结论与边界

**FIXED_LOCAL_VERIFIED：仅本地接入修复已验证。修复版云端诊断 NOT_RUN，HOCT提分效果 UNKNOWN，本轮新增正式分数 null。** 原 Sprint02 V1/SV350471527 仍为 PARTIAL_BLOCKED，没有改写失败报告、旧合同、旧评分、原始日志或已运行Notebook。

实际修复了节点 `node_id` 遗漏，显式检查全部所需字段，核查三个边属性调用点，并实现诊断遇到首个确定性接口错误后保存证据、停止其余视野。7项新增测试及4项原guard回归测试通过，待运行Notebook已在本地构建。没有加载模型权重、运行模型或调用Kaggle接口。

## 修改与实测证据

- `hoct_observer.py`：节点显式请求 `node_id/t/mask`；初始边请求 `edge_id`；候选评分边请求 `edge_id/source_id/target_id/similarity`；solution边请求 `source_id/target_id`。读取后检查实际列，缺失时报告调用位置、required、actual及原始异常。接口尚未返回表时actual为null，不伪造返回列。
- 固定版本实际边API会自动补编号和端点，旧三个边读取点没有被证明发生额外云端报错；本次将隐式依赖改为显式且可测试的读取。
- 抽取共享 `map_endpoints/collect_mapped_edges`，测试直接调用修复函数。候选与solution分别按精确标签掩膜映射，不用行号、最近邻或默认编号。真实 `filter(...).subgraph()` 返回GraphView，本次合成选择保留ID17/19；转为InMemoryGraph后编号成为0/1，两种表示均映射到同一G1端点617/719。**这证明接口适配支持重编号，不声称历史云端已出现该问题。**
- `hoct_worker.py`：保留接口错误类别、原始堆栈及已观察状态。`observe_chunk`在异常路径恢复临时模型/求解器包装；已观察求解状态和阶段随异常传播，未知值为null。
- `diagnostic_runtime.py`：保留首个错误视野的B0回退图、评分、覆盖及错误回执，再以INTERFACE_ERROR停止余下视野；不把全回退称为成功。非零worker退出即使有回执也不得作为complete使用；超时、预算和可恢复求解错误仍按原机制处理。
- 未改1/2/4分块、900秒估时、10小时截止、HOCT0.2.0/general_v0、球半径、尺度、求解参数、G1分类器门槛、原选择器或评分器。原 `hoct_guard.py` 未修改。

## 测试环境与结果

复用现有隔离CPU测试环境 `downloads/LINEFIT_BOUNDARY_20260909/scorer/venv`，未安装或升级依赖。tracksdata精确版本为 `0.1.0rc6.dev3+g980c2d30a`，与云端记录一致；InMemoryGraph实为RustWorkXGraph。图后端、基类、Mask源文件与已归档Kaggle support wheel逐字节一致，来源和SHA256见本任务 verification.json。NumPy本地2.4.2、历史云端2.0.2；这不是全云端环境复现。

|验收项|实际结果|
|---|---|
|真实旧错误复现|旧node_attrs请求缺少node_id，访问抛KeyError|
|真实图接口联通|准确Mask、非连续ID、候选C、合成已选S到原apply_guard通过|
|非零分块与编号|chunk_start=10；候选ID2/5/9/12/15/17/19；GraphView及重编号图均通过|
|保护与边界|空图、空边、缺列、空标签、多标签不唯一、未覆盖边、未完成求解通过|
|包装恢复|异常退出后原ILPSolver._solve和model_predict对象恢复|
|接口错误不重试分块|第一次InterfaceError即停止，保留堆栈、阶段与已观察状态|
|诊断快速停止|执行实际runtime停止代码块，注入首个错误；后续视野调用0，剩余7明确标记|
|原guard回归|4/4通过，节点、坐标、保护边不变|

HOCT已选图和错误由小型合成输入/故障注入提供；真实的是固定版本图对象、字段读取、Mask映射、过滤子图和保护函数。没有执行HOCT模型或真实求解器，因此不将11项本地测试称为8视野云端诊断通过。测试开发期间曾有夹具方法名、GraphView/copy认识错误及不适用断言失败，原始输出追加保留在local_tests.log；最终验收以当前代码重新执行结果为准。

## 本地构建与实际命令

新文件：`experiments/BIOHUB_SPRINT02_HOCT_20260917/interface_fix/diagnostic_fixed.ipynb`。
从哈希匹配V1归档替换零基cell5内嵌修复模块及cell7调度代码；其余6个单元完全一致。全部代码语法检查通过，输出为空、execution_count=null。build_receipt.json保存最终源码SHA256；平台Version/SV均null，cloud_status=NOT_RUN。未运行原上传脚本，也未覆盖原构建器或V1归档。

实际执行命令（仓库根目录）：

```sh
python3 experiments/BIOHUB_SPRINT02_HOCT_20260917/interface_fix/build_fixed.py
downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python experiments/BIOHUB_SPRINT02_HOCT_20260917/interface_fix/verify_fix.py --record
```

验收器实际运行test_observer.py和原test_guard.py，校验旧证据哈希、固定包源码、Notebook内嵌源码及空输出。完整实际输出见interface_fix/local_tests.log。

## 预算和交付

Kaggle新增写入、Save & Run、Notebook Version、submission、Dataset写入、训练、模型推理、最终选择修改均为0。旧请求账本字节未改变，旧生产额度没有沿用。G1 0.948仅是已归档基准，本轮未重新读取或提交正式成绩。

安全fetch前工作区洁净；仅快进现有分支至任务书a0b646817f111028b57766618e9b12561e766edd。origin核验为SailorRen/Biohub-CELL，main记录a123f0ad7f8808b44909d4c5fab48caf5147b50c，本任务不修改main。

本地冻结合同SHA256 `b206425e9255bd0a5de27f2e4c303ac0d03f6192abcd45415edb3be78a9c651e`。Git交付采用同分支固定commit回读本轮变更完整字节，回执随收尾提交归档并再次核对；最终commit、remote HEAD与匹配数量见交付回执及最终回复。验收仅覆盖本地修复与交付，不扩张为云端效果保证。

交付后停止。云端诊断须用户另行授权，不自动重跑。
