# X138 X0／X25 私有母版交付

状态：TEMPLATES_PREPARED_TEAM_ACTION_PENDING。观察截止：2026-09-24T23:43:02.923961+08:00（上海）。本轮仅交付母版，模型运行0，正式提交0，Public均null。



- [X0：V1 / SV352443505](https://www.kaggle.com/code/sailorren/biohub-x138-exact-team-20260924?scriptVersionId=352443505)，自身速度系数0.5，优先。
- [X25：V1 / SV352448643](https://www.kaggle.com/code/sailorren/biohub-x138-v025-team-20260924?scriptVersionId=352448643)，唯一算法差异为自身速度系数0.25。

两份母版均Private，已向当前队友dongdongjiaqi授予Can view并回读；队友视角打开、复制和挂载仍待确认。四项Dataset版本为primary10、secondary2、DeepCenter5、head1，另挂比赛输入，不含旧gate。母版None不代表CPU方案。



## 已核验事实

- SOURCE_CODE_VERIFIED：冻结x138原件SHA256 `6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d`，保留12个代码单元顺序。Cell1在配置初始化前明确设定0.5／0.25；增加中文首页和共同只读末尾回执，清除旧执行元数据。`source.diff`保留完整差异。
- MEASURED：本地26项检查通过：nbformat、AST、代码范围、参数顺序、完整head嵌入模块语法、低阈缓存先于head、锚点守卫及CSV链；8个完整嵌入Python字符串已解析。原motion_relink_edges无模型小图覆盖无前驱、自身速度及有效邻域flow；自身速度残差1.0／1.5，有流残差均0且边完全相同。这是机制检查，不是精度测量。外部support模块全部运行时补丁执行未测试，云端依赖与端到端兼容性NOT_VERIFIED。
- SOURCE_CODE_VERIFIED：官方CLI分别下载唯一V1完整ipynb，X0和X25各13/13单元类型、顺序及源码逐字节等于本地候选；全部12代码单元execution_count=null、outputs=[]。Kaggle JSON序列化变化不等于算法漂移；整文件SHA与逐单元结果详见各`saved_version_readback.json`。
- OFFICIAL_FACT：X0 Kernel135684967／V1／SV352443505；X25 Kernel135684985／V1／SV352448643。每个V1的Input详情分别确认primaryV10、secondaryV2、DeepCenterV5、headV1及比赛输入。
- OFFICIAL_FACT：两份保存版本官方元数据均Private、enable_gpu=false、enable_tpu=false、enable_internet=false、machine_shape=None，无kernel_sources。原环境2026-07-01；Docker `dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`。保存时session off，Quick Save／Never save output。页面9s是版本打包，不是模型运行。
- OFFICIAL_FACT：当前比赛团队页核实`dongdongjiaqi`，两个新母版各保存一次Can view并重新打开共享对话框核验。队友未回执，跨账号打开／复制／挂载NOT_VERIFIED。
- SOURCE_CODE_VERIFIED：原Notebook页面Apache-2.0，四个Dataset官方元数据CC0-1.0。head仅下载计算哈希，33913字节／SHA256 `625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c`，未加载。其余三个权重保留原运行时哈希断言，本轮未下载或实测权重。

## 预算及异常

本轮两个私有母版、两次Quick Save、两次新母版Can view保存。Save & Run、模型、训练、正式请求、GPU／Colab／独立CPU会话、Dataset写入、最终选择改动均0。无旧A/B、CPU分支或既有副本改动。

界面导航期间额外出现一个原版未保存草稿，核对为版本数0、session off后用于X25，没有创建第三个对象；确切创建时刻未观测，保留ledger说明。浏览器上传各仅一次，耗时较长；只读Input树点击发生滚动偏移，重载后回读head真实V1。未换入口重发保存。首次nbformat小检查发现继承minor4与cell id不兼容，最小修正为4.5后26项通过；未改推理逻辑。

## 未证明与交付

历史公开0.953属于原x138归档版本，不是本队新分数；X25效果UNKNOWN，不能叠加A的+0.002。模板存在、Can view已保存不等于队友能挂载或推理跑通。后续只由用户协调队友执行，本任务不自动推进。

固定主体commit及逐文件GitHub回读保存在`experiments/BIOHUB_X138_TEAM_PAIR_20260924_V01/github_readback.json`。验收回执可在后续独立提交保存，绑定主体commit避免自引用循环。
