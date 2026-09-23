# A950 三候选：私有母版交付与队友待执行

任务：BIOHUB_A950_THREE_CANDIDATES_20260923_V01。任务固定提交 c9c674e9b106d422ba83c95c2309bc4cf6413c78；执行分支 codex/a950-three-candidates-20260923。2026-09-23 上海时间。

## 结果与固定入口

状态 **READY_FOR_TEAMMATE_ACTION**。三份母版已实际创建、各 Quick Save 一次并共享给当前比赛团队核实的 dongdongjiaqi，权限均 Can view，Private 保持。保存版本全部14代码单元和1说明单元逐字等于本地对应候选，outputs 空、execution_count 空；本轮未运行模型。队友侧打开、复制、GPU、普通生产、正式提交均未观察到，不能标成跑分成功。

|候选|固定查看链接|Kernel|Version / SV|下一动作|
|---|---|---|---|---|
|V0375|[V0375](https://www.kaggle.com/code/sailorren/biohub-a950-v0375-20260923?scriptVersionId=352145826)|135522207|V1 / 352145826|优先复制、复核后运行|
|V025-L020P|[V025-L020P](https://www.kaggle.com/code/sailorren/biohub-a950-v025-l020p-20260923?scriptVersionId=352143016)|135522297|V1 / 352143016|优先复制、复核后运行|
|V025-L030P|[V025-L030P](https://www.kaggle.com/code/sailorren/biohub-a950-v025-l030p-20260923?scriptVersionId=352147006)|135524886|V1 / 352147006|母版已备；运行 HOLD|

L030P 只在队友 B 的有效 Public ≥ 同窗 D960，或本批 L020P 的有效 Public ≥ 同窗 A 时启动。2026-09-23 21:31 最终只读查询，B 两个既有提交仍 PENDING，L020P 未提交，所以条件尚未满足。

## 既有正式请求对账（MEASURED）

|对象|提交|Version / SV|状态|Public 原始字符串|
|---|---|---|---|---|
|A|56456090|V1 / 351739212|COMPLETE|0.950|
|D960|56416049|V1 / 351441983|COMPLETE|0.948|
|队友 B：dongdongjiaqi/biohub-d960-l030p-20260922|56492412|V1 / 352126664|PENDING|空|
|队友 B：dongdongjiaqi/biohub-d960-l030p-20260922-c2b4c1|56492838|V1 / 352131289|PENDING|空|

两个 B 请求均在本轮开始前已存在：API UTC 时间分别为11:59:07.047、12:17:33.050，不能合并成一个，也未重提、运行或取消。本批 a950 正式条目未发现，正式请求0/3。A、D960精确版本来自归档和同窗提交页面，Public由官方CLI查询核对；不反推隐藏小数或将显示差值当稳定提升。

## 源码构建与验证（SOURCE_CODE_VERIFIED / MEASURED）

完整冻结 A SHA256：393dc558654af6abffd8c786a1b8fd4065a58e5c2a6a0ba61af4b9d3b4be40df；B SHA256：03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb。原件未改。构建源码已先推送8460f67788c3b8abc3ef4df67974562e06573405，再导入平台。

- V0375：velocity 0.375，leaf None。
- L020P：velocity 0.25，leaf 0.20。
- L030P：velocity 0.25，leaf 0.30。

改动仅参数单元0和嵌入支持回执单元5；另外12代码单元保持字节一致。第5单元保留原算法，仅适配候选身份、参数消费断言和 A 对照（velocity0.25、leaf=None）。对照复用候选已选下游配置，非独立 A 生产，更不是正式 Public。原7项选择器、combo、模型、权重、D960、harmonic、DeepCenter、G1、TTA等保持。未使用旧 B 探针。

21项本地测试 PASS：真实小图参数消费与 provenance、全部保护语义、缺失/零/无效评分、真实末帧、分裂、一次性不级联、0.20严格边界、同图0.20删除集属于0.30、ID/行序无关摘要，以及三候选参数和非回执算法AST保持。14×3代码单元AST可解析。测试使用CPU小图，不加载模型，不证明真实精度。原检查器另存本批身份适配版本，保留结构与消费门槛，补充与归档A去重；没有实际CSV，实际文件验收 **NOT_RUN**。

每臂 candidate.ipynb、kernel-metadata.json、source.diff、parameters.json 和 template_readback.json 在本实验目录。build_receipt.json、unit_checks.json保留详细检查及哈希。

## 输入、环境、权限与保存证据

三份保存版本 Input 页面确认：比赛 biohub-cell-tracking-during-development；primary pilkwang/biohub-tracking-support-pack-50ep-v1 **V10**；secondary pilkwang/biohub-temporal-unet3d-seed314159-v1 **V2**；DeepCenter pilkwang/biohub-deepcenter-unet3d-center-prior-v1 **V5**；gate sailorren/biohub-division-train-20260914。

导入后已重新添加 gate，并将三个Dataset从Latest明确固定到10/2/5。gate 使用SV349707105固定URL添加；来源当前只有V1，固定来源页与既有 Can view 权限已回读。L020P、L030P保存版本浏览器下载的metadata直接包含kernelVersion=349707105；V0375的CLI源码保留导入时旧dataSources字段，因此不声称从该字段直接读出gate：该臂结合保存Input的gate slug、固定添加URL和来源V1of1核实。详细证据差异不拼成同一来源。

三份均为Private、Internet=false、GPU=false、TPU=false、machine_shape=None，交互会话始终off。队友复制后须自己选择T4×2、检查实时余额并保持Internet off。每臂Quick Save均明确选择Never save output，没有生产Output或submission.csv。平台nbconvert打包约12秒，属于非运行保存，不是模型推理；保留的历史papermill时间也不能当本轮执行证据。

**环境差异已显式记录：** 三份实际保存docker为 `gcr.io/kaggle-images/python@sha256:dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`；原A实际镜像为 `gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`。导入使用既有dockerImageVersionId31430，未安装依赖或做模型适配；新镜像运行兼容性 **NOT_VERIFIED**。队友副本设置需先复核，不能把模板打包成功当依赖/生产通过。

母版共享保存后均重新打开对话框核对dongdongjiaqi Can view，gate已有同权限，未重复添加。未设Public、未授编辑权、未改第三方输入、未进入队友账号。队友侧挂载能力仍 **NOT_OBSERVED**。

## 实际异常与最小处理

V0375最初从A Copy & Edit后没有当前页跳转，先记REQUEST_UNCERTAIN且不重发；稍后侧栏出现原复制草稿，续接该对象，最终Kernel135522207，未重复创建。浏览器Go to viewer/复制可能打开未列出的窗口，因此用可见侧栏或已知对象链接续接。

末尾CLI两项只读操作发生 `SSL: UNEXPECTED_EOF_WHILE_READING`（OAuthService/IntrospectToken）：查询提交与L030P元数据。各一次后续只读重查成功，保存和提交没有重发。浏览器下载额外回收L020P/L030P的实际metadata；V0375浏览器下载未回收，已用官方CLI完整源码、实际metadata与保存Input验收，不假称浏览器下载成功。

公开增量补查在15分钟范围内完成，见 public_incremental_check.json：742266、742064、741749读取正文与所记录评论；738217仅部分评论；geometric fusion读精确V3/SV351532492页面Public0.948，未重新完整源码审计。其余最新列表仅发现来源，不证明方案成绩，不宣称覆盖所有9月23日新帖，也未擅自换算法。

## 给队友的四步（只需网页）

1. 用本人账号按优先顺序打开V0375、L020P固定链接，确认同队，点击Copy & Edit；L030P先不运行。
2. 确认副本归本人并保持Private，选T4×2、Internet关闭、检查本人实时GPU余额；五项Inputs保留原版本，缺权限不要删除输入。
3. 把副本链接与Input/Settings截图发回用户，先不运行，由用户这边复核，尤其是镜像和固定输入。
4. 复核后本人每候选普通Save & Run All一次，完成后交实际CSV和回执供参数/结构/归档与本批去重检查，合格且额度足够再正式提交一次；若已直接提交则只对账，不重复。报错发截图，不改算法；L030P须满足上述Public门槛。

## 预算及交付边界

新私有母版3/3，非运行Quick Save3/3，正式请求0/3，每臂0/1；队友副本/普通运行未观察到，尚未消费本批计划额度。用户GPU/CPU交互会话、模型推理、训练、Dataset写入、Colab、购买、取消作业、最终选择修改全0。原two-wave账本和CPU研究分支未改。不会后台监控、等待刷新或代队友操作。

本轮完成的是候选构建、非运行母版发布和必要共享。普通产物、真实运行、正式受理及Public增益均未完成。最终Git固定提交与逐文件远端字节核验结果由交付回复给出；不把GitHub验收写成模型提分。
