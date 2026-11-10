# 国内平台：小红书、抖音

`domestic.py` 负责采集，产出的字段和海外对齐（platform, id, handle, followers, bio, likes, collects, comments, ts, text, url, paidflag, shop），写进 `raw/posts_extra.jsonl`，normalize.py 会把它合并进来。

brief 里加：

```json
"xhs_keywords": ["品牌名", "品牌名 产品名", "中文别名"],
"xhs_hot_pages": 3,
"xhs_pages": 2,
"douyin_keywords": ["品牌名", "产品名"],
"douyin_pages": 5
```

国内品牌名常要配中文的 `brand_regex` 和 `official_regex`。`official_regex` 要能匹配“官方”“旗舰店”“直播间”“专卖”这类昵称，也要能匹配创始人号。

## 小红书

- 搜索：`GET /api/v1/xiaohongshu/app_v2/search_notes`，参数 `keyword, page, sort_type(general|popularity_descending|time_descending…), note_type=不限, time_filter=半年内`。“最热”和“综合”两种排序都抓，再按时间窗过滤。
- 结果：`data.data.items[].note`，含 `id, title, desc, timestamp, liked_count, collected_count, comments_count, user.userid/nickname, widgets_context`。
- **商业标记**：`widgets_context` 是 JSON 字符串，其中 `order_cooperate: true` 表示蒲公英合作订单。实测我方 6 条被标记的笔记都是真实投放。
- 作者：`GET /api/v1/xiaohongshu/app_v2/get_user_info?user_id=`，取粉丝数和简介，**所有作者都抓**。
- 没有公开播放量。看赞、藏、评，工具和干货类内容加看收藏率（藏÷赞）。
- 蒲公英博主列表接口（`pgy_get_blogger_list`）实测拿不到结果。博主池规模和报价要请用户从蒲公英后台导出。

## 抖音

- 搜索：`POST /api/v1/douyin/search/fetch_video_search_v2`，body `keyword, cursor, sort_type(0 综合|1 最热), publish_time=180, filter_duration=0, content_type=0, search_id, backtrace`。翻页用返回里 `business_config.next_page` 的 cursor 和 search_id。
- 结果：`data.business_data[].data.aweme_info`，含作者粉丝数、简介（signature）、点赞、收藏、评论、分享。
- **商业标记**：`GET /api/v1/douyin/app/v3/fetch_one_video?aweme_id=`。详情里 `star_atlas_info.log_extra` 解析后 `is_star: true` 表示星图商单；带 `promotion_id` 表示挂车带货。实测我方 16 条私下合作视频没有一条被误标成星图。
- 不公开播放量，用点赞。
- 品牌号、门店号、直播间号、创始人号很多，要在 `official_regex` 里剔除。

## 国内投放信号

| 类型 | 信号 |
|---|---|
| 付费合作 | 小红书 `order_cooperate`（蒲公英）；抖音星图 `is_star`；文案“合作”“广告”“赞助” |
| 寄样 | “品牌寄送”“收到了”“体验装”；没报备的软广很多，单靠文案识别率低 |
| 带货 | 抖音 `promotion_id`（小黄车）；小红书商品卡/店铺；“评论区置顶链接” |
| 自然 | 以上都没有。私下合作识别不出来，所以这个占比是上限 |

## 国内渠道

天猫、京东、抖音电商、小红书店铺、拼多多、线下（屈臣氏、KKV、集合店）。规模数据看品牌财报、电商平台榜单、行业媒体（青眼、36氪、界面、晚点）。

## 内外对比模式

同一品牌两套口径分开统计，对比时只比**比例和结构**（自然占比、量级结构、选题卖点），不比绝对数，因为平台指标不同（国内没有播放量）。
