"""Pull comments under the competitor's top posts, to find what users praise, complain about and ask.

  --dry-run   print planned calls, estimated cost and balance
  default     fetch, then write raw/comments.jsonl and 评论摘录.md (grouped by signal, top-liked first)

Picks the top --commercial posts (by views, or likes where views are missing) of commercial content
and the top --organic posts of organic content on every platform. Read 评论摘录.md yourself and write
the weaknesses section of narrative.json from it; the signal tags only sort comments, they don't judge them.
"""
import argparse
import collections
import concurrent.futures as cf
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_brief, read_jsonl, write_jsonl  # noqa: E402
import tikhub  # noqa: E402

SIGNALS = {
    '吐槽/不满': r"expensive|overpriced|pricey|too much|subscription|monthly fee|paywall|scam|waste|useless|gimmick|doesn'?t work|not work|broke|broken|stopped working|"
               r"battery|bug|glitch|laggy|refund|return(ed)? it|disappoint|worse|privacy|creepy|illegal|consent|caro|estafa|no sirve|suscripci|"
               r"高い|微妙|サブスク|太贵|好贵|有点贵|贵了|价格.{0,2}贵|不值|订阅|会员费|收费|智商税|鸡肋|没用|不好用|难用|垃圾|退货|翻车|坏了|续航|卡顿|隐私|偷录|违法|割韭菜|硬广|又是广告",
    '购买意向/问价': r"where (can i|to) buy|link\??$|how much|price\?|does it work (with|on|in)|want (one|this|it)|need (this|one)|cuánto|dónde|link por favor|"
                 r"どこで|いくら|欲しい|多少钱|在哪买|求链接|链接|怎么买|想要|种草了|已下单|入了",
    '提问/疑虑': r"\?|？|does it|can it|is it|will it|how does|what about|compared to|vs\b|还是|能不能|可以.*吗|支持.*吗|和.*比|区别",
    '夸奖/认可': r"love|best|amazing|game ?changer|life ?saver|genius|so useful|obsessed|me encanta|increíble|最高|便利|好用|神器|太方便|救命|绝了|爱了|真香",
}
SIG = {k: re.compile(v, re.I) for k, v in SIGNALS.items()}
LIKE_PLATS = ('小红书', '抖音')


def metric(p):
    v = p.get('likes') if p['platform'] in LIKE_PLATS else p.get('views') or p.get('likes')
    return v if isinstance(v, (int, float)) else 0


def ig_code(p):
    m = re.search(r'/(?:p|reel)/([^/?#]+)', p.get('url') or '')
    return m.group(1) if m else p['id']


def checked_get(path, params):
    # Never turn a failed page into a successful empty comment cache.
    return tikhub.require_success(tikhub.get(path, params))


def read_comment_cache(path):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if isinstance(data, dict) and data.get('complete') is True:
        rows = data.get('comments')
    else:
        # Old empty lists could represent a swallowed API error: refetch them once.
        rows = data if isinstance(data, list) and data else None
    if not isinstance(rows, list) or any(not isinstance(r, list) or len(r) != 2 for r in rows):
        return None
    return rows


def fetch(p, pages):
    """Return [(text, likes)] for one post. Response shapes were checked against live TikHub calls."""
    out, cur, tok = [], 0, None
    for _ in range(pages):
        plat = p['platform']
        if plat == 'TikTok':
            d = checked_get('/api/v1/tiktok/app/v3/fetch_video_comments', dict(aweme_id=p['id'], cursor=cur, count=20)).get('data') or {}
            out += [(c.get('text'), c.get('digg_count')) for c in d.get('comments') or []]
            cur, more = d.get('cursor'), d.get('has_more')
        elif plat == '抖音':
            d = checked_get('/api/v1/douyin/app/v3/fetch_video_comments', dict(aweme_id=p['id'], cursor=cur, count=20)).get('data') or {}
            out += [(c.get('text'), c.get('digg_count')) for c in d.get('comments') or []]
            cur, more = d.get('cursor'), d.get('has_more')
        elif plat == 'YouTube':
            q = dict(video_id=p['id'], sort_by='top')
            if tok:
                q['continuation_token'] = tok
            d = checked_get('/api/v1/youtube/web_v2/get_video_comments', q).get('data') or {}
            out += [(c.get('content'), c.get('like_count')) for c in d.get('comments') or []]
            tok = more = d.get('continuation_token')
        elif plat == 'Instagram':
            q = dict(code_or_url=ig_code(p))
            if tok:
                q['pagination_token'] = tok
            d = checked_get('/api/v1/instagram/v2/fetch_post_comments', q).get('data') or {}
            out += [(c.get('text'), c.get('comment_like_count')) for c in (d.get('data') or {}).get('items') or []]
            tok = more = d.get('pagination_token')
        elif plat == '小红书':
            # First page only: the follow-up cursor is a JSON context the endpoint does not accept back reliably.
            d = (checked_get('/api/v1/xiaohongshu/app_v2/get_note_comments', dict(note_id=p['id'])).get('data') or {}).get('data') or {}
            out += [(c.get('content'), c.get('like_count')) for c in d.get('comments') or []]
            more = False
        else:
            return out
        if not more:
            break
    return out


