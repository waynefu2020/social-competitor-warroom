---
name: social-competitor-warroom
description: 社媒竞品作战室（海内外全平台 × 全品类竞品策略拆解、红人投放雷达、长视频口播植入/赞助短链深挖、真实用户吐槽验真、3年TCO/订阅成本精算、四大派别进攻话术与 5 套 Dribbble 视觉风格高颜值 HTML 报告生成）。当用户想要做「海内外社媒竞品调研」「小红书/抖音/B站/YouTube/TikTok/Instagram 竞品拆解」「SaaS/App/美妆/消费品/AI硬件新品上市攻防话术」「抓取竞品近半年/1年 YouTube 或社媒付费商单」「扒竞品评论区真实差评/避坑帖」「完善飞书/本地竞品表格」「某个人群该投哪类博主」或「把竞品资料生成高颜值网页报告」时立即激活本技能。融合了 competitor-kol-radar 全套脚本管线：支持本地文件或飞书文档（lark-cli）输入；采集优先用 TikHub API（配合 yt-dlp 补全缺失字段），无 Key 时自动无缝降级为「Agent 联网调研 + Agent-Reach」免费方案；内置 5 套 Dribbble 顶级视觉设计风格（先向用户展示 5 张预览图供 5 选 1，再生成报告）。
---

# ⚔️ 社媒竞品作战室（Social Competitor Warroom · 海内外全平台 × 全品类版）

本技能将零散的竞品信息转化为**可直接呈交 CEO / 合伙人 / 营销总监 / 投资人**的高密度竞品攻防策略报告与交互式单文件 HTML 网页。**不仅适用于智能硬件，同样深度适配 AI 软件/SaaS/App（如 Manus、Granola、Wispr Flow、Gamma）、美妆个护 D2C（如花知晓 Flower Knows）、教育科技与新消费品**，覆盖**海外（YouTube / TikTok / Instagram / Reddit / App Store）**与**国内（小红书 / 抖音 / B站）**双栖市场。

---

## 核心铁律（执行前必读）

1. **绝不捏造或张冠李戴竞品话术与差评**：
   - 引用某竞品的官方宣传词或商业成绩前，必须在原始数据中核实该品牌确实使用过该表述；我方推演出的攻击话术必须明确归入「我方策略 / 进攻话术」，严禁安到竞品头上充当事实。
   - **所有引用的用户吐槽、避坑帖、测评视频、红人商单，100% 必须附带真实可点击的原帖 URL**（小红书必须带 `xsec_token` 参数，YouTube 必须带 `watch?v=` 链接，抖音/TikTok/B站带原视频链接）。
2. **术语规范铁律（严禁使用“中插”）**：
   - 在中文报告、飞书文档与表格中，海外/国内视频中段的赞助广告统一规范表述为 **「口播植入」** 或 **「泛频道植入」**（与 **「垂直专场 / 专场测评」** 相对），**严禁使用中文里不存在的生造词“中插”**。
3. **分清商业属性层级，不在不同层级间硬比数据**：
   - 严格区分 **明确付费赞助 (`Paid`)**、**专属合作短链/兑换码 (`Custom Link/Code`)**、**PR 礼盒寄样 (`Gifted`)**、**分佣联盟/底栏常驻工具单 (`Affiliate / Footer Tool List`)** 与 **纯自然内容 (`Organic`)**。算商单播放中位数时，必须剔除官方号、同名噪音（`noise_regex`）、声明了 `not sponsored` 的独立评测、普通用户拉新码（如 `manus.im/invitation`）以及底栏常驻联盟链接。
4. **飞书非必选，零门槛输入**：
   - 用户**不需要**有飞书。优先支持直接读取用户上传的本地文件（Excel / CSV / Markdown / PDF / 截图 / 口述产品定位）。仅当用户主动给出飞书链接时才调用 `lark-cli`。
5. **采集双轨制（TikHub API + `yt-dlp` 混合补全优先 ➡️ 免费降级 `Agent 联网 + Panniantong/Agent-Reach`）**：
   - 优先使用内置脚本（`scripts/`）调用 **TikHub API** 抓取精确结构化数据；当 YouTube 接口偶发缺失发布日期或播放量时，自动用 `yt-dlp` 并发补齐。若无 TikHub Key，自动无缝切换至 **Agent 联网搜索 + [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)** 免费采集。
6. **视觉风格先展示 5 张预览图，让用户 5 选 1**：
   - 生成最终 HTML 报告前，先向用户展示 `resources/previews/` 下的 **5 张 Dribbble 风格预览大图**，让用户选定 **1 种**后再输出。

---

## Step 0：明确市场、品类与对标竞品选品

