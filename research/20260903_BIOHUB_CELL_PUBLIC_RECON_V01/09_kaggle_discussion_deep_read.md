# Kaggle Discussion 深度阅读

> 范围：2026-09-03 登录态浏览器只读。正文不再分发；仓库仅保存 URL、动态元数据、页面哈希和原创摘要。
> 证据解释：Host/Kaggle Staff 与普通参赛者严格分开；参赛者数值若无版本或独立复算，不作为官方事实。

- 三页清单发现：73 个唯一主题。
- 实际正文深读：30 个唯一主题。
- 完整线程：30 个。
- 浏览器操作：只导航、等待、展开回复和读取 DOM；没有点赞、回复、发帖或提交。

## 1. Cell Tracking In-Person Workshop

- source_id: `KDISC_738833`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738833
- 作者/角色: Jordão Bragantini / Competition Host
- 访问时间: 2026-09-03T08:26:37.724Z UTC；2026-09-03T16:26:37.724000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: true
- 页面字节/SHA-256: 2307 / `bf15717dcd22a990edd05677da740d0c95b1844faf775a5090c65d76a9dbe56e`
- 摘要: Competition Host宣布2026-11-30至12-03在Redwood City举办线下workshop，并表示竞赛结束后邀请符合官方资格的获奖者；属于 HOST_CONFIRMED。

## 2. What if we want the raw data, and/or want to use a language other than Python?

- source_id: `KDISC_728620`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728620
- 作者/角色: Wayne B Hayes / Participant
- 访问时间: 2026-09-03T08:26:22.360Z UTC；2026-09-03T16:26:22.360000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: true
- 页面字节/SHA-256: 2223 / `dc76c79f68c520d547a556016da227b516ed5dd3c7dd8c41a0e7af34c008f889`
- 摘要: 参赛者询问原始数据/非Python实现；Competition Host仅说明Zarr是标准且有多语言实现，没有确认另供TIFF或原始数据。

## 3. Welcome to the Biohub - Cell Tracking During Development Challenge

- source_id: `KDISC_716062`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/716062
- 作者/角色: Thibgolds / Competition Host
- 访问时间: 2026-09-03T08:26:19.606Z UTC；2026-09-03T16:26:19.606000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 6/6；Host 回复: true
- 页面字节/SHA-256: 9383 / `7a14a519ac4ef4dd79193d6aaef028c2a4497f7809095426880b3b28558ab579`
- 摘要: Competition Host介绍任务、稀疏标注、官方资源和推荐方法；Host回复确认公开test文件只是运行占位样本、私有test更大且与公开train无重叠，并说明仓库已加入CSV转GEFF脚本。

## 4. How to get started + Competition's Official Discord

- source_id: `KDISC_714101`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/714101
- 作者/角色: María Cruz / Kaggle Staff
- 访问时间: 2026-09-03T08:26:16.653Z UTC；2026-09-03T16:26:16.653000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 7/7；Host 回复: true
- 页面字节/SHA-256: 7461 / `53195b70bf84ca396eda83510b1ba1b7ab5f19c9f644f834f4c444d75f02fca4`
- 摘要: Kaggle Staff说明官方Discord是公开但不由Staff/Host监控，重要信息应留在论坛；评论中出现metric exploit报告，Host仅确认正在调查。最终补丁结论以专门Host/Staff帖子为准。

## 5. focus3d : one of the best 3d cell segmentation

- source_id: `KDISC_738217`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217
- 作者/角色: hengck23 / Participant
- 访问时间: 2026-09-03T08:24:22.762Z UTC；2026-09-03T16:24:22.762000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 15/15；Host 回复: false
- 页面字节/SHA-256: 6278 / `74d5392cc1c9352865c154066df02428ee46137a332faf672589fa3c1daa6561`
- 摘要: 作者展示FOCUS-3D尝试并延伸到HOCT、Trackastra和合成/增强数据方向；多条回复是设想或草稿链接，未证明当前比赛效果，归类 COMMUNITY_REPORT/INFERENCE。

## 6. Question about the node-count adjustment in the metric (adj_edge_jaccard can exceed 1)

