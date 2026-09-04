# V20A safe-div parent radius 调用链冻结说明

## 结论

`SOURCE_CODE_VERIFIED`：V19C 的 `BIOHUB_SAFE_DIV_MAX_UM` 在全部 10 个代码单元的抽取源中只出现于环境设置、运行期常量解析、配置显示、safe-division 候选距离判定与最终打印。唯一改变图行为的使用是 `add_safe_divisions_postlink` 中对候选第二个 daughter 的 parent-to-candidate 距离门：`parent_dist > SAFE_DIV_MAX_UM` 时跳过。

因此，从静态调用链看，parent radius 不参与 detection、双 seed 融合、edge scoring、ILP association 或 pre-division graph 构建；它只影响 safe-division 提案及之后的图、诊断与 scorer 输出。这是静态依赖结论，不是运行等价性证明。

## 证据位置（抽取源行号）

| 阶段 | 位置 | 行为 |
|---|---:|---|
| 预设 | 31 | 将 `BIOHUB_SAFE_DIV_MAX_UM` 设为 `7.0` |
| 解析 | 229 | 环境变量解析为 `SAFE_DIV_MAX_UM` |
| 配置显示 | 332 | 写入 `CONFIG_DISPLAY.safe_div_max_um` |
| safe-division | 2502–2508 | 遍历 unclaimed candidate，应用 parent radius gate |
| 运行摘要 | 3956–3959 | 打印 parent/sister/cap 值 |

源码身份：ScriptVersionId `346969653`，Notebook 容器 SHA-256 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`，12 个 cell 中 10 个代码 cell 全部 AST 通过。由于第三阶段 embryo-group 硬门已阻断，本任务没有实际构建或复用上游 cache，也没有做端到端等价性测试。

## 未执行的 cache 门

若未来在新合同中解决至少 3 个独立 embryo groups，可以考虑复用上游中间结果，但必须同时完成：

1. 上游 artifact 内容 SHA-256；
2. R70/R80/R90 引用同一 SHA；
3. 至少一个样本的 cache 复用与完整端到端重跑逐字段等价性核验；
4. 任一不一致即 fail closed，三个 arm 全部端到端重跑。
