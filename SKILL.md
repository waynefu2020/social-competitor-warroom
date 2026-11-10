---
name: social-competitor-warroom
description: >-
  社媒竞品作战室（全品类竞品策略拆解、真实用户吐槽深挖、3年持有总成本TCO精算、四大派别进攻话术与高颜值HTML报告生成）。
  当用户想要做「社媒竞品调研」「小红书/抖音竞品拆解」「新品上市竞品攻防话术」「扒竞品评论区真实差评/避坑帖」「完善竞品表格」或「把竞品资料生成高颜值网页报告」时立即激活本技能。
  支持任意用户零门槛使用：既可上传本地资料（Excel/CSV/Markdown/PDF/截图/口述），也可直连飞书文档（lark-cli）；采集优先用 TikHub API，无 Key 时自动无缝降级为「Agent 联网调研 + Agent Reach（xhs-cli / yt-dlp / Exa / Jina）」免费方案；内置 5 套 Dribbble 顶级视觉设计风格供用户自选或一键实时切换。
---

# 社媒竞品作战室 (Social Competitor Warroom)

将散乱的社媒竞品信息（小红书 / 抖音 / YouTube / TikTok / 电商详情页）转化为 **老板能直接拍板、运营能直接抄作业、客服能直接对线** 的实战作战系统。

与单纯统计 KOL 投放数量的脚本不同，本技能聚焦于 **「产品定位于代际差定义」+「已验证渠道打法复刻」+「3年真实持有总成本(TCO)算账」+「真实素人退货差评截流」**，并输出支持 **5 套 Dribbble 视觉风格一键切换** 的交互式单文件 HTML 报告。

---

## Step 0：立项与零门槛输入适配（不强制绑定飞书）

动手前，先识别用户手头有什么资料，自动匹配以下 **4 种输入模式**（用户已给清的不再重复追问）：

1. **模式 A · 本地文件 / 截图上传（最通用）**
   - 用户直接提供 `.xlsx`、`.csv`、`.md`、`.pdf`、`.html`、网页截图或聊天记录。
   - 直接读取并提取已有竞品列表、价格和卖点，缺项进入 Step 2 自动补齐。
2. **模式 B · 零资料纯口述（白手起家）**
   - 用户只给出我方产品（或品类名称）及 3~10 个竞品名字（若用户连竞品有哪些都不知道，先联网搜索该赛道 Top 8 代表性产品供用户确认）。
3. **模式 C · 飞书 / 云文档协同（可选进阶）**
   - 若用户提供了飞书 Wiki / Docx 链接且本地装有 `lark-cli`，使用 `lark-cli docs +fetch` 读取现有表格，并在分析完成后用 `lark-cli docs +update` 将补齐的策略、话术与带链接的用户吐槽回写到飞书文档（详见 [references/feishu-sync-guide.md](references/feishu-sync-guide.md)）。
4. **模式 D · 残缺表格补全**
   - 用户给了半成品表格（例如只有产品名、价格、卖点，缺“渠道打法”、“进攻话术”或“用户吐槽”），定向抓取缺失模块并补齐。

**立项必对齐的「我方底牌」（若用户未提供，简短问一句）：**
- 我方产品名称、首发价/日常价、会员/续费规则？
- 我方最核心的 **3 张王牌**（例如：独特功能、存量用户底座、资产归属、形态差异）？

---

## Step 1：双轨数据采集（TikHub 优先 ➡️ 免费「联网调研 + Agent Reach」无缝兜底）

每个竞品需采集两类核心数据：**① 官方与达人高赞种草打法**、**② 真实素人避坑/退货差评与评论区交锋**。

### 轨道 A：优先方案 —— TikHub API（批量结构化深抓）
先检查环境变量 `TIKHUB_API_KEY` 或 `~/.config/tikhub/key` 是否存在。若存在，优先使用 TikHub 接口采集：
- **小红书搜索**：`/api/v1/xiaohongshu/app_v2/search_notes` 或 `/api/v1/xiaohongshu/web/search_notes`
- **蒲公英商单识别**：检查底层 `order_cooperate` 标记及合作暗号，统计竞品报备商单数、千赞率与达人垂类分布（如科技数码 vs 职场 vs 细分人群）。
- **评论区楼中楼与视频逐字稿**：对高赞种草帖与高评避坑帖抓取评论区热评及回复，提取头部测评视频 ASR 逐字稿。

### 轨道 B：免费方案 —— Agent 联网调研 + [Agent Reach](https://github.com/Panniantong/Agent-Reach) 技能组合拳（零成本通用）
若用户没有 TikHub Key（或余额不足），**绝对不要卡住报错**，立即提示用户并切换至免费组合方案（详细安装与调用指南见 [references/data-collection-playbook.md](references/data-collection-playbook.md)）：

