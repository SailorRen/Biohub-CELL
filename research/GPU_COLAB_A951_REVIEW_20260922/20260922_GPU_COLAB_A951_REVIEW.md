# Biohub：GPU额度、Colab执行路径及两份“0.951”方案核查

日期：2026-09-22。此次为官方资料检索、已上传Notebook静态比较、已有输出读取和小型CPU函数测试。没有训练、加载真实模型权重推理、运行整本Notebook、启动Kaggle/Colab会话、购买订阅或正式提交。未写GitHub，本报告为当前对话附件。

## 结论

1. 最近候选不是重复训练，而是固定模型推理、TTA、验证选参和重复后处理。完整预跑数小时并非算法试验每次都需要的最低工作量。
2. 截图的File → Open in Colab是官方导出入口，可配合Colab自己的托管GPU运行；不同于Run → Kaggle Jupyter Server连接Kaggle后台。是否消耗Kaggle额度取决于实际计算后台，不能只看网页名称。
3. 不能承诺Colab执行一次后就一定能零Kaggle普通运行提交新版本。需要核对本比赛当前保存版本、输出和加速器绑定要求；旧Quick Save经验不能替代当前平台事实。正式隐藏评分必须完整处理当次隐藏输入。
4. 两份附件确有快速生产结构和关联改动，但此次未取得两目标页的精确Version/SV与正式Public面板；标题0.951尚未独立验证。不能据此宣布本账户达到0.951，也不能据代码缺陷反推作者一定没有0.951。
5. 快速版主要可借鉴：移除验证选参、减少重复图处理、固定生产配置、batch 4→8、工作空间限制、并行后处理。DivNet及密度距离覆盖存在失效路径，不能按介绍原样相信。

## 1. 本项目最新已归档状态

GitHub分支codex/two-wave-four-submit-20260922的本次读取HEAD为3540a5acab8709a7cc42eef1f4fa18f66d44aa02。
读取reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md末节确认：
- A（D960-V025）Kernel135318885 / V1 / SV351739212普通运行9029.9秒，即2小时30分29.9秒。
- 实际CSV241889行，4样本；独立检查通过。velocity0.25实际调用127524次，leaf禁用。
- 原选择器选中combo(tight55+bonus125+relaxed9)。
- 上海2026-09-22 14:40:43已正式提交，submission56456090；14:41:20回读PENDING、Public原始空字符串。
- 提交续接新Notebook0、Save & Run0、正式请求1；总账正式1/4。B/C/D未执行。
以上是GitHub固定报告归档，不是本次登录Kaggle实时查分。已提交A不需再运行或再次提交。

固定报告：https://github.com/SailorRen/Biohub-CELL/blob/3540a5acab8709a7cc42eef1f4fa18f66d44aa02/reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md

## 2. GPU消耗的原因与可削减部分

最近生产读取固定主模型、secondary、DeepCenter及G1 gate，没有新fit/optimizer训练。每个独立Save & Run仍执行普通推理与整套后处理，并继承8视野验证、7项后处理选择及组合生成。

本次特别修正此前“CPU回放”的笼统说法：
- A/B构建器在候选处理后再次调用original(copy.deepcopy(nodes),copy.deepcopy(edges),**kw)。
- runtime.install中original是filter_output_graph。
- filter_output_graph每次新建repair_frame_cache和deepcenter_heatmap_cache，并调用gap/安全分裂处理；DeepCenter模型通常在CUDA设备上，热图计算会执行模型前向和TTA。
- 因此这次回放不仅有CPU图操作，也可能重新计算DeepCenter GPU热图；没有重新训练，也不等于再次运行全部上游主模型。
- G1的局部分裂影子回放与外层完整filter回放不同；共享缓存时不能简单把每次调用都算成完整GPU重复。

不能凭静态代码算出精确浪费时长。下一步应复用已有日志阶段时间，而不是新增独立GPU性能诊断。

来源：
- https://github.com/SailorRen/Biohub-CELL/blob/4dca986a5bd61e3191ff790b74b505017678652e/experiments/BIOHUB_TWO_WAVE_20260922_V01/build.py
- https://github.com/SailorRen/Biohub-CELL/blob/1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca/experiments/BIOHUB_SCORE_TRIO_20260921_V01/runtime.py
- D960同固定commit下candidate.ipynb，以及此前上传同源Geometric Fusion中的DeepCenter/filter函数。

建议分开：开发阶段保存同配置的上游预测/必要热图，多个后处理共享；最终生产只做必要推理、确定的后处理和输出合法性检查。只有模型/输入/检测配置不变才可复用缓存。最终隐藏数据必须重新推理，不能使用可见4视频的结果替代隐藏预测。