若用户尚未指定竞品名单，或我方产品是复合型创新产品（市面上无 100% 同构竞品），按以下两种方法快速帮用户锁定 3~6 个标杆竞品（详见 [references/methodology.md](references/methodology.md) 与 [references/overseas-and-cross-category-playbook.md](references/overseas-and-cross-category-playbook.md)）：

1. **核心能力双轴象限选品法（适合 AI 软件 / 创新硬件 / 复合工具）**：
   - 将我方核心价值拆成两条能力轴（例如 X 轴 = `极低摩擦捕捉 + 上下文记忆（帮你记）`，Y 轴 = `Agent 端到端交付成品（帮你做）`），分别找出海外与国内在各条轴上最能打的代表产品（例如海外选 `Granola + Manus + Wispr Flow + Plaud + Genspark + Gamma`；国内 B站/小红书选 `AutoGLM + Kimi/秘塔 + 通义听悟/飞书妙记 + Flomo/Get笔记`）。
2. **三梯度选品法（适合消费品 / 美妆 / 垂直 App）**：
   - ① **体量/阶段相近**（看 Google Trends 起量时间） + ② **同品类内容最能打的**（学爆款模板） + ③ **品类天花板头部**。

---

## Step 1：多源资料读取与双轨数据采集（海内外全平台）

详细脚本调用与 API 参数见 [references/data-collection-playbook.md](references/data-collection-playbook.md)、[references/overseas-and-cross-category-playbook.md](references/overseas-and-cross-category-playbook.md) 及内置脚本目录 `scripts/`：

### 轨道 A：TikHub API + `yt-dlp` 极速结构化管线（推荐，单次调研约 $0.3~$1）
本技能在 `scripts/` 下内置了完整的可执行采集与分析管线（设好环境变量 `TIKHUB_API_KEY` 或写入 `~/.config/tikhub/key` 即可运行）：

1. **海外长视频（YouTube 6个月~1年赞助商单深挖）—— 两轮赞助指纹检索法**：
   - **第一轮**：搜品牌词与评测词，从初筛视频的描述栏（Description）中**逆向提取该品牌专用的商单追踪短链与兑换码格式**（例如 `go.granola.ai/...`、`granola.ai/?via=`、`manus.im/redeem?c=`、`ref.wisprflow.ai/...`、`gamma.yt.link/...`），并结合公开赞助索引页（如 `SponsorRadar`、`MeetSponsors`）补充纯口播植入视频线索。
   - **第二轮**：运行 `scripts/yt_sponsor_radar.py`，对专属短链与 `"sponsored by <brand>"` 进行深度翻页检索，拉取完整详情，并用 `--enrich-missing` 自动调 `yt-dlp` 补齐缺失的发布日期与播放量，自动导出按播放量排序的付费商单 CSV 与统计 JSON。
2. **海外多平台雷达（TikTok + Instagram + YouTube + 评论区槽点）**：
   ```bash
   S=/Users/waynefu2024/Desktop/Marketing1/.agents/skills/social-competitor-warroom/scripts
   python3 -I $S/collect.py --brief brief.json --stage search --dry-run   # 预估调用次数与余额
   python3 -I $S/collect.py --brief brief.json --stage search
   python3 -I $S/normalize.py --brief brief.json
   python3 -I $S/collect.py --brief brief.json --stage details           # 补齐 YouTube 详情与 IG 粉丝数
   python3 -I $S/normalize.py --brief brief.json
   python3 -I $S/comments.py --brief brief.json                          # 抓取高赞评论并按「吐槽/问价/疑虑/认可」分类产出 评论摘录.md
   ```
3. **国内平台雷达（小红书蒲公英 + 抖音星图 + B站长视频）**：
   ```bash
   python3 -I $S/domestic.py --brief brief.json --stage search
   python3 -I $S/domestic.py --brief brief.json --stage details          # 识别小红书蒲公英商单与抖音 star_atlas_info 星图商单
   python3 -I $S/domestic.py --brief brief.json --stage import
   python3 -I $S/normalize.py --brief brief.json
   ```

### 轨道 B：零成本免费方案（Agent 联网调研 + `Panniantong/Agent-Reach`）
当用户未配置 `TIKHUB_API_KEY` 时，自动切换至 [references/fallback-agent-reach.md](references/fallback-agent-reach.md)：
- 使用 `scripts/agent_reach_import.py` 调用 `yt-dlp`（YouTube / TikTok / B站）与 `xhs-cli`（小红书，保留 `xsec_token`）拉取数据；
- 配合 Agent 内置联网搜索（`Exa` / `WebSearch`）与 `Jina Reader`（`https://r.jina.ai/<URL>`）深挖 Reddit (`r/...`)、Trustpilot、App Store / Google Play 1~3 星差评与官网定价页。

---

## Step 2：数据清洗、抽查与全品类核心拆解

运行或整理数据后，必须按 [references/pitfalls.md](references/pitfalls.md) 进行 **20 条样本抽查**，并完成两大核心拆解：

