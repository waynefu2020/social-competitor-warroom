"""Compute KPIs, archetype and benchmark position from raw/posts.jsonl.

Writes <base>/analysis.json and <base>/<brand>_内容清单.csv.
--save-benchmark appends/updates this brand in references/benchmarks.json.
"""
import argparse
import collections
import csv
import datetime
import json
import math
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, load_brief, read_jsonl  # noqa: E402
from lexicons import POINTS, THEMES  # noqa: E402

PLATS = ['TikTok', 'Instagram', 'YouTube', '小红书', '抖音', 'B站']
CATS = ['organic', 'gifted', 'affiliate', 'paid', 'collab']
CN = {'organic': '未识别合作信号', 'gifted': '寄样(PR)', 'affiliate': '联盟带货', 'paid': '付费合作', 'collab': '品牌合作(未注明)'}
TIERS = ['纳米 <1万', '小 1-10万', '中 10-50万', '大 50-100万', '头部 100万+', '未知']


def tier(f):
    if not f:
        return '未知'
    for lim, name in [(1e4, TIERS[0]), (1e5, TIERS[1]), (5e5, TIERS[2]), (1e6, TIERS[3])]:
        if f < lim:
            return name
    return TIERS[4]


def lang(t):
    for code, rx in [('ko', r'[가-힯]'), ('ja', r'[぀-ヿ]'), ('th', r'[฀-๿]'), ('ru', r'[Ѐ-ӿ]'),
                     ('hi', r'[ऀ-ॿ]'), ('zh', r'[一-鿿]'), ('vi', r'[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]')]:
        if re.search(rx, t, re.I):
            return code
    low = t.lower()
    for code, rx in [('es', r'\b(el|los|las|que|para|con|más|reuniones|maquillaje)\b'), ('pt', r'\b(você|não|ainda|maquiagem)\b'),
                     ('fr', r'\b(je|les|avec|une|très|maquillage)\b'), ('de', r'\b(und|ich|nicht|mit|das)\b'), ('it', r'\b(della|che|questa|trucco)\b'),
                     ('id/ms', r'\b(yang|bisa|banget|sangat|tak)\b')]:
        if re.search(rx, low):
            return code
    return 'en'


