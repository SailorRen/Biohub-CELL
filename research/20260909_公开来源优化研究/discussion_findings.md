# 公开讨论阅读记录

本轮读取第一屏20个帖子条目并选择9帖获取正文；8帖的正文及当时全部可取得文字评论已读，1帖评论读取失败且未作为论据。未审读图片内测量，不声称读完讨论区。原文留在 ignored downloads；此处仅摘要、哈希与评论ID。

## [focus3d : one of the best 3d cell segmentation](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 32/32（含删除记录）；`AUTHOR_CLAIM`。

FOCUS分割生成密集标签，再蒸馏较快点检测器、校准质心偏移并学习多帧链接。作者的节点/边召回来自自述样本且排除分裂，不是独立正式收益。正文和全部返回文字评论已读；图片内结果未核验。

可作为中长期检测/时序路线；直接大模型推理已有超时的参与者反馈，需独立预算。

## [magic or overfitting?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/740145)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 3/3（含删除记录）；`AUTHOR_CLAIM`。

作者自述概率细化、候选排序和位置改善；评论提出高召回短名单上用更强上下文模型重排。无绑定正式分，图像测量未核验。

优先定位密集、微弱、快移细胞与短断轨的实际损失，不把作者自测当本项目收益。

## [Post-Processing Plateau?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/740103)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 0/0（含删除记录）；`AUTHOR_CLAIM`。

作者自述后处理停在0.942；无评论、无绑定submission。

只说明存在类似体验，不证明通用后处理上限。

## [Problems with edje connection](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739685)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 7/7（含删除记录）；`COMMUNITY_REPORT`。

参与者报告CV改善与LB变化不一致；评论3522082称运动链接CV各折约+.012而LB仅+.001。没有可复算材料或submission绑定。

按漏检、断轨长度、分裂和错连分层；帖子中的gap频率例子是假设，不是真实分布统计。

## [I measured my own division_jaccard (0.22). What's yours?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739516)

状态：`PARTIAL_NOT_USED`；评论记录 0/1（含删除记录）；`UNKNOWN`。

取得正文但根未将其纳入已读论据；评论读取SSL失败。

PARTIAL，不计阅读最低数，不引用其division数值。

## [How are your local CVs like? It feels like a huge gap, atleast for me.](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739352)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 6/6（含删除记录）；`COMMUNITY_REPORT`。

参与者报告本地CV与LB差异，建议拆开raw J、adjusted J、节点数、分裂和缺边。删除评论没有可读内容。

提示独立核验本地指标与误差分布；不能据此断言本项目过拟合或分布偏移。

## [can we turn auto research to auo data generator?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739731)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 7/7（含删除记录）；`COMMUNITY_REPORT`。

讨论合成细胞数据和成像模拟。一位参与者自述尝试两周合成数据未见清晰收益；另有Zebrahub、模型资源指路。

纯合成数据不是优先捷径；不采用帖子中隐藏测试适应或未经授权写操作。

## [Are all public notebooks overfit?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739278)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 1/1（含删除记录）；`UNKNOWN`。

正文提出公开Notebook是否过拟合，一条回复追问CV；没有提供验证数据。

不能把提问写成已证实过拟合。

## [Is public Zebrahub data allowed as external training data?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/734330)

状态：`FULL_AVAILABLE_TEXT_READ`；评论记录 3/3（含删除记录）；`HOST_CONFIRMED`。

主办方Thibgolds在comment3512606确认本赛允许Zebrahub数据及资源，并表示与测试无重叠；角色已由浏览器COMPETITION HOST徽标核验。

允许研究具体外部资产，但本轮未下载数据/权重；仍须核验所选版本谱系、许可和预处理。
