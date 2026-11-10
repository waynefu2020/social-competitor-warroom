# ⚔️ Social Competitor Warroom（社媒竞品作战室）

> **把零散的竞品信息，一键炼成「给老板 / 投资人汇报级」的社媒竞品攻防作战室与交互式高颜值 HTML 研报。**  
> Compatible with **Claude Code · Google Antigravity · Cursor · Windsurf · Codex · OpenClaw**

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent_Skill-SKILL.md-141311.svg)](SKILL.md)
[![Data Engine](https://img.shields.io/badge/Data-TikHub_%2B_Agent--Reach-2A5C43.svg)](https://github.com/Panniantong/Agent-Reach)

---

## ✨ 为什么需要这个 Skill？

普通的 AI 竞品调研只会给你列出枯燥的「产品 A 卖点、产品 B 价格」罗列表格。而真正能帮新品打赢上市战役的**社媒竞品调研**，必须回答这 6 个致命问题：

1. **三张王牌（Core Pillars）**：在高度同质化的竞品卖点里，哪 3 个代际差能让我们一击必杀？
2. **四大派别进攻话术（4-Faction Battle Matrix）**：把市面上 5~15 款竞品归入 4 个流派，针对每一派的软肋给出一针见血的销售/种草反击金句。
3. **社媒爆款打法反推（5 Validated Playbooks）**：不止看竞品发了什么，更从蒲公英商单数、头部达人万赞爆款、投流切片词根、私域转化率中，拆出 5 套可直接抄作业的渠道打法。
4. **3 年真实持有总成本精算（3-Year TCO）**：撕开「硬件便宜、订阅割韭菜」的伪装，算清 **硬件首付 + 赠送额度 + 36 个月订阅续费** 的真实账单。
5. **真实素人退货/避坑深挖（Voice of Customer）**：严格过滤品牌公关软文，只抓自掏腰包的真实买家差评与高赞避坑帖，**每一条吐槽均附带可点击验真的原帖链接（含 `xsec_token`）**，绝不编造。
6. **野生自来水实证 & 评论区截流名单（Organic Proof）**：找出已经在用「友商产品 + 我们生态」组 CP 的野生用户，并列出最值得寄送测品的高意向退货党评论区名单。

---

## 🌟 四大核心特性

### 1. 零门槛多源输入（不强制绑定飞书）
- **本地文件 / 口述直传**：直接拖入 `Excel (.xlsx)`、`CSV`、`Markdown`、`PDF`、竞品详情页截图，甚至只口述一句「帮我调研 AI 录音卡赛道」。
- **飞书文档双向同步（可选）**：若团队使用飞书且安装了 `lark-cli`，支持直接读取飞书 Wiki/Docx 竞品表，并将补齐的策略、话术与带真实链接的用户吐槽一键写回飞书文档。

### 2. 双轨制社媒数据采集（TikHub 优先 + 免费自动降级）
- **🚀 轨道 A（专业极速版 — TikHub API）**：推荐配置 `TIKHUB_API_KEY`，支持小红书/抖音/TikTok/B站高赞商单、素人避坑帖、评论区前排高赞吐槽及 `xsec_token` 直达链接的批量结构化拉取。
- **🌐 轨道 B（零成本免费版 — Agent 联网调研 + [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)）**：无 API Key 时自动无缝降级，调用 Agent 内置搜索与开源脚手架 `Agent-Reach`（集成 `xhs-cli`、`yt-dlp`、`Exa`、`Jina Reader`）完成交叉核验。

### 3. 铁律级事实核查（Anti-Hallucination）
- 严禁张冠李戴竞品 Slogan（例如把 A 品牌的宣传词安到 B 品牌头上）。
- 报告中引用的每一条素人避坑帖、高管对线帖、横评帖，**100% 附带真实可点击的原帖 URL**，老板/合伙人随时点击验真。

### 4. 内置 5 套 Dribbble 殿堂级视觉风格（先选 1 种再生成）
生成 HTML 报告前，Skill 会自动展示 5 套完全不同排版骨架与字体的视觉预览（可打开 [`resources/dribbble-style-picker.html`](resources/dribbble-style-picker.html) 实时交互预览），由你任选 1 种生成独立单文件 HTML：

| 编号 | 风格名称 | 视觉基因与排版骨架 | 最适合场景 |
| :--- | :--- | :--- | :--- |
| **01** | **Editorial 暖白社论风** *(默认推荐)* | *Monocle* / * Kinfolk* 杂志感 · 暖米纸底 `#F6F2EA` + 朱砂橙 `#D84A1B` + 衬线大标题 | 给老板 / 合伙人 / 投资人深度阅读、品牌战略复盘 |
| **02** | **Linear Dark 极客暗黑风** | Linear / Raycast 质感 · 深邃曜石黑 `#090A0F` + 电光紫蓝微光边框 + 赛博毛玻璃 | AI 硬件、SaaS、开发者工具、科技新品发布会作战室 |
| **03** | **Swiss Grid 瑞士国际主义网格** | 12 栏裸露黑色网格线 `1.5px solid #111` + 国际克莱因蓝 `#0038FF` + 巨型序号 | 投行级竞品拆解、硬核参数与 3 年 TCO 财务精算 |
| **04** | **Neo-Brutalism 新粗野主义波普** | Gumroad / Figma 潮流感 · 高饱和奶油黄 + 粗黑描边 `#000` + 硬朗偏移阴影 `5px 5px 0 #000` | 新消费品牌、Z 世代社媒种草策略、广告 Agency 比稿提案 |
| **05** | **Apple Bento 苹果发布会便当盒** | Apple Keynote 质感 · 苹果浅灰底 `#F5F5F7` + `28px` 超大圆角白卡 + 渐变大字报数字 | CEO 全员大会演示、产品经理评审会、大屏直接投屏汇报 |

---

## 📦 一键安装

### 方式一：使用 `npx skills` 安装（推荐）

```bash
npx skills add waynefu2020/social-competitor-warroom
```

### 方式二：Git Clone 到本地技能目录

**Claude Code（全局或项目级）：**
```bash
git clone https://github.com/waynefu2020/social-competitor-warroom.git ~/.claude/skills/social-competitor-warroom
```

**Google Antigravity / Cursor / OpenClaw（项目级 `.agents/skills`）：**
```bash
git clone https://github.com/waynefu2020/social-competitor-warroom.git .agents/skills/social-competitor-warroom
```

---

## 🔌 可选增强工具配置（按需安装）

本技能支持**零配置开箱即用**。如果你希望解锁更强的社媒原生抓取或飞书同步能力，可按需配置：

1. **免费社媒采集脚手架 [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)（强烈推荐）**
   > ⚠️ 注意：请勿直接从 PyPI `pip install agent-reach`（存在同名冲突包），请使用官方 GitHub Release 安装：
   ```bash
   uv tool install https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip
   agent-reach setup
   agent-reach add xiaohongshu   # 按提示扫码或导入小红书 Cookie
   agent-reach doctor            # 检查小红书/抖音/B站/Exa 通道状态
   ```
2. **TikHub API（可选，适合高频大批量采集）**
   ```bash
   export TIKHUB_API_KEY="your_tikhub_api_key"
   ```

---

## 🚀 快速开始（Prompt 示例）

安装完成后，在 Claude Code 或 Antigravity 中直接输入以下任意指令即可触发：

### 场景 1：上传本地 Excel / CSV / 笔记，生成高颜值竞品作战室网页
> 「这是我整理的競品资料 `@竞品调研表.xlsx` 和小红书笔记明细 `@小红书明细.csv`。请用 `social-competitor-warroom` 帮我深挖竞品的真实素人差评（带小红书链接）、精算 3 年持有总成本，并生成一份交互式 HTML 竞品调研报告。」

### 场景 2：零资料冷启动，让 Agent 自动联网深扒整个赛道
> 「我们准备做一款面向超级个体的 AI 硬件/工具，对标 Plaud、得到录音卡、钉钉 A1、安克录音豆。请启动 `social-competitor-warroom`，帮我采集小红书上的真实种草打法与高赞退货避坑帖，输出四大派别进攻话术和 HTML 报告。」

### 场景 3：读取并补齐飞书竞品文档 + 生成汇报网页
> 「帮我读取这篇飞书竞品文档 `https://xxx.feishu.cn/wiki/xxx`，补充底部的『用户吐槽分析』（要求每条吐槽都有小红书原帖可点击链接），同步更新回飞书文档，并生成一份 Editorial 暖白社论风的 HTML 网页报告给老板看。」

---

## 📂 仓库目录结构

```text
social-competitor-warroom/
├── SKILL.md                                 # 核心技能指令与 6 步标准化作业流（SOP）
├── references/
│   ├── data-collection-playbook.md          # 双轨采集手册（TikHub API + Panniantong/Agent-Reach）
│   ├── dribbble-5-styles.md                 # 5 套 Dribbble 视觉风格完整 CSS 变量与排版规范
│   └── feishu-sync-guide.md                 # 飞书文档（lark-cli）读取与带链接回写指南
├── resources/
│   ├── dribbble-style-picker.html           # 5 套 Dribbble 视觉风格实时交互预览画廊
│   └── editorial-report-reference.html      # 780+ 行完整单文件 HTML 标杆模板（已脱敏演示版）
├── README.md
└── LICENSE
```

---

## 📄 License

MIT License © 2026 [waynefu2020](https://github.com/waynefu2020)