1. **检查或一键安装 [Agent Reach](https://github.com/Panniantong/Agent-Reach)（开源互联网感知工具箱）**：
   - 先运行 `agent-reach version` 检查是否已安装。
   - **若用户电脑尚未安装 Agent Reach**：可主动帮用户通过官方最新安装流一键安装（⚠️ 切勿从 PyPI 安装同名包，必须用官方 GitHub Release）：
     ```bash
     uv tool install https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip
     agent-reach setup
     agent-reach add xiaohongshu   # 开启小红书渠道（搜笔记、读正文、看评论）
     ```
   - **调用 `agent-reach` 技能抓取社媒数据**：
     - **小红书 (`xiaohongshu` / `xhs-cli`)**：搜笔记、读正文、看评论（获取带 `xsec_token` 的真实结果与评论区吐槽）。
     - **B站 (`bilibili`) & YouTube (`youtube`)**：免登录直接搜索视频、获取长测评信息与字幕。
     - **Reddit (`reddit`) / Twitter (`twitter`) / V2EX (`v2ex`) / 网页阅读 (`web`)**：跨平台搜集海外与极客社区真实口碑。
2. **调用 Agent 内置 `search_web` 精准语法深挖**：
   - **查价格与隐形续费**：搜 `"品牌名" 价格 会员 续费 免费时长 额度`
   - **查种草打法与 PR 动作**：搜 `"品牌名" 发布会 OR 联名 OR 直播间 OR 销量`
   - **查真实素人差评（必搜负向词）**：搜 `site:xiaohongshu.com "品牌名" (避雷 OR 退货 OR 别买 OR 缺点 OR 实话实说 OR 闲置 OR 智商税)` 以及 `site:post.smzdm.com "品牌名" 缺点`

---

## Step 2：防幻觉事实核查与水军清洗（老板级交付铁律）

在整理竞品档案与用户吐槽时，必须遵守以下 **3 条死规矩**（详见 [references/data-collection-playbook.md](references/data-collection-playbook.md)）：

1. **严禁张冠李戴（区分「竞品真话术」与「我方推演话术」）**：
   - 竞品的 `进攻话术` 一栏，只能写**竞品官方详情页、发布会或合作达人实际说过的原话**。
   - 我方针对竞品软肋推演出的攻击角度（如“钉钉飞书离职带不走”），只能放在 **我方的「差异化进攻话术」** 中，绝不能塞进竞品自己的宣传栏里。
2. **每一条用户吐槽必须 100% 挂真实原帖直达链接**：
   - 凡是写进报告的素人避坑帖、退货帖、高管对线帖、野生自来水帖，必须保留 **`@博主昵称` + `《原帖标题》` + `互动数据（赞/评）` + `可点击跳转的原帖 URL（小红书需保留 xsec_token 防 404）`**。没有真实出处链接的槽点一律剔除。
3. **水军与铺量 KOC 剔除**：
   - 剔除粉丝 `<500` 且零评论的公关通稿号、剔除只背诵详情页参数不提任何缺点的铺量帖；优先采信**自费多机横评帖、带退货截图的避坑帖、推广博主开小号讲真话帖、以及评论区 ≥20 条真实追问的帖子**。

---

## Step 3：四大核心战略模块提炼

不要只罗列枯燥的信息表，必须将采集到的数据提炼为以下 **4 个高管决策模块**：

### 模块 1：我方三张王牌 & 一句话代际定义
- **一句话代际定义（Thesis）**：用一句话把赛道内所有竞品定义为“上一代”（例如：*“上一代录音卡，有 Agent，没记性；而 XX 是唯一拥有个人长期记忆、能直接调用 Agent 替你干活的新一代产品”*）。
- **三张核心王牌（Core Pillars）**：提炼 3 个最具排他性的卖点，每个卖点标明 **「精准击穿哪些竞品的什么死穴」**。

### 模块 2：四大派别逐个击破（Battlecards 攻防话术）
将 8~10 款竞品按商业逻辑归类为 **3~4 个典型派别**（例如：`A. 企业办公绑定派`、`B. 高价硬件+天价年费派`、`C. 半成品软件&静态派`、`D. 全天候穿戴&删原音派`）。
每个派别输出：
- **代表竞品** + **核心软肋标签**
- **一句话一击必杀金句**（可直接印上海报、放进详情页首屏或给客服当标准话术）

### 模块 3：5 套已验证的社媒渠道打法（Data-Backed Playbook）
从竞品真实爆款中拆出 **5 套已被市场验证跑通的打法**，每套严格按三栏结构输出：
1. **打法名称**（如：*避开红海场景抢占高溢价细分人群* / *头部大V造词 + 15s切片投流 + 20单腰部带词根截流* / *用私域升级包激活百万存量老用户* / *3年总账单打爆订阅焦虑* / *避坑帖评论区招募“退货党体验官”截流*）
2. **竞品真实数据支撑**（带超大高亮数字，如 `55 单商单`、`13.7万 赞`、`307 条评论`）
3. **我方可直接落地的执行动作（3条 Bullet）**

### 模块 4：价格格局与「3 年真实持有总成本 (TCO)」精算表
- **首日买断价 vs 长期隐形订阅税**：算清 **3 年（或 1 年）真实持有总成本 = 硬件/首购价 + 赠送期满后的订阅/耗材续费**。
- **战略分流结论**：明确指出对哪些竞品**直接拿价格/TCO 当强杀伤武器**（如高年费海外品牌），对哪些免费基础款竞品**不拼价格、重点打高阶功能代际差**。

---

## Step 4：5 套 Dribbble 视觉风格预览与 5 选 1 生成 HTML 报告

本技能内置了从 Dribbble 热门趋势提炼的 **5 套高阶视觉设计系统**（详见 [references/dribbble-5-styles.md](references/dribbble-5-styles.md)、预览画廊 [resources/dribbble-style-picker.html](resources/dribbble-style-picker.html) 与标杆实现 [resources/editorial-report-reference.html](resources/editorial-report-reference.html)）：

| 风格代码 | 风格名称 | Dribbble 视觉基因 & 适用场景 |
| :--- | :--- | :--- |
| `editorial` *(默认推荐)* | **① 暖纸社论杂志风**<br>*(Kinfolk / Monocle Editorial)* | 米白暖纸底 `#F4F1EA` + 炭黑墨色 + 爱马仕橙 `#C2410C` + 橄榄绿 `#4D5B2F`，思源宋体大标题 + `Instrument Serif` 巨型数字。**适合：给老板/投资人深度阅读、品牌战略复盘** |
| `bento-dark` | **② 暗黑流光便当盒风**<br>*(Linear / Raycast Dark Bento)* | 曜石黑 `#090B10` + 1px 微光渐变玻璃边框 + 靛蓝/翠绿霓虹高亮，非对称 Bento Grid 卡片。**适合：AI 产品、智能硬件、SaaS 极客路演投屏** |
| `mckinsey` | **③ 麦肯锡高管作战看板**<br>*(Pitch / Stripe Executive)* | 纯净白灰底 + 深海蓝 `#0B1F3A` + 皇家蓝 `#1F5FBF` + 信号灯徽章，严谨商务表格与高密度对比。**适合：正式立项汇报、B2B 尽调、大厂述职** |
| `swiss` | **④ 瑞士国际主义网格风**<br>*(Readymag / Pentagram Brutalist)* | 建筑感 `2px solid #111` 粗黑分割线 + 暖灰底 + 瑞士高饱和红 `#E3261C` + 直角硬朗排版。**适合：设计驱动型品牌、潮流数码、独立开发者** |
| `xhs-craft` | **⑤ 小红书原生手账拆解风**<br>*(XHS Viral Note Craft)* | 米黄方格纸纹理 `#FFFDF6` + 荧光笔半截涂抹高亮（黄/绿/粉）+ 胶带便利贴卡片。**适合：社媒运营脑暴、生活方式品类、直接截图发小红书干货贴** |

### 风格选择与交付流程（先展示 5 张风格预览图，让用户 5 选 1）：
1. **生成前向用户逐一展示 5 张风格预览效果图**：在生成最终 HTML 报告前，**必须在回复中直接嵌入展示 `resources/previews/` 下的 5 张高清风格预览图**（或引导用户打开 [resources/dribbble-style-picker.html](resources/dribbble-style-picker.html) 预览画廊），并配合 `ask_question` 工具让用户从 5 种风格中点选 1 种：
   - `① 暖纸社论杂志风 (editorial)`：预览图 `resources/previews/01-editorial.png`
   - `② 暗黑流光便当盒风 (bento-dark)`：预览图 `resources/previews/02-bento-dark.png`
   - `③ 麦肯锡高管作战看板 (mckinsey)`：预览图 `resources/previews/03-mckinsey.png`
   - `④ 瑞士国际主义网格风 (swiss)`：预览图 `resources/previews/04-swiss.png`
   - `⑤ 小红书原生手账拆解风 (xhs-craft)`：预览图 `resources/previews/05-xhs-craft.png`
2. **纯粹单风格精修输出**：根据用户选定的那 **1 种** 风格，读取 [references/dribbble-5-styles.md](references/dribbble-5-styles.md) 对应的 CSS 设计 Token 与排版细节（若选 `editorial` 直接参照 [resources/editorial-report-reference.html](resources/editorial-report-reference.html)），生成干净、零冗余的单文件 HTML 报告。

---

## Step 5：交付前自检清单（Verification）

输出最终 HTML 报告（及飞书同步）前，逐项核对：
- [ ] **7 大标准章节是否齐全**：`Hero（含核心指标卡）` ➡️ `★ 三张王牌` ➡️ `01 四大派别进攻话术` ➡️ `02 5大社媒渠道打法` ➡️ `03 价格与3年TCO总成本表` ➡️ `04 竞品档案（支持分类筛选与折叠详情）` ➡️ `05 按产品形态拆解的真实用户吐槽 vs 破局打法（含可点击原帖胶囊）` ➡️ `06 野生自来水实证与高意向截流靶标`。
- [ ] **原帖链接抽查**：所有种草案例与素人吐槽是否都挂上了真实可点开的超链接？
- [ ] **事实口径抽查**：是否有把“我方推演话术”误写成“竞品官方宣传话术”？数字前后的口径（如月费、赠送时长、3年总和）是否算对？
