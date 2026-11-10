# 双轨数据采集与防幻觉事实核查手册

本手册规定了 `social-competitor-warroom` 技能在采集竞品社媒数据、扒取真实用户吐槽以及进行事实核查时的标准执行动作。

---

## 一、 采集源优先级路由（Prioritized Data Collection）

### 优先级 1：TikHub API（高速结构化全量采集）
当检测到环境变量 `TIKHUB_API_KEY` 或配置文件 `~/.config/tikhub/key` 存在时，优先推荐并使用 TikHub 接口：

1. **小红书关键词搜索（含蒲公英商单标记）**
   - 端点：`GET https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes` 或 `/api/v1/xiaohongshu/web/search_notes`
   - 必抓搜索词组合：
     - **品牌声量与爆款种草**：`"<品牌名>"`、`"<产品名> 测评"`
     - **真实素人避坑与差评**：`"<品牌名> 避雷"`、`"<品牌名> 退货"`、`"<品牌名> 缺点"`、`"<品牌名> 实话实说"`
   - **商单判定**：检查返回 JSON 中的 `order_cooperate` 字段（官方蒲公英报备标记），或正文中包含 `合作 / 体验官 / 品牌方送` 等信号。
   - **保留 `xsec_token`**：拼接小红书链接时，务必保留接口返回的 `xsec_token`（如 `https://www.xiaohongshu.com/explore/<note_id>?xsec_token=<token>&xsec_source=pc_search`），防止用户在网页端点开报 404。

2. **高赞避坑帖评论区深挖（楼中楼交锋）**
   - 对排名前 5 的素人避坑帖或自购横评帖，拉取前 2~3 页评论与楼中楼回复（重点捕捉：**其他买家的共鸣痛点、官方客服/高管下场回复、友商评论区截流话术、以及“求推荐替代品”的高意向买家**）。

---