- source_id: `KDISC_739018`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739018
- 作者/角色: Michael Hernandez / Participant
- 访问时间: 2026-09-03T08:17:50.482Z UTC；2026-09-03T16:17:50.482000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 2/2；Host 回复: false
- 页面字节/SHA-256: 5018 / `5392326318b414aea9b7cdf7dc6475ee0b45e212f06b3d90c9adfc50d0967e9b`
- 摘要: 参与者从公开 scoring code 指出预测节点少于 estimated_number_of_nodes 时 signed ratio 会使调整系数大于1，并给出本地样例；两条评论为参赛者的合成测试或策略观点，未见主办方确认，必须标 COMMUNITY_REPORT/SOURCE_CODE_PENDING_VERIFY。

## 7. Quick question for anyone above the 0.94 line — is the detector still a 3D UNet heatmap for you, or did you move to something else ?

- source_id: `KDISC_738276`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738276
- 作者/角色: Rishabh Roy / Participant
- 访问时间: 2026-09-03T08:24:51.302Z UTC；2026-09-03T16:24:51.302000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 4/4；Host 回复: false
- 页面字节/SHA-256: 3816 / `9037514516aab1f4377033bb401caf10c2d1a09bf98b1c3d3d61676b19e2d417`
- 摘要: 参与者讨论3D U-Net以外检测器及proxy/LB关系；关于LB dense labels的说法被其他参与者质疑且无官方回复，故该点 UNKNOWN。

## 8. Detector overfits past ~epoch 10 on fixed sparse-GT frames -- anyone else see this?

- source_id: `KDISC_738773`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738773
- 作者/角色: nusrati / Participant
- 访问时间: 2026-09-03T08:24:29.004Z UTC；2026-09-03T16:24:29.004000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 2/2；Host 回复: false
- 页面字节/SHA-256: 3141 / `4c9fcf2fab1d8e383c254fb0056e5206fbac68500b101aae972afd9da37dc321`
- 摘要: 作者报告固定稀疏标注帧训练时loss下降但真实metric恶化、peak数增加；无可绑定训练产物，属于 AUTHOR_CLAIM，不能当作通用结论。

## 9. Hand labeling - is it external data?

- source_id: `KDISC_737103`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737103
- 作者/角色: Tim Krige / Participant
- 访问时间: 2026-09-03T08:22:11.534Z UTC；2026-09-03T16:22:11.534000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 5/5；Host 回复: false
- 页面字节/SHA-256: 3117 / `95fd05774da1ab4a62f3360e1105dc90c714b1557b95bb508c8c2a302f0135c0`
- 摘要: 参赛者询问手工标注外部数据是否合法；评论意见互相冲突且无主办方答复，故结论 UNKNOWN，不能据此判定规则。含一条已删除评论。

## 10. what layer did ur gains actually come from

- source_id: `KDISC_737543`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737543
- 作者/角色: Kevin Park / Participant
- 访问时间: 2026-09-03T08:25:07.934Z UTC；2026-09-03T16:25:07.934000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 8/8；Host 回复: false
- 页面字节/SHA-256: 5987 / `350ffeb8cb53f77b35f1e0ac47dee1ee1bf2812ecfa17a8061bf1b8af4d83c12`
- 摘要: 多位参赛者讨论检测、链接、division层的相对作用并报告个人CV/LB数值；页面嵌套回复已展开。所有分数均未绑定submission/version，按 COMMUNITY_REPORT 处理。

## 11. Very dim nodes?

- source_id: `KDISC_737896`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737896
- 作者/角色: weke / Participant
- 访问时间: 2026-09-03T08:25:39.571Z UTC；2026-09-03T16:25:39.571000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 3/3；Host 回复: false
- 页面字节/SHA-256: 2284 / `f714febf4ed92723210a06a4a2a4968c98bce6d114b2f41c38d557a606013f21`
- 摘要: 作者给出具体训练样本节点并询问极暗节点是否伪影；回复提出插值或假阳性可能，无官方确认，结论 UNKNOWN。

## 12. Public Notebook Rankings Need a Metric Refresh

- source_id: `KDISC_736937`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/736937
- 作者/角色: Yunus Gümüşsoy / Participant
- 访问时间: 2026-09-03T08:18:36.081Z UTC；2026-09-03T16:18:36.081000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: false
- 页面字节/SHA-256: 2389 / `33861403c105fb0ad8e5a7b73b03fd01f9fe3f5c0e316851958cd571f69ba309`
- 摘要: 参赛者报告 leaderboard 已按修复后 metric 重算，但部分公开 Notebook 页面仍展示补丁前膨胀分数，导致 Highest Score 排序失真；没有主办方回复，因此属于 COMMUNITY_REPORT，但与当前 Notebook 页面分数高于 Leaderboard 顶分的观察一致。