def to_int(x):
    try:
        return int(str(x).replace(',', ''))
    except (TypeError, ValueError):
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--commercial', type=int, default=15, help='每个平台取多少条商业内容')
    ap.add_argument('--organic', type=int, default=5, help='每个平台取多少条自然内容')
    ap.add_argument('--pages', type=int, default=2)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    b = load_brief(a.brief)
    posts = read_jsonl(os.path.join(b['_raw'], 'posts.jsonl'))
    if not posts:
        sys.exit('raw/posts.jsonl 为空：先运行采集和 normalize.py。')
    cdir = os.path.join(b['_raw'], 'comments')
    os.makedirs(cdir, exist_ok=True)

    pick = []
    for plat in sorted({p['platform'] for p in posts}):
        P = sorted([p for p in posts if p['platform'] == plat], key=metric, reverse=True)
        pick += [p for p in P if p['cat'] != 'organic'][:a.commercial] + [p for p in P if p['cat'] == 'organic'][:a.organic]
    todo = [p for p in pick if read_comment_cache(os.path.join(cdir, f"{p['platform']}_{p['id']}.json")) is None]
    planned = len(todo) * a.pages
    bal, err = tikhub.balance()
    est = planned * tikhub.PRICE_PER_CALL * 3  # comment endpoints cost more than search
    print(f'选中 {len(pick)} 条内容（{dict(collections.Counter(p["platform"] for p in pick))}），待抓 {len(todo)} 条；'
          f'最多 {planned} 次调用，预估 ≤ ${est:.2f}；余额 {bal if bal is not None else "未知 " + str(err)}')
    if a.dry_run:
        return
    if bal is not None and bal < est:
        sys.exit('余额不足。')

    def job(p):
        rows = fetch(p, a.pages)
        json.dump({'complete': True, 'comments': rows}, open(os.path.join(cdir, f"{p['platform']}_{p['id']}.json"), 'w', encoding='utf-8'), ensure_ascii=False)
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(job, todo))

    out = []
    for p in pick:
        f = os.path.join(cdir, f"{p['platform']}_{p['id']}.json")
        if not os.path.exists(f):
            continue
        for text, likes in read_comment_cache(f) or []:
            text = re.sub(r'\s+', ' ', text or '').strip()
            if len(text) < 4:
                continue
            out.append(dict(platform=p['platform'], post=p['id'], url=p.get('url'), handle=p.get('handle'), cat=p['cat'],
                            text=text[:300], likes=to_int(likes), brand=bool(b['_brand_regex'].search(text)),
                            signals=[k for k, rx in SIG.items() if rx.search(text)]))
    write_jsonl(os.path.join(b['_raw'], 'comments.jsonl'), out)

    md = [f"# {b['brand']} 评论摘录", '',
          f"来源：{len({c['post'] for c in out})} 条内容下的 {len(out)} 条评论（每个平台商业内容前 {a.commercial} 条 + 自然内容前 {a.organic} 条）。",
          '信号标签只是关键词粗分，用来排序，读的时候自己判断；跑题的评论（夸博主、玩梗）直接跳过。', '']
    for sig in SIGNALS:
        C = sorted([c for c in out if sig in c['signals']], key=lambda c: -c['likes'])
        md += [f'## {sig}（{len(C)} 条）', '']
        md += [f"- [{c['platform']}·{'商业' if c['cat'] != 'organic' else '自然'}·@{c['handle']}]({c['url']}) 👍{c['likes']} {c['text']}" for c in C[:40]]
        md.append('')
    C = sorted([c for c in out if not c['signals']], key=lambda c: -c['likes'])
    md += [f'## 未分类、点赞最高（{len(C)} 条，只列前 30）', '']
    md += [f"- [{c['platform']}·@{c['handle']}]({c['url']}) 👍{c['likes']} {c['text']}" for c in C[:30]]
    path = os.path.join(b['_base'], '评论摘录.md')
    open(path, 'w', encoding='utf-8').write('\n'.join(md))
    cnt = collections.Counter(s for c in out for s in c['signals'])
    print(f'共 {len(out)} 条评论 | {dict(cnt)} | 写入 raw/comments.jsonl 和 {os.path.basename(path)}')
    bal2, _ = tikhub.balance()
    if bal is not None and bal2 is not None:
        print(f'花费 ${bal - bal2:.3f}，余额 ${bal2:.2f}')


if __name__ == '__main__':
    main()
