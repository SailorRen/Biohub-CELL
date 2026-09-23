# Codex：准备一个队友可复制的 B Notebook

任务ID：BIOHUB\_B\_TEAM\_COPY\_PREP\_20260923\_V01
仓库：SailorRen/Biohub-CELL
分支：codex/two-wave-four-submit-20260922
交接基点：b00be3c7377876a8116ffc6b04eba6cb29c370f0
沿用目录：experiments/BIOHUB\_TWO\_WAVE\_20260922\_V01

## 一、目标和授权

实际整理现有B为私有复制母版，处理现有队友的必要查看权限，交付一个Kaggle固定版本链接。队友没有Codex，不让他处理GitHub、命令行、哈希或重新搭建五项输入。

本轮只准备和共享：不运行模型、不正式提交、不进入队友账号。仍用冻结B，不修改已取得0.950的A，也不把A混入B。

母版不需要submission.csv或生产Output。零额度下不能保留GPU标签，可以将母版设为None，让队友复制后在自己的副本中选择T4×2。不要再把“GPU＋磁盘输出同时保存”作为交接门槛。

## 二、先同步，再操作平台

安全同步原分支，确认包含交接基点；有新交付先读并排重，不覆盖本地改动、不强推、不合并main。

将本正文保存为：
tasks/CODEX\_20260923\_BIOHUB\_B\_TEAM\_COPY\_PREP\_V01.md
先推送并回读，再操作Kaggle。

只读AGENTS.md、最新报告B停点、原platform\_ledger.json、B/candidate.ipynb、B/kernel-metadata.json及必要输入回执，不重新调查GPU政策或审计全仓库。

现有B：sailorren/biohub-d960-l030p-20260922，Kernel135375343。
冻结B/candidate.ipynb SHA256：
03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb

## 三、优先复用，只在必要时保存一次

先核查已有V1/SV351871500的全部14代码单元、固定输入及设置。能作为共享复制母版就直接复用，不为改标题额外保存。不把V2/SV351886222文本探针作为交接入口。

已有版本不适合时，在同一个B上恢复冻结源码，最多Quick Save一次：

- 原14代码单元的类型、顺序、源码不变；不改模型、阈值、精度、batch或选择器。
- 可加一个简短Markdown说明：“B／未跑分／复制到本人账号／运行需T4×2／不要直接提交母版”。新增说明单列差异，不声称整个ipynb哈希仍未变化。
- 保持Private、Internet off，优先原环境；实际镜像不同则如实记录待运行验证，不在本轮安装或重建环境。
- 全程会话off；GPU可静态保留就保留，要求启动GPU则取消启动，在off状态选择None后准备非运行保存。
- 只选Quick Save，不执行单元、不保存探针输出、不生成CSV、不打开CPU文件会话。

固定输入，逐项核对实际版本，不用同名最新版：

1. 比赛：biohub-cell-tracking-during-development。
2. primary／离线依赖：pilkwang/biohub-tracking-support-pack-50ep-v1/10。
3. secondary：pilkwang/biohub-temporal-unet3d-seed314159-v1/2。
4. DeepCenter：pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5。
5. gate：sailorren/biohub-division-train-20260914/1，历史SV349707105。

从最终实际版本导出复核源码、Inputs和设置，不能拿草稿代替保存版本。交付明确指向该Version/SV的查看链接，不是默认探针V2或仅自己可看的编辑页；不得猜测新版本号。

## 四、共享给现有队友

从当前比赛团队页确认现有队友及准确Kaggle用户名。历史显示名Dongdongjiaqi仅作为线索，不直接当账号slug使用。

确认唯一对应的真实队友后，授权：

- B保持Private，给该队友Can view；已有权限不重复添加。
- 核查gate来源Notebook的权限，必要时在用户拥有的该Notebook上也加Can view；不改其代码、权重或版本。
- 其他输入分别检查公开性／权限。私有Dataset权限单独处理；只共享用户拥有、且本任务必需的对象。无权共享的第三方输入列明缺口，不删除、替换或公开。

只向该名已核实队友开放所需资料，不给编辑权限、不设Public、不扩大到整个仓库，不索取账号密码或Token、不登录队友账号。平台正常共享通知允许随共享产生，不另发邮件。

用户名无法唯一核实时，先完成母版与链接，仅把共享标记为等待确认身份，不扩大授权。当前账号看到权限已设置，不等于队友已打开或能挂载输入；队友视角必须保留待验证。

## 五、上限与交付

本轮新Kaggle Notebook为0；新增非运行Quick Save最多1次，复用已有版本则0次。CPU／GPU／Colab会话、推理、训练、正式提交、Dataset创建、购买、取消旧作业及最终选择修改全部0。

这是母版整理与必要共享授权，不恢复旧B的正式提交许可。历史计数及不明请求保留；保存拒绝／响应不明也计数，只读对账，不换入口重发。

沿用原报告与账本，保存B/team\_copy\_handoff.json，记录真实链接／Version／SV、源码核验、输入、保存配置、共享对象与权限、队友侧待验证项。小文件推送原分支并固定commit回读，数据／模型／CSV／凭据不入GitHub。

最终回复先给可转发的真实Kaggle固定版本链接，再给队友最多四步中文说明：

1. 用本人账号打开，确认同队，点击Copy & Edit。
2. 确认副本归本人并保持私有，选择T4×2、Internet关闭，检查自己的GPU余额。
3. 把副本链接和Input／Settings截图发回用户，先不运行，由用户这边复核。
4. 后续经用户协调后才运行一次并提交；报错只发截图，不改代码。

分开报告母版是否准备、共享是否设置、队友侧是否验证。无队友回执写TEMPLATE\_PREPARED\_TEAMMATE\_CHECK\_PENDING；身份缺口写SHARING\_PENDING\_IDENTITY。不得宣称已跨账号复制、已跑通或已提交。