关闭原选择器不是纯日志删减：原选择器实际影响最终配置。应显式采用有来源的选中配置、保留G1 gate和必要阈值；不能关闭validator后默认base并宣称与D960等价。

## 3. Colab三种入口不要混淆

|入口/执行方式|实际意义|对GPU额度的影响|
|---|---|---|
|File → Open in Colab，连接Colab自有托管GPU|导出Notebook并在Colab运行|使用Colab分配资源，不使用Kaggle普通GPU会话|
|Run → Kaggle Jupyter Server，再从Colab连接|Colab仅作为前端，后台为Kaggle|仍占Kaggle的会话资源|
|File → Link to Colab|关联账户/验证适用订阅权益|不是直接把当前作业迁到Colab|

用户当前免费Colab也可能取得GPU，但未在本次连接验证，不能保证型号、余额或持续时间。迁移普通工作不一定需要Pro。

最小迁移只处理环境：Notebook源码、固定数据/权重路径、Kaggle输入下载授权、依赖版本和实际GPU数量。不要将整个数据集下载到Mac；可直接下载必要输入到Colab运行时。不将Token写进Notebook输出或GitHub。用Kagglehub/官方API下载时遵守访问权限和比赛条款。

不能把Kaggle数据留云端的旧执行约束误称为比赛禁止Colab。也不能假定点击导出就已经迁移全部依赖和私有输入，应检查实际导出的初始化代码。

正式评分仍在Kaggle。Colab的CSV只证明开发运行，不自动替代隐藏评分；不要依靠伪造占位输出、隐藏数据硬编码或未验证的Quick Save路径宣称可以零额度正式提交。可核对平台当前支持的外部导入/版本提交方式；若仍要求普通完整产物，则运行精简生产版而非带整套研究循环的Notebook。

官方依据（本次阅读的是官方正文/搜索缓存，平台页面可能动态变化）：
- File导出：https://www.kaggle.com/product-announcements/470030
- Kaggle后台远程连接：https://www.kaggle.com/product-announcements/567740
- 比赛数据下载到Colab：https://www.kaggle.com/product-announcements/540971
- Colab资源限制：https://research.google.com/colaboratory/faq.html
- GPU使用建议：https://www.kaggle.com/docs/efficient-gpu-usage
- Kaggle工作人员区分普通commit和正式submission：https://www.kaggle.com/c/nfl-health-and-safety-helmet-assignment/discussion/274509 （历史其他竞赛说明，不冒充Biohub逐作业扣时审计）
- Biohub主办方解释可见测试为占位：https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/716062

## 4. 两份新附件身份与已有运行时间

以下均来自用户附件已有执行metadata/output，不是本次运行，也未独立验证真实输出CSV；逐单元指纹见source_review_manifest.json。

|项|haideptry Fast ILP|takaito a951-gshift|
|---|---|---|
|文件字节|451222|454141|
|SHA256|50e9dca61fd776a673edf6c382f0a3f27988102e1b2c7d12f30365772fb68689|2c5fa9a028a11c90f1726a4812c35bb7756006c46d592c23e927090a2adf1a5b|
|单元|17总计，8代码|18总计，9代码|
|代码AST|8/8通过|9/9通过|
|整本运行|1393.575243秒，23分13.6秒|2065.503079秒，34分25.5秒|
|主要模型推理单元|563.237534秒|596.91秒|
|后处理单元|603.42634秒|897.874529秒|
|依赖准备单元|218.628038秒|560.030631秒|
|日志最终CSV行数|245195|245398|
|正式Public与SV绑定|未独立取得|未独立取得|

Fast版推理+后处理约19分27秒，接近标题19m；包含准备等的整本时长为23分14秒。不能把标题作为整本时长，也不能以普通可见4视频时长预测隐藏测试出分时间。Gshift比Fast慢的观测不是受控速度消融，包含不同环境/启动成本，不能全归因gshift补丁。

两者共用8个基础代码单元；gshift额外增加一个覆盖配置单元，另两处源单元修改配置和motion函数。多数核心生产源码同源，不能称两条独立新主干。

## 5. Fast版有哪些真实可借鉴改动

### 已看到的效率改动

- 禁用并删除完整validator/后处理参数扫描；固定tight5.5。
- batch4→8；实际worker命令是8。
- CUDNN_CONV_WSCAP_DBG=1024；子进程也设置。
- 4线程并行处理各视频的后处理，不是所有步骤都纯CPU，DeepCenter仍可用CUDA。
- 没有我们额外加入的原版回放/对照模块。
- 双GPU视频分片我们原来已有，不能把它算成我们缺失的创新。
- 对比同源旧附件，依赖准备和13支持脚本的预期哈希没有变化；没有看到独立替换ILP求解器的实现。标题Fast ILP不足以证明新的求解算法。

