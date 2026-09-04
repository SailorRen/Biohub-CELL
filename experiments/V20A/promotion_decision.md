# V20A 晋升决策

## 决策

`BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`

没有 selected arm，selected radius 为 `null`，不晋升、不创建 Kaggle Notebook Version、不提交 competition submission。

## 硬门证据

Kaggle 只读 competition file listing 完整枚举了 24,886 条文件元数据。199 个 train stems 在文件结构上都有配对 `.zarr`、`.geff` 及 scorer 必需 metadata paths。按官方定义的 embryo ID（folder name 第一段）分组：

| embryo group | sample count |
|---|---:|
| `44b6` | 71 |
| `6bba` | 128 |
| **合计** | **199** |

有效 embryo groups 是 2，而冻结合同要求至少 3。所有 train stems 只出现上述两个 prefix，所以即使后续 payload-level 可读性核验排除了某些样本，group 数也只能减少，不会增加到 3。

## 未执行结果

| arm | parent radius | 状态 |
|---|---:|---|
| R70 | 7.0 µm | `NOT_RUN_HARD_GATE` |
| R80 | 8.0 µm | `NOT_RUN_HARD_GATE` |
| R90 | 9.0 µm | `NOT_RUN_HARD_GATE` |

R70 没有在本协议下复现；所有 fold/sample/prefix 指标、paired delta、cache 等价性、runtime/memory 与 topology/schema 指标都是 `NOT_RUN`。不用历史 V19C 四样本值冒充本次指标。

## 平台操作

- validation Notebook Version: 0
- production Notebook Version: 0
- SaveKernel: 0
- notebook run: 0
- formal competition submission: 0
- submission status poll: 0
- retry: 0
- submission ID: `null`
- Public Score: `null`
- 30-minute monitoring: `NOT_APPLICABLE_NO_SUBMISSION`

此决策不否定 parent radius 假设本身；它只表示在用户冻结的 embryo-disjoint 证据要求下，现有 competition train data 无法构成允许候选运行的验证协议。
