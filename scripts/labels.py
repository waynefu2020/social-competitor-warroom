"""Manual creator-type labels, and by-type stats that guard against the usual traps.

  export  write labels.csv: one row per creator with commercial content (bio + sample caption), ready to label by hand
  report  by creator type and by content angle, split by cooperation type, with concentration warnings

Pass several --brief to pool competitors (e.g. "which creator types work for this audience across 5 brands").
Labels are kept on re-export, so you can add a brand and only label the new creators.
"""
import argparse
import collections
import csv
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_brief, read_jsonl  # noqa: E402

COLS = ['平台', '博主', '粉丝', '商业内容条数', '品牌', '简介', '示例文案', '示例链接', '博主类型', '内容角度', '内容形式', '沟通人群', '传播卖点', '备注']
CN = {'organic': '自然', 'gifted': '寄样', 'affiliate': '联盟带货', 'paid': '付费', 'collab': '品牌合作'}
LIKE_PLATS = ('小红书', '抖音')  # no public view counts


def load(briefs, every):
    posts = []
    for path in briefs:
        b = load_brief(path)
        for p in read_jsonl(os.path.join(b['_raw'], 'posts.jsonl')):
            if every or p['cat'] != 'organic':
                p['brand'] = b['brand']
                posts.append(p)
    return posts


def read_labels(path):
    if not os.path.exists(path):
        return {}
    return {(r['平台'], r['博主']): r for r in csv.DictReader(open(path, encoding='utf-8-sig'))}


def export(posts, path):
    old = read_labels(path)
    by = collections.defaultdict(list)
    for p in posts:
        by[(p['platform'], p.get('handle') or '')].append(p)
    rows = []
    for (plat, h), ps in sorted(by.items(), key=lambda x: -len(x[1])):
        top = max(ps, key=lambda p: (p.get('views') or p.get('likes') or 0))
        keep = old.get((plat, h), {})
        rows.append({'平台': plat, '博主': h, '粉丝': top.get('followers') or '', '商业内容条数': len(ps),
                     '品牌': ' / '.join(sorted({p['brand'] for p in ps})), '简介': re.sub(r'\s+', ' ', top.get('bio') or '')[:160],
                     '示例文案': re.sub(r'\s+', ' ', top.get('title') or top['text'])[:160], '示例链接': top.get('url'),
                     **{k: keep.get(k, '') for k in ('博主类型', '内容角度', '内容形式', '沟通人群', '传播卖点', '备注')}})
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    todo = sum(1 for r in rows if not r['博主类型'])
    print(f'写入 {path}：{len(rows)} 位博主，待标注 {todo} 位。逐个点开示例内容看，填“博主类型”“内容角度”；'
          '要出内容方向表，再填“内容形式”（开箱/测评/情景剧/vlog/教程…）“沟通人群”“传播卖点”。不要用正则批量判。')


def metric(p):
    return p.get('likes') if p['platform'] in LIKE_PLATS else p.get('views')


def table(posts, key, unit, hit):
    g = collections.defaultdict(list)
    for p in posts:
        g[(p[key], p['cat'])].append(p)
    print(f'  {key} × 合作类型 | 条数 | {unit}中位数 | {unit}÷粉丝中位 | ≥{hit:,} 占比 | 集中度（最大单号 / 最大品牌）')
    for (k, c), ps in sorted(g.items(), key=lambda x: (x[0][0], -len(x[1]))):
        v = [metric(p) for p in ps if isinstance(metric(p), (int, float))]
        if not v:
            continue
        r = [metric(p) / p['followers'] for p in ps if isinstance(metric(p), (int, float)) and p.get('followers')]
        acc = collections.Counter(p.get('handle') for p in ps).most_common(1)[0]
        br = collections.Counter(p['brand'] for p in ps).most_common(1)[0]
        line = (f'  {k} × {CN[c]} | {len(ps)} | {statistics.median(v):,.0f} | {statistics.median(r):{".1%" if unit == "点赞" else ".2f"}} | '
                f'{sum(x >= hit for x in v) / len(v):.0%} | @{acc[0]} {acc[1]}/{len(ps)} · {br[0]} {br[1]}/{len(ps)}' if r else
                f'  {k} × {CN[c]} | {len(ps)} | {statistics.median(v):,.0f} | - | {sum(x >= hit for x in v) / len(v):.0%} | '
                f'@{acc[0]} {acc[1]}/{len(ps)} · {br[0]} {br[1]}/{len(ps)}')
        print(line)
        if len(ps) < 10:
            print('      ⚠ 样本 < 10，只作参考')
        if len(ps) >= 5 and acc[1] / len(ps) > 0.3:
            rest = [metric(p) for p in ps if p.get('handle') != acc[0] and isinstance(metric(p), (int, float))]
            if rest:
                print(f'      ⚠ 一个号占 {acc[1] / len(ps):.0%}，去掉它后中位数 {statistics.median(rest):,.0f}（{len(rest)} 条）')
        if len(ps) >= 5 and br[1] / len(ps) > 0.6:
            print(f'      ⚠ {br[0]} 占 {br[1] / len(ps):.0%}，结论只代表这个品牌的打法')


def report(posts, path):
    labels = read_labels(path)
    if not labels:
        sys.exit(f'没有找到 {path}，先运行 export 并人工标注。')
    done = []
    for p in posts:
        lab = labels.get((p['platform'], p.get('handle') or ''))
        if lab and lab['博主类型']:
            p['博主类型'], p['内容角度'] = lab['博主类型'], lab['内容角度'] or '未标注'
            done.append(p)
    print(f'已标注 {len(done)} / {len(posts)} 条内容。只在同一合作类型内比较博主类型：联盟、寄样的长尾帖会把整组中位数拉低。')
    for fam, plats, unit, hit in (('海外', None, '播放', 10000), ('国内', LIKE_PLATS, '点赞', 1000)):
        P = [p for p in done if (p['platform'] in LIKE_PLATS) == bool(plats)]
        if not P:
            continue
        print(f'\n## {fam}（{unit}）')
        table(P, '博主类型', unit, hit)
        table(P, '内容角度', unit, hit)
    print('\n没有价格数据时，只能说“播放高/互动高”，不能说“效率高/性价比高”。')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['export', 'report'])
    ap.add_argument('--brief', action='append', required=True, help='可重复，多个竞品合并分析')
    ap.add_argument('--labels', help='标注表路径，默认放在第一个 brief 旁边')
    ap.add_argument('--all', action='store_true', help='连自然内容一起导出/统计（默认只看商业内容）')
    a = ap.parse_args()
    path = a.labels or os.path.join(os.path.dirname(os.path.abspath(a.brief[0])), 'labels.csv')
    posts = load(a.brief, a.all)
    if not posts:
        sys.exit('没有可用内容：先跑 normalize.py。')
    export(posts, path) if a.action == 'export' else report(posts, path)


if __name__ == '__main__':
    main()