## 13. Scoring after notebook ran

- source_id: `KDISC_737659`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737659
- 作者/角色: Alex Amirkhanyan / Participant
- 访问时间: 2026-09-03T08:25:42.316Z UTC；2026-09-03T16:25:42.316000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 5/5；Host 回复: false
- 页面字节/SHA-256: 2285 / `34fc57e78af4ce20e9dbed3c5de403913fd0299f32061bf217b5620fcf1cbee7`
- 摘要: 多名参赛者报告submission scoring耗时6至11小时；没有可绑定提交记录或平台说明，属于 COMMUNITY_REPORT，不可推广为服务SLA。

## 14. division jaccard

- source_id: `KDISC_737577`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737577
- 作者/角色: nusrati / Participant
- 访问时间: 2026-09-03T08:18:57.287Z UTC；2026-09-03T16:18:57.287000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 2/2；Host 回复: false
- 页面字节/SHA-256: 2954 / `860f903db2e1270874d44cbcb8c0b6d097d645addfa08bc94d66796a23fd1007`
- 摘要: 作者报告其 ILP 在多组权重下 Division Jaccard 近零，真实 division 被大量假阳性淹没；作者随后明确该帖讨论从零训练模型，不能用其当前页面分数解释此实验。没有官方回复，属于 AUTHOR_CLAIM。

## 15. Is public Zebrahub data allowed as external training data?

- source_id: `KDISC_734330`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/734330
- 作者/角色: marumarukun / Participant
- 访问时间: 2026-09-03T08:22:13.900Z UTC；2026-09-03T16:22:13.900000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 3/3；Host 回复: true
- 页面字节/SHA-256: 2451 / `19920f974741b52faab32f7b25528795c12b82d440eedb96fbff8802892fd210`
- 摘要: Competition Host Thibgolds明确答复可使用Zebrahub数据和资源，并称与test set无重叠。该回复属于 HOST_CONFIRMED；仍需对具体资产逐项核对许可证与公开可得性。

## 16. Errors on GT cell traces

- source_id: `KDISC_732474`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/732474
- 作者/角色: Tim Krige / Participant
- 访问时间: 2026-09-03T08:23:09.119Z UTC；2026-09-03T16:23:09.119000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 2/2；Host 回复: false
- 页面字节/SHA-256: 4147 / `799f79e2b58caa89ce2f53b9bac537cdd75573c8cc5085250f2b4d0c521ab311`
- 摘要: 作者和评论者报告训练真值轨迹可能存在错误/自动跟踪偏差，但未给出可复核资产或官方回复；属于 COMMUNITY_REPORT，不能视为已证实数据缺陷。

## 17. A one-to-one linker scores 0.000 on divisions - four measurements on the metric itself

- source_id: `KDISC_733877`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/733877
- 作者/角色: Luka Duvanov / Participant
- 访问时间: 2026-09-03T08:17:58.580Z UTC；2026-09-03T16:17:58.580000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 0/0；Host 回复: false
- 页面字节/SHA-256: 3424 / `ac4ef494878567c2595ed9f39c791cf04d2f3622e56cd056625cdccb656625b3`
- 摘要: 作者声称用官方代码对手工图做四组隔离实验：一对一 linker 无分裂项、重复检测仅受节点数影响，并报告补丁 commit aa65e90 前后合成图差异；这些数值是 AUTHOR_CLAIM，需在固定 commit 源码或可复现实验中另证。

## 18. The voxels are 4:1 anisotropic in Z, and two other things sitting in zarr.json

- source_id: `KDISC_734053`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/734053
- 作者/角色: Maximo Lorenzo y Losada / Participant
- 访问时间: 2026-09-03T08:22:45.930Z UTC；2026-09-03T16:22:45.930000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 0/0；Host 回复: false
- 页面字节/SHA-256: 4002 / `699fe7e95fcc82e837d243a2314e2267d8e4a8a7d3dc7c99d1b06c70075cada4`
- 摘要: 作者从随附Zarr元数据说明物理尺度、强度分位数、time-major chunking及submission图结构。技术事实需与官方data/evaluation交叉核验；性能含义属于 INFERENCE。

