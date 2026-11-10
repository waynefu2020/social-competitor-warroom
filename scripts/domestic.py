"""Collect Xiaohongshu and Douyin content from TikHub and append it to raw/posts_extra.jsonl.

  --stage search   XHS note search + Douyin video search (keywords from the brief)
  --stage details  author profiles for EVERY XHS author (fans, bio) + Douyin video details (星图 / 挂车 flags)
  --stage import   parse raw responses into raw/posts_extra.jsonl rows, which normalize.py merges
  --dry-run        print planned calls, estimated cost and current balance; fetch nothing

Commercial signals come from platform fields, not caption keywords:
  XHS   note.widgets_context.order_cooperate == true  -> 蒲公英合作订单 (paid)
  抖音  detail star_atlas_info.log_extra.is_star       -> 星图商单 (paid)
        detail carries promotion_id                    -> 挂车带货 (affiliate)
Private deals carry neither, so 'organic' on these platforms is an upper bound.
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_brief, write_jsonl  # noqa: E402
import tikhub  # noqa: E402

XHS_SORTS = (('popularity_descending', 'xhs_hot_pages', 3), ('general', 'xhs_pages', 2))


def save(path, data):
    tikhub.save_cache(path, data)


def post(path, body, retries=3):
    # Douyin search only answers POST; the GET variants return 404.
    req = urllib.request.Request(tikhub.BASE + path, data=json.dumps(body).encode(), method='POST',
                                 headers={'Authorization': 'Bearer ' + tikhub.api_key(), 'User-Agent': 'curl/8.7.1',
                                          'Content-Type': 'application/json', 'Accept': 'application/json'})
    err = ''
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
                error = tikhub.response_error(data)
                return {'error': error} if error else data
        except urllib.error.HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code in (400, 401, 402, 403, 404, 422):
                break
        except Exception as e:
            err = str(e)
        if attempt + 1 < retries:
            time.sleep(2 + attempt * 3)
    return {'error': err}


def num(x):
    s = str(x or 0).replace(',', '').replace('+', '')
    try:
        return int(float(s.replace('万', '').replace('w', '')) * 1e4) if re.search('[万w]', s) else int(float(s))
    except ValueError:
        return 0


def xhs_items(d):
    x = d.get('data') or {}
    x = x.get('data', x)
    return x.get('items') or []


def xhs_search(b, i, kw, sort, pages):
    n = 0
    for page in range(1, pages + 1):
        p = os.path.join(b['_raw'], 'cn', f'xhs_{i}_{sort}_p{page}.json')
        d = tikhub.read_cache(p)
        if d is None:
            d = tikhub.get(
                '/api/v1/xiaohongshu/app_v2/search_notes', dict(keyword=kw, page=page, sort_type=sort, note_type='不限', time_filter='半年内'))
        save(p, d)
        items = xhs_items(d)
        n += len(items)
        if not items:
            break
    return f'小红书「{kw}」{sort}: {n}'


def dy_search(b, i, kw, sort, pages):
    n, cur, sid, bt = 0, 0, '', ''
    for page in range(pages):
        p = os.path.join(b['_raw'], 'cn', f'dy_{i}_s{sort}_p{page}.json')
        d = tikhub.read_cache(p)
        if d is None:
            d = post(
                '/api/v1/douyin/search/fetch_video_search_v2',
                dict(keyword=kw, cursor=cur, sort_type=sort, publish_time='180', filter_duration='0', content_type='0', search_id=sid, backtrace=bt))
        save(p, d)
        data = d.get('data') or {}
        n += len(data.get('business_data') or [])
        bc = data.get('business_config') or {}
        nxt = bc.get('next_page') or {}
        if not bc.get('has_more') or not nxt:
            break
        cur, sid = nxt.get('cursor', 0), nxt.get('search_id', '')
        m = re.search(r'"backtrace": ?"([^"]*)"', json.dumps(d, ensure_ascii=False))
        bt = m.group(1) if m else ''
    return f'抖音「{kw}」sort{sort}: {n}'


def find_key(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        o = list(o.values())
    if isinstance(o, list):
        for v in o:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def dy_flags(d):
    # The cart meta also has an is_star_atlas field that stays false on real 星图 orders; only star_atlas_info is reliable.
    star = False
    sai = find_key(d, 'star_atlas_info')
    if isinstance(sai, dict):
        try:
            star = bool(json.loads(sai.get('log_extra') or '{}').get('is_star'))
        except ValueError:
            star = '"is_star":true' in (sai.get('log_extra') or '')
    return star, 'promotion_id' in json.dumps(d)


def xhs_user(d):
    s = json.dumps(d, ensure_ascii=False)
    # The fans count sits in different places depending on the profile layout.
    m = (re.search(r'"fans": ?"?([0-9]+)', s) or re.search(r'"count": ?"?([0-9]+)"?,[^{}]*"type": "fans"', s)
         or re.search(r'"type": "fans"[^{}]*"count": ?"?([0-9]+)', s))
    desc = find_key(d, 'desc')
    return dict(fans=int(m.group(1)) if m else None, bio=desc if isinstance(desc, str) else '')


def parse_xhs(b):
    rows = {}
    for f in glob.glob(os.path.join(b['_raw'], 'cn', 'xhs_*.json')):
        for it in xhs_items(json.load(open(f))):
            n = it.get('note') or {}
            if not n.get('id'):
                continue
            try:
                w = json.loads(n.get('widgets_context') or '{}')
            except ValueError:
                w = {}
            u = n.get('user') or {}
            prof = os.path.join(b['_raw'], 'cn', 'xhsuser', f"{u.get('userid')}.json")
            up = xhs_user(json.load(open(prof))) if os.path.exists(prof) else {}
            rows[n['id']] = dict(platform='小红书', id=n['id'], handle=u.get('nickname'), uid=u.get('userid'), followers=up.get('fans'),
                                 bio=up.get('bio', ''), views=None, likes=num(n.get('liked_count')), collects=num(n.get('collected_count')),
                                 comments=num(n.get('comments_count')), ts=n.get('timestamp') or n.get('update_time'),
                                 title=n.get('title') or '', text=f"{n.get('title') or ''} {n.get('desc') or ''}",
                                 url=f"https://www.xiaohongshu.com/explore/{n['id']}",
                                 paidflag=bool(w.get('order_cooperate')), shop=False, disclosed=False, source='tikhub:xhs')
    return list(rows.values())


def parse_dy(b):
    rows = {}
    for f in glob.glob(os.path.join(b['_raw'], 'cn', 'dy_*.json')):
        for it in ((json.load(open(f)).get('data') or {}).get('business_data') or []):
            a = (it.get('data') or {}).get('aweme_info')
            if not a:
                continue
            au, st = a.get('author') or {}, a.get('statistics') or {}
            det = os.path.join(b['_raw'], 'cn', 'dydetail', f"{a['aweme_id']}.json")
            star, cart = dy_flags(json.load(open(det))) if os.path.exists(det) else (False, False)
            rows[a['aweme_id']] = dict(platform='抖音', id=a['aweme_id'], handle=au.get('nickname'), uid=au.get('uid'),
                                       followers=au.get('follower_count'), bio=au.get('signature') or '', views=None,
                                       likes=st.get('digg_count'), collects=st.get('collect_count'), comments=st.get('comment_count'),
                                       ts=a.get('create_time'), text=a.get('desc') or '', url=f"https://www.douyin.com/video/{a['aweme_id']}",
                                       paidflag=star, shop=cart, disclosed=False, detail=os.path.exists(det), source='tikhub:douyin')
    return list(rows.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--stage', choices=['search', 'details', 'import'], required=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    b = load_brief(a.brief)
    for d in ('cn', 'cn/xhsuser', 'cn/dydetail'):
        os.makedirs(os.path.join(b['_raw'], d), exist_ok=True)
    xk, dk = b.get('xhs_keywords') or [], b.get('douyin_keywords') or []

    if a.stage == 'import':
        rows = parse_xhs(b) + parse_dy(b)
        brand = b['_brand_regex']
        rows = [r for r in rows if brand.search(r['text'])]
        path = os.path.join(b['_raw'], 'posts_extra.jsonl')
        keep = [json.loads(l) for l in open(path, encoding='utf-8')] if os.path.exists(path) else []
        keep = [r for r in keep if r.get('source') not in ('tikhub:xhs', 'tikhub:douyin')]
        write_jsonl(path, keep + rows)
        for plat in ('小红书', '抖音'):
            P = [r for r in rows if r['platform'] == plat]
            if P:
                print(f"{plat}: {len(P)} 条提及品牌 | 平台商业标记 {sum(r['paidflag'] for r in P)} | 挂车 {sum(r['shop'] for r in P)} | "
                      f"有粉丝数 {sum(1 for r in P if r.get('followers'))}" + (f" | 已抓详情 {sum(r['detail'] for r in P)}" if plat == '抖音' else ''))
        print('写入 raw/posts_extra.jsonl，接着运行 normalize.py。')
        return

    if a.stage == 'search':
        jobs = [(xhs_search, i, kw, s, int(b.get(k, n))) for i, kw in enumerate(xk) for s, k, n in XHS_SORTS]
        jobs += [(dy_search, i, kw, s, int(b.get('douyin_pages', 5))) for i, kw in enumerate(dk) for s in ('0', '1')]
        planned = sum(j[4] for j in jobs)
    else:
        xrows, drows = parse_xhs(b), parse_dy(b)
        brand = b['_brand_regex']
        uids = sorted({r['uid'] for r in xrows if r.get('uid') and brand.search(r['text'])
                       and tikhub.read_cache(os.path.join(b['_raw'], 'cn', 'xhsuser', f"{r['uid']}.json")) is None})
        vids = sorted({r['id'] for r in drows if brand.search(r['text'])
                       and tikhub.read_cache(os.path.join(b['_raw'], 'cn', 'dydetail', f"{r['id']}.json")) is None})
        planned = len(uids) + len(vids)

    bal, err = tikhub.balance()
    est = planned * tikhub.PRICE_PER_CALL * 2  # domestic endpoints cost roughly twice the overseas average
    print(f'计划调用：最多 {planned} 次，预估 ≤ ${est:.2f}；当前余额：{bal if bal is not None else "未知 " + str(err)}')
    if a.dry_run:
        return
    if bal is not None and bal < est:
        sys.exit('余额不足，先充值或减少关键词/页数。')

    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        if a.stage == 'search':
            for r in ex.map(lambda j: j[0](b, *j[1:]), jobs):
                print(r, flush=True)
        else:
            # Profiles for every author, not just the top posts: enriching a subset biases any by-creator-type comparison.
            list(ex.map(lambda u: save(os.path.join(b['_raw'], 'cn', 'xhsuser', f'{u}.json'),
                                       tikhub.get('/api/v1/xiaohongshu/app_v2/get_user_info', dict(user_id=u))), uids))
            list(ex.map(lambda v: save(os.path.join(b['_raw'], 'cn', 'dydetail', f'{v}.json'),
                                       tikhub.get('/api/v1/douyin/app/v3/fetch_one_video', dict(aweme_id=v))), vids))
            print(f'小红书作者主页 {len(uids)} 个，抖音视频详情 {len(vids)} 条')
    bal2, _ = tikhub.balance()
    if bal is not None and bal2 is not None:
        print(f'本阶段花费 ${bal - bal2:.3f}，余额 ${bal2:.2f}')


if __name__ == '__main__':
    main()