def valid_metric(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def med(xs):
    xs = [x for x in xs if valid_metric(x)]
    return [statistics.median(xs) if xs else None, len(xs)]


def counts(texts, dic):
    c = collections.Counter()
    for t in texts:
        for k, rx in dic.items():
            if re.search(rx, t, re.I):
                c[k] += 1
    return dict(c)


LIKE_PLATS = ('小红书', '抖音')  # no public view counts


def metric(p):
    v = p.get('likes') if p['platform'] in LIKE_PLATS else p.get('views')
    return v if valid_metric(v) else None


def tier_perf(P):
    """Which follower tier of commercial creators performs best: absolute median and median per follower."""
    if len({p['platform'] for p in P}) > 1:
        raise ValueError('tier_perf requires one platform; do not mix metrics')
    out = []
    for t in TIERS[:-1]:
        ps = [p for p in P if p['cat'] != 'organic' and tier(p.get('followers')) == t and metric(p) is not None]
        if not ps:
            continue
        v = [metric(p) for p in ps]
        r = [metric(p) / p['followers'] for p in ps if p.get('followers')]
        out.append(dict(tier=t, n=len(ps), creators=len({p.get('handle') for p in ps}), median=statistics.median(v),
                        per_follower=statistics.median(r) if r else None))
    # Per-follower is a descriptive ratio only, not cost efficiency or ROI.
    # Prices, conversions, and attributed revenue are not observed.
    ok = [x for x in out if x['n'] >= 5]
    ok = ok if len(ok) >= 2 else []  # a single eligible tier has nothing to beat
    return dict(rows=out, platform=P[0]['platform'] if P else None,
                ratio_note='指标/粉丝仅描述触达或互动，不代表成本效率或 ROI', unit='点赞' if P and P[0]['platform'] in LIKE_PLATS else '播放',
                best_abs=max(ok, key=lambda x: x['median'])['tier'] if ok else None,
                best_ratio=max(ok, key=lambda x: x['per_follower'] or 0)['tier'] if ok else None)


def content_matrix(posts, labels_path):
    """Content direction table from the manual labels: form x creator type x audience x selling point, with examples."""
    if not os.path.exists(labels_path):
        return None
    with open(labels_path, encoding='utf-8-sig') as f:
        lab = {(r['平台'], r['博主']): r for r in csv.DictReader(f)}
    groups = collections.defaultdict(list)
    for p in posts:
        r = lab.get((p['platform'], p.get('handle') or ''))
        key = r and (r.get('内容形式') or '').strip()
        if key:
            groups[(p['platform'], key)].append((p, r))
    rows = []
    for (platform, form), items in sorted(groups.items(), key=lambda x: -len(x[1])):
        top = lambda col: [k for k, _ in collections.Counter(r.get(col, '').strip() for _, r in items if r.get(col, '').strip()).most_common(3)]
        ex = sorted(items, key=lambda it: -(metric(it[0]) or 0))[:3]
        vals = [metric(p) for p, _ in items if metric(p) is not None]
        rows.append(dict(form=form, platform=platform, n=len(items), metric_n=len(vals), creator_types=top('博主类型'), audiences=top('沟通人群'), points=top('传播卖点'),
                         median=statistics.median(vals) if vals else None, unit='点赞' if items[0][0]['platform'] in LIKE_PLATS else '播放',
                         examples=[dict(u=p.get('url'), h=p.get('handle'), p=p['platform'], v=metric(p)) for p, _ in ex]))
    return rows or None


def brand_led(p):
    return p['cat'] in ('paid', 'collab', 'gifted') or (p['cat'] == 'affiliate' and p.get('channel') == '官网专属折扣码')


def archetype(k):
    # Disclosure and search samples do not establish paid amplification,
    # organic causality, conversion, or a brand's overall marketing strategy.
    total = k.get('total', 0)
    commercial = total * (1 - k.get('organic_share', 1))
    if total < 30 or commercial < 5:
        return '证据不足', '合作披露或样本不足，不能判断声量驱动力；未识别合作信号不等于自然内容。'
    comm_aff = k.get('affiliate_of_commercial')
    if comm_aff is not None and comm_aff >= 0.5:
        return '联盟信号较多', f'已识别商业信号的样本里 {comm_aff:.0%} 为联盟/带货信号，不能据此推断成交或投放效果。'
    return '合作信号混合', '仅描述检索样本的合作信号分布；播放差异不能证明买量，未披露内容不能证明用户自传播。'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--save-benchmark', action='store_true')
    a = ap.parse_args()
    b = load_brief(a.brief)
    posts = read_jsonl(os.path.join(b['_raw'], 'posts.jsonl'))
    if not posts:
        sys.exit('raw/posts.jsonl 为空：先运行 collect.py 和 normalize.py。')
    cat = b.get('category', 'general')
    themes, points, products = THEMES.get(cat, THEMES['general']), POINTS.get(cat, POINTS['general']), b.get('products') or {}

    plat = {}
    for pn in PLATS:
        P = [p for p in posts if p['platform'] == pn]
        if not P:
            continue
        comm = [p for p in P if p['cat'] != 'organic']
        first = {}
        for p in P:
            first.setdefault(p['handle'], p)
        crC = {p['handle']: p.get('followers') for p in comm}
        crO = {p['handle']: p.get('followers') for p in P if p['cat'] == 'organic'}
        texts = [p['text'] for p in P]
        plat[pn] = dict(
            total=len(P), creators=len(first),
            bycat={c: sum(1 for p in P if p['cat'] == c) for c in CATS},
            creators_bycat={c: len({p['handle'] for p in P if p['cat'] == c}) for c in CATS},
            views={c: med([p.get('views') for p in P if p['cat'] == c]) for c in CATS},
            likes={c: med([p.get('likes') for p in P if p['cat'] == c]) for c in CATS},
            views_brandled=med([p.get('views') for p in P if brand_led(p)]),
            fmed_comm=med(list(crC.values()))[0], fmed_org=med(list(crO.values()))[0],
            tiers_comm={t: sum(1 for f in crC.values() if tier(f) == t) for t in TIERS},
            tiers_org={t: sum(1 for f in crO.values() if tier(f) == t) for t in TIERS},
            products=counts(texts, products), themes=counts(texts, themes), points=counts(texts, points),
            langs=collections.Counter(lang(p.get('title') or p['text']) for p in P).most_common(8),
            channels=collections.Counter(p['channel'] for p in P if p.get('channel')).most_common(),
            per_creator_commercial=round(len(comm) / max(1, len(crC)), 2),
            tier_perf=tier_perf(P),
        )

    allc = collections.Counter(p['cat'] for p in posts)
    n = len(posts)
    tt = plat.get('TikTok') or {}
    org_v = (tt.get('views') or {}).get('organic', [None])[0]
    bl_v = (tt.get('views_brandled') or [None])[0]
    comm_n = n - allc['organic']
    kpi = dict(
        total=n, creators=len({(p['platform'], p['handle']) for p in posts}),
        organic_share=allc['organic'] / n, unclassified_share=allc['organic'] / n,
        organic_definition='兼容字段：未识别合作信号，不代表确认自然内容', paid_share=allc['paid'] / n, gifted_share=allc['gifted'] / n,
        affiliate_share=allc['affiliate'] / n, collab_share=allc['collab'] / n, bycat=dict(allc),
        brandled_vs_organic_views=(bl_v / org_v) if (bl_v is not None and org_v and
            tt['views']['organic'][1] >= 5 and tt['views_brandled'][1] >= 5) else None,
        brandled_vs_organic_views_n={'brandled': (tt.get('views_brandled') or [None, 0])[1],
                                   'unclassified': (tt.get('views') or {}).get('organic', [None, 0])[1]},
        brandled_vs_organic_views_platform='TikTok',
        affiliate_of_commercial=(allc['affiliate'] / comm_n) if comm_n else None,
        commercial_follower_median=med([p.get('followers') for p in posts if p['cat'] != 'organic'])[0],
    )
    traffic = None
    swp = os.path.join(b['_raw'], 'sales', 'similarweb.json')
    if os.path.exists(swp):
        sw = json.load(open(swp))
        sw = sw.get('data', sw)
        ts = sw.get('trafficSources') or {}
        traffic = dict(sources=ts, monthly=sw.get('monthlyVisits'), visits=[v.get('visits') for v in sw.get('visitsHistory') or []],
                       countries=[[c.get('countryName'), c.get('share')] for c in (sw.get('topCountries') or [])[:6]])
        kpi['social_traffic_share'] = (ts.get('socialOrganic') or 0) + (ts.get('socialPaid') or 0)
    kpi['archetype'], kpi['archetype_reason'] = archetype(kpi)
    # Keep coverage visible; disclosure patterns remain descriptive even with larger samples.
    with_views = sum(1 for p in posts if p['platform'] in ('TikTok', 'Instagram', 'YouTube', 'B站') and valid_metric(p.get('views')))
    if n < 100 or with_views < 30:
        kpi['archetype'] += '（描述性结果，样本不足）'
        kpi['archetype_reason'] += f'但样本只有 {n} 条、带播放量的 {with_views} 条，需要更完整的数据验证。'

    bench_path = os.path.join(SKILL_DIR, 'references', 'benchmarks.json')
    bench = [x for x in (json.load(open(bench_path)) if os.path.exists(bench_path) else []) if x.get('brand') != b['brand']]
    me = dict(brand=b['brand'], category=cat, window=b['_window'], archetype=kpi['archetype'], organic_share=round(kpi['organic_share'], 3),
              paid_share=round(kpi['paid_share'], 3), gifted_share=round(kpi['gifted_share'], 3), affiliate_share=round(kpi['affiliate_share'], 3),
              brandled_vs_organic_views=round(kpi['brandled_vs_organic_views'], 2) if kpi['brandled_vs_organic_views'] else None,
              commercial_follower_median=kpi['commercial_follower_median'], social_traffic_share=round(kpi.get('social_traffic_share'), 3) if kpi.get('social_traffic_share') is not None else None)

    rows = [dict(p=p['platform'], h=p.get('handle'), f=int(p['followers']) if p.get('followers') else None, tier=tier(p.get('followers')),
                 c=p['cat'], ch=p.get('channel') or '', v=p.get('views') if isinstance(p.get('views'), (int, float)) else None,
                 l=p.get('likes') if isinstance(p.get('likes'), (int, float)) else None, lang=lang(p.get('title') or p['text']), u=p.get('url'),
                 t=re.sub(r'\s+', ' ', p.get('title') or p['text'])[:140], ts=p['ts']) for p in posts]

    coverage = dict(sources=dict(collections.Counter(p.get('source', 'tikhub') for p in posts)),
                    no_date=sum(1 for p in posts if p.get('ts_unknown')),
                    no_followers={pn: sum(1 for p in posts if p['platform'] == pn and not p.get('followers')) for pn in plat})
    labels_path = os.path.join(b['_base'], b.get('labels') or 'labels.csv')
    comments = read_jsonl(os.path.join(b['_raw'], 'comments.jsonl'))
    out = dict(brand=b['brand'], category=cat, window=b['_window'], decision_question=b.get('decision_question', ''), coverage=coverage,
               content_matrix=content_matrix(posts, labels_path),
               comments=dict(n=len(comments), posts=len({c['post'] for c in comments}),
                             signals=dict(collections.Counter(s for c in comments for s in c['signals']))) if comments else None,
               plat=plat, kpi=kpi, me=me, benchmarks=bench, traffic=traffic, rows=rows, tiers=TIERS,
               themes=list(themes), points=list(points), products=list(products))
    json.dump(out, open(os.path.join(b['_base'], 'analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)

    csv_path = os.path.join(b['_base'], f"{b['brand']}_内容清单.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['平台', '博主', '粉丝数', '量级', '类型', '转化渠道', '播放量', '点赞', '语言', '发布日期', '链接', '内容摘要'])
        for r in sorted(rows, key=lambda r: (r['p'], -(r['v'] or 0))):
            w.writerow([r['p'], r['h'], r['f'] or '', r['tier'], CN[r['c']], r['ch'], r['v'] or '', r['l'] or '', r['lang'],
                        datetime.date.fromtimestamp(r['ts']).isoformat() if r['ts'] else '', r['u'], r['t']])

    if a.save_benchmark:
        json.dump(bench + [me], open(bench_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f"打法画像：{kpi['archetype']} —— {kpi['archetype_reason']}")
    print(f"共 {n} 条 / {kpi['creators']} 位博主 | 未识别合作 {kpi['organic_share']:.0%} · 寄样 {kpi['gifted_share']:.0%} · 联盟 {kpi['affiliate_share']:.0%} · "
          f"付费 {kpi['paid_share']:.1%} · 品牌合作 {kpi['collab_share']:.0%}")
    for pn, d in plat.items():
        v = d['views']
        if not any(v[c][1] for c in CATS):  # 小红书、抖音没有公开播放量
            lk = d['likes']
            print(f"{pn}: {d['total']} 条 / {d['creators']} 人 | 点赞中位数 未识别合作 {lk['organic'][0]} · 付费 {lk['paid'][0]} · 联盟 {lk['affiliate'][0]} "
                  f"| 商业博主粉丝中位数 {d['fmed_comm']}")
            continue
        print(f"{pn}: {d['total']} 条 / {d['creators']} 人 | 播放中位数 未识别合作 {v['organic'][0]} · 联盟 {v['affiliate'][0]} · 品牌主导 {d['views_brandled'][0]} "
              f"| 商业博主粉丝中位数 {d['fmed_comm']} | 渠道 {d['channels'][:4]}")
    for pn, d in plat.items():
        tp = d['tier_perf']
        if tp['rows']:
            print(f"{pn} 商业博主量级效果（{tp['unit']}中位 / ÷粉丝）：" + '；'.join(
                f"{x['tier']} {x['n']}条 {x['median']:,.0f} / {x['per_follower']:.0%}" if x['per_follower'] is not None else f"{x['tier']} {x['n']}条 {x['median']:,.0f}"
                for x in tp['rows']) + (f" → 绝对值最高 {tp['best_abs']}，÷粉丝最高 {tp['best_ratio']}" if tp['best_abs'] else '（≥5 条的量级不足两档，不评最优）'))
    if out['content_matrix']:
        print(f"内容方向表：{len(out['content_matrix'])} 种内容形式（来自 {os.path.basename(labels_path)}）")
    print(f'对标库 {len(bench)} 个品牌；输出 analysis.json 与 {os.path.basename(csv_path)}')


if __name__ == '__main__':
    main()