### 优先级 2：免费方案 —— Agent 联网调研 + [Agent Reach](https://github.com/Panniantong/Agent-Reach) 技能（零门槛通用）
当用户未配置 TikHub API Key 时，**自动切换为「Agent 内置联网搜索 + [Agent Reach](https://github.com/Panniantong/Agent-Reach) 免费工具箱」**，无需用户花一分钱即可完成高质量调研：

#### 0. 检查或帮新用户一键安装 Agent Reach（v1.6+ 官方标准流）
如果其他用户下载了本 Skill 但电脑上还没装 `agent-reach`，Agent 可按 [官方安装指南](https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md) 自动为其检测并安装（⚠️ **严禁从 PyPI 安装同名包**，必须使用 GitHub Release URL）：

```bash
# 1. 检查是否已安装（v1.6+ 会输出 JSON）
agent-reach version

# 2. 若未安装：先确保有 uv，再安装官方最新包并初始化默认渠道（bilibili / youtube / v2ex / github / web）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip
agent-reach setup

# 3. 按需一键开启小红书、Reddit、Twitter、Instagram 等可选渠道
agent-reach add xiaohongshu
agent-reach add reddit
```

#### 1. 激活并调用 `agent-reach` 渠道工具链
运行 `agent-reach doctor` 或 `which xhs yt-dlp || true` 检查可用渠道：

- **小红书渠道 (`xiaohongshu` / `xhs-cli`)**：
  ```bash
  # 搜索种草爆款与真实差评（每次操作间隔 2-3 秒防验证码）
  xhs search "品牌名"
  xhs search "品牌名 避雷"
  xhs search "品牌名 缺点 退货"

  # 读取单篇笔记详情与评论（必须传入 search 结果中带 xsec_token 的 URL）
  xhs read "https://www.xiaohongshu.com/explore/..."
  xhs comments "https://www.xiaohongshu.com/explore/..."
  ```
  *(注：小红书渠道需登录态，若未登录先提示用户确认后运行 `xhs login`，或直接搭配下方搜索引擎语法)*

- **B站 (`bilibili`) & YouTube (`youtube`) 默认免登录渠道**：
  ```bash
  # 提取多机横评视频元数据与自动字幕
  yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --convert-subs vtt --skip-download -o "/tmp/%(id)s" "VIDEO_URL"
  ```

- **网页阅读与搜索 (`web` / Exa / Jina Reader `r.jina.ai`)**：
  ```bash
  # 用 Jina Reader 免费读取什么值得买/知乎/少数派/科技媒体深度长文
  curl -s "https://r.jina.ai/https://post.smzdm.com/p/xxxxxx/"
  ```

- **海外社区口碑（`reddit` / `twitter` / `instagram`）**：
  ```bash
  rdt search "Brand Name review" --limit 10
  twitter search "Brand Name" -n 10
  ```

#### 2. Agent 内置 `search_web` 高级搜索算子（零依赖保底）
即使本地未安装任何 CLI，使用内置 `search_web` 依次执行以下 4 组查询（每个竞品必跑）：
1. **查官方定价与续费深坑**：`"<品牌名>" 定价 会员 续费 免费额度 每月多少钱`
2. **查核心卖点与近期大动作**：`"<品牌名>" 发布会 核心卖点 联名 直播间 销量`
3. **查小红书/值得买真实差评**：`site:xiaohongshu.com "<品牌名>" (避雷 OR 退货 OR 别买 OR 缺点 OR 智商税)` 及 `site:post.smzdm.com "<品牌名>" 测评 缺点`
4. **查野生 CP（竞品 + 我方产品）**：`"<竞品名>" "<我方产品名>"`（寻找是否已有真实用户自发将竞品与我方产品组合使用）

---

## 二、 水军与低质铺量帖清洗规则（4 条量化标准）

在汇总社媒表现与用户口碑时，必须过滤掉公关水军噪音：
1. **粉丝与互动倒挂过滤**：粉丝 `<500` 却使用千篇一律的公关通稿话术（如“打工人邪修神器”“某品牌杀疯了”），且评论数 `≤2` 的帖子，一律剔除。
2. **低粉 KOC 铺量降权**：粉丝 `<2万` 且通篇背诵官方详情页参数（如“6麦8米拾音、120种语言”）而不提任何真实使用瑕疵的报备帖，仅计入“铺量声量”，不作为真实口碑依据。
3. **高可信度正面种草采信标准**：优先选取 **千赞以上破圈爆款**、**明确切中某一细分场景（如 ADHD / 一人公司 / 专家访谈 / 律所取证）** 的标杆贴。
4. **高可信度负面吐槽采信标准**：优先采信 **自掏腰包多机横评贴、带订单/退货截图的避坑帖、推广博主开小号讲真话帖、以及评论区 ≥20 条真实买家追问对线的帖子**。

---

## 三、 防幻觉与事实核查铁律（Fact-Check Guardrails）

为了确保报告拿给老板、投资人或全网读者看时 **100% 经得起推敲**，必须执行以下核查：

1. **「竞品自己的话术」vs「我方进攻它的话术」严禁混同**
   - ❌ **错误示范**：分析员觉得得到录音卡比钉钉A1好在“离职带得走”，就把“强调钉钉飞书离职带不走”写进得到的官方进攻话术里（实际上得到官方只宣传“调用12万电子书库让灵感发芽”）。
   - ✅ **正确做法**：
     - 在 `竞品档案 -> 他们的进攻话术` 中，**只写该竞品官方或合作达人真正讲过的卖点与对比角度**；
     - 在 `01 差异化点 -> 我方进攻话术` 中，写**我方如何用我方王牌击穿该竞品的软肋**。
2. **每一条用户吐槽必须绑定真实原帖链接**
   - 报告第 05 节（用户吐槽分析）与第 06 节（野生自来水实证）中列出的每一个案例，必须包含：`@博主名` + `《原帖标题》` + `真实原帖 URL`。
   - 若某条槽点只有传闻、找不到具体原帖或测评文章出处，宁可不写，绝不编造博主名字或链接。
3. **价格对比与性价比分析口径透明**
   - 对比各竞品日常售价、主流规格及会员/礼盒时，必须在表格注明计算与规格口径，对官方未公开细节的竞品明确标注“官方暂未披露细则”，绝不瞎猜数字。