### 1. 红人营销与长视频/多平台投放 7 维深拆（适用于海内外红人方案 & 飞书 7 列表格）
针对每个竞品，精确提炼以下 **黄金 7 列结构**（可直接回写飞书表格或放入 HTML 报告竞品档案）：
1. **产品**：品牌名与核心版本动向（如新增 Notetaker、MCP 工作流、Gamma 5 等）。
2. **目标人群**：精准画像（如 Tech Founders、VC、独立开发者、ADHD、一二线大厂 PM 等）。
3. **核心卖点**：提炼最具差异化的 3~4 个钩子（如 `No annoying bots 无机器人闯入`、`端到端直接交付成品`、`买一送一无限权益`）。
4. **博主种草案例（精选 3 条最具代表性的真实视频/笔记）**：附带 **博主名、粉丝量、播放/互动量、可点击原视频链接、视频标题及使用的专属折扣码/短链**。
5. **博主画像**：统计近 N 个月捕获的 **合作频道数、核心商单条数、播放量中位数、粉丝量级分布**，以及**跨语区分布**（如英/日/韩/西/德语区占比）与**集中度警告 `⚠`**。
6. **内容主题分析（必拆 🟢 爆款内容 vs 🔴 效果差的内容）**：
   - **🟢 爆款内容（What Worked）**：如「非工具类高净值商业/理财播客、装修改造 Vlog 中的 30-60s 口播植入（20万~105万播放）」或「丢给 AI 一个真实完整项目从零做到上线的一镜到底专场（13万~188万播放）」。
   - **🔴 效果差的内容（What Flopped）**：如「小号批量拆分的“如何安装/如何导出/如何加饼图”机械式 SEO 操作教程（仅 10~180 播放）」或「纯薅羊毛白嫖积分教程」。
7. **渠道打法总结**：判定其打法画像（`买量重投型` / `破圈泛植入选品型` / `自来水裂变型` / `联盟铺量型`），提炼其追踪短链机制、试用/积分权益钩子与线上线下转化收口（官网 DTC、Amazon/Impact 联盟、TikTok Shop、Ulta/Best Buy/日本量贩店）。

### 2. 真实买家吐槽与退货死穴深挖（Voice of Customer）
按产品形态或品类子赛道分组，对比呈现：
- **用户集中吐槽点（5 大真实痛点）**：从评论区（`评论摘录.md`）、小红书避坑帖、Reddit、App Store 差评中提炼，绝不编造。
- **真实素人避坑原帖 & 评论区高赞交锋**：列出 `@作者（赞/评数据）：[《原帖标题》](真实URL)`。
- **我方破局与降维打击打法**：逐条给出我方如何解决该痛点，以及如何去高赞差评帖评论区精准截流。

---

## Step 3：提炼「高管作战室」四大战略决策模块

无论调研的是 AI 硬件、SaaS 软件还是美妆消费品，最终报告必须提炼出以下 **4 个高管决策模块**：

1. **我方三张王牌 & 一句话代际定义（Core Pillars & Thesis）**：
   - 用一句话将市面上所有竞品定义为“上一代”或“单点工具”，提炼我方 3 张最具排他性的王牌，并标明每张王牌 **「精准击穿哪些竞品的什么死穴」**。
2. **四大派别逐个击破（4-Faction Battlecards）**：
   - 将竞品按商业逻辑归为 3~4 个流派，针对每一派的软肋给出**一句话一击必杀金句**。
3. **5 套已验证的社媒渠道打法 & 预算配比建议（Validated Playbooks）**：
   - 给出明确的预算与内容配比建议（例如海外长视频：**60% 泛高净值频道 30-60s 口播植入破圈 + 40% “真项目一镜到底”垂直专场讲透深层闭环**），每套打法含：`打法名称` + `竞品真实数据支撑` + `我方 3 条落地动作`。
4. **价格格局与「真实持有总成本 (TCO) / 订阅经济模型」精算表**：
   - **智能硬件**：算清 `硬件首付 + 赠送额度 + 36个月订阅续费 = 3年总成本`。
   - **SaaS / App**：算清 `免费额度上限 + Pro/Max 年费 + Token/积分消耗 + 博主链接免费试用期钩子`。
   - **美妆 / 消费品 D2C**：算清 `主力单品价 vs 全套礼盒端盒价 (Full-Set Box) + 折扣码让利 + 零售渠道溢价`。

---

## Step 4：展示 5 张 Dribbble 风格预览图，让用户 5 选 1 生成 HTML 报告

本技能内置了 **5 套高阶 Dribbble 视觉设计系统**（详见 [references/dribbble-5-styles.md](references/dribbble-5-styles.md)、预览画廊 [resources/dribbble-style-picker.html](resources/dribbble-style-picker.html) 与标杆实现 [resources/editorial-report-reference.html](resources/editorial-report-reference.html)）：

