# 本轮证据入口

- `sources.json`：权威来源索引、准确版本、17单元阅读覆盖、时间与全部缺口。
- `sources/N01/source_cells.json`、`sources/N02/source_cells.json`：保留原始source字段和零基索引，删除输出/metadata；Apache-2.0许可随附。
- `dependencies/support_v10/`：13个原样脚本，全读4,090行；本轮与N02内嵌预期哈希逐一匹配。Dataset Data Card为CC0；来源说明保留复用和API失败边界。
- `讨论逐条阅读.json`：8主帖、37条唯一可见回复的顺序语义摘要；不再分发Unknown许可原文/图片。
- `准确分数核对.json`、`官方页面与排行榜.json`、`列表筛查.json`：分开保存卡片/准确版本/动态队伍榜及检索限制。
- `同家族静态差异.json`：只能证明文本相同/不同，不证明净性能收益。

研究仍为PARTIAL_RESEARCH_BLOCKED；文件完整性不代表科学复现。无训练、推理、平台写入或提交。第三方脚本仅作为研究资料，未执行。