## 19. The linking radius is 8.4 µm, and divisions are one link in 853

- source_id: `KDISC_733973`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/733973
- 作者/角色: Luka Duvanov / Participant
- 访问时间: 2026-09-03T08:22:04.313Z UTC；2026-09-03T16:22:04.313000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 0/0；Host 回复: false
- 页面字节/SHA-256: 2520 / `7a89883afdf54311f2563e57bdb0f026ff888247105bf4cc9edabaa1bb9568cd`
- 摘要: 作者声称基于199个训练 movie、128,883个真值 link 统计位移和division稀疏性，并建议按物理单位设链接半径、用Zarr元数据强度分位数归一化。数字是 AUTHOR_CLAIM，需以Notebook源码或独立复算验证。

## 20. GEFF node coordinates alignment with Zarr image volume

- source_id: `KDISC_733389`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/733389
- 作者/角色: Estee / Participant
- 访问时间: 2026-09-03T08:22:48.759Z UTC；2026-09-03T16:22:48.759000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: false
- 页面字节/SHA-256: 3438 / `48dac2abff1d98eaf8c19f0e8f2d2e36d49ee7aa3fb678e39a277b6170476cb2`
- 摘要: 作者提问GEFF坐标对齐；普通参赛者回复坐标可直接索引(t,z,y,x)且物理尺度仅用于距离。没有官方回复，故该解释为 COMMUNITY_REPORT。

## 21. Every submission except the unmodified sample_submission.csv gets "Submission Scoring Error" (7/7 reproducible)

- source_id: `KDISC_732674`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/732674
- 作者/角色: Krish Rakholiya / Participant
- 访问时间: 2026-09-03T08:25:45.150Z UTC；2026-09-03T16:25:45.150000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 3/3；Host 回复: false
- 页面字节/SHA-256: 6244 / `6e93512a0ebceb50a71d48d83b0d5417ba03e756f6cae9a67dd382c59540b1ae`
- 摘要: 作者报告7次诊断提交后又公开纠正初始结论，怀疑动态test样本名/时间范围等约束；普通回复指向getting-started Notebook。无官方确认，保留修订过程并归类 AUTHOR_CLAIM。

## 22. Does CV match LB in this competition?

- source_id: `KDISC_730160`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/730160
- 作者/角色: Chester Yuan / Participant
- 访问时间: 2026-09-03T08:25:47.852Z UTC；2026-09-03T16:25:47.852000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 5/5；Host 回复: false
- 页面字节/SHA-256: 4224 / `5f10c3258610a519043674b23b2018c632ca729df8204c4647ea030d9d0365e3`
- 摘要: 参赛者报告公开权重可能在全部199训练视频训练、训练内CV会泄漏，并建议leave-one-embryo-out；多组CV/LB数字均未绑定版本或submission，属于 COMMUNITY_REPORT。

## 23. beware of jumps in ground truth track

- source_id: `KDISC_724283`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/724283
- 作者/角色: hengck23 / Participant
- 访问时间: 2026-09-03T08:23:59.774Z UTC；2026-09-03T16:23:59.774000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 15/15；Host 回复: false
- 页面字节/SHA-256: 9640 / `dcdbdcff321151c58a0b45576aa6fd3fc8188b223dde9e1f5f3b2190b9eaafb0`
- 摘要: 作者及评论者报告6bba训练样本存在重复帧/跳帧，并给出199视频扫描的具体计数；全部为参赛者自述，未独立复算也无官方回复。页面标题计数为7个顶层评论，另展开8个嵌套回复，共实际加载15条。

## 24. Exact duplicate volumes, but GT edge moves 8.9 µm

- source_id: `KDISC_729082`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/729082
- 作者/角色: g john rao / Participant
- 访问时间: 2026-09-03T08:23:21.326Z UTC；2026-09-03T16:23:21.326000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: false
- 页面字节/SHA-256: 2509 / `0ce480676e9189153df0243d4bf29c09a102bf48df50d7c2b601ef050dd592a4`
- 摘要: 作者给出具体训练样本/帧和位移计算，报告连续volume字节相同而GT节点移动8.90µm；评论补充观察。未独立复算，属于 AUTHOR_CLAIM/COMMUNITY_REPORT。