### 风格选择与交付流程（先展示 5 张风格预览图，让用户 5 选 1）：
1. **生成前向用户逐一展示 5 张风格预览效果图**：在生成最终 HTML 报告前，**必须在回复中直接嵌入展示 `resources/previews/` 下的 5 张高清风格预览图**（或引导用户打开 [resources/dribbble-style-picker.html](resources/dribbble-style-picker.html) 预览画廊），并配合 `ask_question` 工具让用户从 5 种风格中点选 1 种：
   - `① 暖纸社论杂志风 (editorial)` *(默认推荐)*：预览图 `resources/previews/01-editorial.png` —— 适合给老板/投资人深度阅读、品牌战略复盘
   - `② 暗黑流光便当盒风 (bento-dark)`：预览图 `resources/previews/02-bento-dark.png` —— 适合 AI 产品、智能硬件、SaaS 极客路演投屏
   - `③ 麦肯锡高管作战看板 (mckinsey)`：预览图 `resources/previews/03-mckinsey.png` —— 适合正式立项汇报、B2B 尽调、大厂述职
   - `④ 瑞士国际主义网格风 (swiss)`：预览图 `resources/previews/04-swiss.png` —— 适合设计驱动型品牌、潮流数码、超级个体
   - `⑤ 小红书原生手账拆解风 (xhs-craft)`：预览图 `resources/previews/05-xhs-craft.png` —— 适合社媒运营脑暴、美妆/生活方式、直接截图发小红书
2. **纯粹单风格精修输出**：根据用户选定的那 **1 种** 风格，严格按照 [references/dribbble-5-styles.md](references/dribbble-5-styles.md) 的 CSS Token 与 7 大章节骨架生成单文件 HTML 报告（若用户同时提供了飞书文档，按 [references/feishu-sync-guide.md](references/feishu-sync-guide.md) 同步回写飞书文档并验证 `revision_id`）。

---

## Step 5：交付前自检清单（Verification）

- [ ] **原帖链接 100% 可点**：所有种草案例（如每个竞品精选的 3 条代表视频/笔记）与素人差评吐槽，是否都挂上了真实可点开的超链接？
- [ ] **术语与事实口径核查**：全文是否已彻底杜绝“中插”一词（统一用“口播植入 / 植入”）？是否有把“我方推演话术”误写成“竞品宣传话术”？是否剔除了 `not sponsored` 与底栏常驻工具单的污染？
- [ ] **集中度与样本量标注**：单一账号占比 >30% 或单一语种/国家占比 >60% 时，是否已标出 `⚠ 集中度提示`？

---

## 参考文件导航（References & Scripts）

| 路径 | 用途说明 |
| :--- | :--- |
| [references/overseas-and-cross-category-playbook.md](references/overseas-and-cross-category-playbook.md) | **海外竞品 & 全品类自适应手册**：SaaS/App/美妆/硬件四套拆解模板、YouTube 赞助指纹搜索法、爆款 vs 低效内容拆解法 |
| [references/data-collection-playbook.md](references/data-collection-playbook.md) | **双轨采集手册**：TikHub API 核心端点与 `Panniantong/Agent-Reach` 免费安装使用指南 |
| [references/methodology.md](references/methodology.md) | **口径与方法论**：5级内容分类、核心 KPI、打法画像四原型判定、统计置信度规则 |
| [references/pitfalls.md](references/pitfalls.md) | **实战防坑清单**：同名噪音、假商单、平台字段陷阱、跨合作层级误比等 25 个真实踩坑对策 |
| [references/platforms-overseas.md](references/platforms-overseas.md) / [platforms-domestic.md](references/platforms-domestic.md) | 海外（TikTok/IG/YouTube）与国内（小红书/抖音/B站）字段解析规范 |
| [references/channel-signals.md](references/channel-signals.md) / [audience-research.md](references/audience-research.md) | 销售转化渠道信号解读 & 多竞品合并的「新人群投放研究」方法 |
| [references/dribbble-5-styles.md](references/dribbble-5-styles.md) | 5 套 Dribbble 视觉风格完整 CSS 变量、排版规范与高清预览图 |
| [references/feishu-sync-guide.md](references/feishu-sync-guide.md) | 飞书文档（`lark-cli`）读取、Callout/表格组装与带链接回写指南 |
| `scripts/yt_sponsor_radar.py` | YouTube 6个月~1年赞助指纹深挖 + `yt-dlp` 自动补全 + 合作层级清洗脚本 |
| `scripts/collect.py` / `domestic.py` / `comments.py` / `normalize.py` / `analyze.py` | 融合自 `competitor-kol-radar` 的全平台自动化采集、清洗、评论槽点提取与分析脚本群 |