这些改动不是逐项受控实测。删除回放可能保留预测；固定选参、batch变化及并行实现需核对输出和数值行为，不能保证一键保持Public。

### 关联打分：relative-rank / mutual-best

对原边logits同时考察行/列排名，列第一加0.12，行第一加0.06，互相第一再加0.06，再进行softmax/sigmoid。日志明确记录补丁实际应用。它不需要重新训练，但改变关联概率与ILP候选图，不是仅运行加速。可能偏好明确的一对一匹配，是否伤害分裂必须平台验证。

### 与D960的区别

检测0.965而非0.960，DeepCenter安全分裂阈值0.25而非0.20；没有自有G1分类门；存在密度分组速度/bonus调整；没有F1邻域流，也没有之前Geometric Fusion的leaf剪枝。故整本替换不等于只加一个已验证组件。

## 6. Gshift具体做什么

每对相邻帧通过互为最近邻（半径12µm）取得可靠匹配，至少20对时取三维位移中位数Δ_t。没有足够匹配则使用零位移。

匹配时：
- 没有历史前驱：predicted = x_t + Δ_t。
- 有前驱：predicted = x_t + Δ_t + w * [(x_t - x_(t-1)) - Δ_(t-1)]。
- 距离门槛也相对x_t+Δ_t判断，但边的真实物理距离仍单独保存。

它补偿整体漂移，不直接平移最终CSV坐标，也不是检测阈值调整。F1用局部邻域位移，Gshift用帧级整体位移，不能因为都叫运动补偿就无条件叠加。

CPU小图验证：关闭gshift时与Fast原函数一致；25点、3帧、每步2µm平移的测试记录两个有效shift，范数合计4µm。仅证明行为，不证明真实质量增益。

## 7. 不能忽略的失效路径

### DivNet加载不等于参与输出

两本唯一的divnet_score_division调用处都在 `if OUTPUT_DIVISION_GEOMETRY_FILTER and edges` 下；该开关默认0，已有配置日志为false，没有后续启用路径。因此本附件记录的默认运行不能据“DivNet loaded”宣称DivNet否决了分裂。

即使启用外层开关，原评分函数将(4,16,32,32)片段连续unsqueeze两次，变成(1,1,4,16,32,32)六维输入；首个Conv3d需要四/五维。小型CPU测试实际捕获形状错误，函数的except Exception使返回值为None，调用者因而跳过否决。没有读取真实checkpoint；修复必须核对训练模型的输入协议，不能任意挤维度后宣称使用正确权重。

### 密度分组的距离没有实际传入计算

函数虽然接收tight_um、relaxed_um，但循环使用全局MOTION_RELINK_TIGHT_UM和MOTION_RELINK_RELAXED_UM；实际组别速度与bonus可改变，组别距离覆盖不生效。CPU测试向函数传tight/relaxed100µm，但全局5.5/10仍阻挡10.5µm连接；改全局relaxed为11才通过。

这些问题说明不能按说明文案归因，不等于证明作者分数虚假。修复也属于新候选，不能自动继承标题0.951。

## 8. 立即推进顺序（建议，不是已执行任务）

A已有正式提交56456090，不再花GPU重跑。

先停止按旧数小时研究Notebook复制后续候选。最短路径是将验证与额外回放移出生产、固定已记录的下游配置，并复用已有预测/热图做后处理开发。缓存缺失时只在Colab真实托管GPU取得一次必要上游预测，不启动大训练或重复全量8视野诊断。

用截图入口导出，确认后台为Colab托管GPU而非Kaggle远程服务器；先验证分配与必要依赖/私有输入可访问，再进行一次有限普通运行。免费资源不可用时，才选择已有Kaggle剩余额度可容纳的精简运行或经用户确认购买Pro关联增额，不声称已解决当前账号资源分配。

公开分数只需要对两个精确目标Version/SV/Public及源码做小范围页面绑定；不是新一轮全网调研。确认某精确版本确0.951且可复现时，优先单次原版平台复现作为完整方案证据，再做本账户增量；未知时仍可按明确假设研究Fast结构、relative-rank或gshift，不标记已提分。

本报告不授权/启动新Notebook、正式提交、配额购买、Dataset写入、取消作业或修改最终选择。可用算力、当前Public分数和完整Colab到Kaggle提交路径仍须实际工具核对。
