# XR0最后两候选正式评分

任务：BIOHUB_XR0_LAST_TWO_20260926_V01；遵循SCORE_FIRST_V02。
当前状态：RUNNING_BATCH。尚未启动普通运行或正式提交，Public为UNKNOWN。

固定交付b05a5e115111cfae66424f0b2e7eac09c1b914b8任务原文9571字节及SHA256核对通过。沿用原XR0十二个有效单元，XD960仅DET和守卫0.960，XRL9仅RELAXED_UM=9.0；其余算法不变。附加原head哈希核验、只读门限消费计数和上一批轻量输出验收，不增加推理。

本地18项必要检查通过，包括nbformat、逐单元AST、允许diff还原、参数读取顺序、真实support源码上的动态补丁与缓存先于head。没有CV或G1退分调查。

实时检查：sailorren；正式额度2次，页面约7小时重置；无活动事件。GPU界面00:59/30小时，API总量21600秒及reserved=0，timeUsed序列化异常；按较小6小时总量减界面约59分钟规划。并发上限未明确公开，上一批两槽实际获准，本批将同批请求两份，不取消其他任务。

完整团队54条submission无本批记录。旧XD960 V1/SV352620382仍仅9秒Quick Save，源码相符、无输出；不改旧共享资产，使用本批独立对象。精确新slug只读GetKernel返回403，未据此证明不存在；采用完整团队提交表、当前本账号比赛Notebook列表与无活动事件完成排重。

预算：计划完整GPU运行2、共享工程备用1；正式请求上限2、每候选1；当前消耗均0。候选、账本和检查位于experiments/BIOHUB_XR0_LAST_TWO_20260926_V01/。

## Run receipts

Code commit 2a574a0127abdfc46fb8fd33f3d0cc5778a77b3a: remote 26/26 byte-equal.
XD960 V1/SV353050916; XRL9 V1/SV353050971. Both SAVE_AND_RUN_ALL accepted, GPU T4 x2; full runs used 2/2, formal requests 0/2. No output acceptance or Public yet. Earlier LOCAL_PREPARED statements above describe pre-launch history.