## 25. not all sparse GT edge are correct

- source_id: `KDISC_729053`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/729053
- 作者/角色: hengck23 / Participant
- 访问时间: 2026-09-03T08:24:19.810Z UTC；2026-09-03T16:24:19.810000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 1/1；Host 回复: false
- 页面字节/SHA-256: 1872 / `ebd7418da05acef6598d799f2c225caedd8fa0a1bedd8887592f06c79c7cab5a`
- 摘要: 作者称发现低频GT edge错误，评论链接具体Notebook版本并给出另一种解释。没有官方确认或独立复算，属于 COMMUNITY_REPORT。

## 26. Post-patch: is the 0.91+ frontier separated by the edge term or by divisions?

- source_id: `KDISC_728551`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728551
- 作者/角色: Arul Prasad S P / Participant
- 访问时间: 2026-09-03T08:22:06.686Z UTC；2026-09-03T16:22:06.686000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 2/2；Host 回复: false
- 页面字节/SHA-256: 3525 / `890755fdcdc4794c460c99d0dd88e89ab1f48947b86994a83a122e9021b26e85`
- 摘要: 作者讨论补丁后edge/division项分离，并报告其HOCT合成球输入实验性能与耗时；评论仅含参赛者约0.2的模糊猜测。无官方回复，均为 COMMUNITY_REPORT/AUTHOR_CLAIM。

## 27. COMPLETED: Rescore Underway

- source_id: `KDISC_728324`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728324
- 作者/角色: inversion / Kaggle Staff
- 访问时间: 2026-09-03T08:16:59.208Z UTC；2026-09-03T16:16:59.208000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 4/4；Host 回复: false
- 页面字节/SHA-256: 2621 / `897c49cf04cd1e11c2a35297700bbf2538e0974d9856785612a0b2e77d0364f5`
- 摘要: Kaggle Staff 公告 metric 已补丁并启动全量重算，期间分数可能暂时消失，多数提交预计至少小幅下降；同一 staff 后续评论明确重算完成。参赛者要求刷新公开 Notebook 页面分数，未见此帖给出已刷新确认。

## 28. Division Metric exploit and patch.

- source_id: `KDISC_727154`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/727154
- 作者/角色: Thibgolds / Competition Host
- 访问时间: 2026-09-03T08:16:28.960Z UTC；2026-09-03T16:16:28.960000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 14/14；Host 回复: true
- 页面字节/SHA-256: 6890 / `e3dfc68db121abe2a14e2cae15f25481e28b460b386c0dad774261c08ba12a9a`
- 摘要: 主办方确认 Division Jaccard 存在 exploit，补丁已公开并将重算全部提交；非主动利用者预计不受影响。评论中主办方更新重算正在运行；参赛者对漏洞机制的解释仅属社区报告，需由代码另证。

## 29. Any update on the re-scoring timeline?

- source_id: `KDISC_727957`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/727957
- 作者/角色: Simon Rüba / Participant
- 访问时间: 2026-09-03T08:17:17.829Z UTC；2026-09-03T16:17:17.829000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 3/3；Host 回复: true
- 页面字节/SHA-256: 2688 / `6e28799ba1ca4a8d3ce02dbdaf489660f7e326ae61fb8f477d4c00e8bd24fdac`
- 摘要: 发帖者报告当时 Leaderboard 仍显示补丁前分数；Competition Host 回复重算正在进行并预计次日完成。最终完成状态应以 Kaggle Staff 的 728324 后续确认作为更强证据。

## 30. You can score on train locally, and why a clean prediction can go above 1.0

- source_id: `KDISC_728300`
- URL: https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728300
- 作者/角色: Busya Prime / Participant
- 访问时间: 2026-09-03T08:22:09.053Z UTC；2026-09-03T16:22:09.053000+08:00 Asia/Singapore
- 读取: FULL_THREAD_READ；评论 0/0；Host 回复: false
- 页面字节/SHA-256: 3291 / `8894750a9b1fe0429a70dab2446eb20aa3644b55b51aeb9525b70589b8f89d0f`
- 摘要: 作者解读官方开源评分器、说明adjusted edge项可能超过1并提供本地评分Notebook。公式可与官方源码交叉核验；关于运行秒级等属于 AUTHOR_CLAIM。
