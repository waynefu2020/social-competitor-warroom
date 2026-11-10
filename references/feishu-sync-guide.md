# 飞书云文档（lark-cli）可选同步指南

> **注意**：本指南仅在用户主动提供了飞书文档链接（`https://*.feishu.cn/wiki/...` 或 `docx/...`）且本地安装了 `lark-cli` 时使用。若用户没有飞书，直接跳过本步骤，读取用户上传的本地文件（Excel / CSV / Markdown / PDF / 截图）或口述需求即可。

---

## 一、 读取飞书竞品文档

1. **优先读取全文 Markdown 概览（省 Token）**：
   ```bash
   lark-cli docs +fetch --doc "<飞书文档URL>" --doc-format markdown
   ```
2. **定位需要修改的章节与 Block ID（写入前必做）**：
   ```bash
   # 先获取目标章节标题或表格的 block_id
   lark-cli docs +fetch --doc "<飞书文档URL>" --doc-format xml --detail with-ids
   # 或只读取特定章节
   lark-cli docs +fetch --doc "<飞书文档URL>" --scope section --start-block-id <标题block_id> --detail with-ids
   ```

---

## 二、 完善「用户吐槽分析」与「主要结论」的标准 DocxXML 模板

使用 `lark-cli docs +update` 更新飞书文档时，默认使用 `--doc-format xml`，并通过文件重定向传入内容：

```bash
lark-cli docs +update \
  --doc "<飞书文档URL>" \
  --command block_replace \
  --block-id <目标Block_ID> \
  --doc-format xml \
  --content - < update_payload.xml
```

### 标准「用户吐槽分析」DocxXML 结构规范：

1. **顶部核心洞察 Callout**：
   ```xml
   <callout emoji="💡" background-color="light-red" border-color="red">
     <p><b>核心洞察</b>：网红达人商单都在吹「表层卖点」，但真实自掏腰包的素人买家退货和骂街最狠的是<b>「痛点1」、「痛点2」、「痛点3」</b>。这正是 <b>我方产品</b> 降维收割的黄金机会。</p>
   </callout>
   ```
2. **按产品形态拆解的 4 列表格（必须带可点击的原帖 `<a>` 链接）**：
   - 列宽建议：`<colgroup><col width="110"/><col width="340"/><col width="340"/><col width="270"/></colgroup>`
   - 表头背景：`background-color="light-gray"`
   - 第 3 列（`真实素人避坑原帖 & 评论区高赞交锋`）中的每一个帖子标题，必须使用 `<a href="URL">《原帖标题》</a>` 嵌套在 `<li>` 中，注意 URL 中的 `&` 必须转义为 `&amp;`！
3. **野生自来水实证 & 高意向截流动作**：
   - 列出已自发将「竞品 + 我方产品」组合使用的野生笔记（附直达链接），以及可在评论区招募“退货党体验官”的高赞避坑帖链接。
