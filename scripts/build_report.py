"""Render an offline, single-file report from analysis.json and narrative.json."""
import argparse
import html
import json
import os
import re
import sys
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, load_brief  # noqa: E402

STYLES = ('editorial', 'bento-dark', 'mckinsey', 'swiss', 'xhs-craft')
ALIASES = {'brand': 'editorial', 'terminal': 'bento-dark', 'consulting': 'mckinsey',
           'wrapped': 'swiss', 'notebook': 'xhs-craft'}
STYLE_NAMES = dict(zip(STYLES, ('暖纸社论杂志', '暗黑便当盒', '高管作战看板', '瑞士网格', '小红书手账')))
PURPOSE = {'小红书': 'xhs-craft', 'xhs': 'xhs-craft', 'rednote': 'xhs-craft',
           '汇报': 'mckinsey', 'report': 'mckinsey', 'boss': 'mckinsey', 'client': 'mckinsey',
           '社媒': 'swiss', 'social': 'swiss', '视频': 'swiss', 'video': 'swiss'}
CATEGORY = {'tech': 'bento-dark', 'app': 'bento-dark', 'saas': 'bento-dark'}
REQUIRED = ('verdict', 'summary', 'actions')
LABELS = {'platform': '平台', 'metric_n': '有效指标样本数', 'form': '内容形式',
          'median': '中位数', 'unit': '指标单位', 'finding': '发现', 'sowhat': '对我们的含义', 'title': '标题', 'detail': '具体动作',
          'priority': '优先级', 'budget': '预算量级', 'measure': '验证指标与时间', 'type': '动作类型',
          'pain': '用户痛点', 'evidence': '证据', 'opportunity': '机会', 'links': '原帖链接',
          'name': '名称', 'role': '角色', 'url': '来源链接', 'organic': '未识别合作信号（不等于自然）', 'paid': '付费合作',
          'gifted': '寄样', 'affiliate': '联盟带货', 'collab': '品牌合作（未注明）'}


def resolve_style(cli, narrative, brief):
    for style in (cli, narrative.get('style'), brief.get('style')):
        if style and style != 'auto':
            style = ALIASES.get(style, style)
            if style not in STYLES:
                raise ValueError(f'未知风格 {style}，可选：{", ".join(STYLES)}')
            return style, '指定'
    purpose = str(narrative.get('purpose') or brief.get('purpose') or '').lower()
    for key, style in PURPOSE.items():
        if key in purpose:
            return style, f'按用途「{purpose}」'
    category = str(brief.get('category') or '').lower()
    return CATEGORY.get(category, 'editorial'), '按品类或默认'


def esc(value):
    return html.escape(str(value), quote=True)


def safe_json(obj):
    # Even inert application/json script nodes must not allow HTML parser breakouts.
    return json.dumps(obj, ensure_ascii=False, allow_nan=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')


def link(value):
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme.lower() in ('https', 'http') and bool(parsed.netloc)
        valid = valid and not any(ord(c) < 32 for c in value)
    except ValueError:
        valid = False
    if valid:
        return f'<a href="{esc(value)}" target="_blank" rel="noopener noreferrer">{esc(value)}</a>'
    return esc(value)


def render_value(value):
    """Preserve all supplied data; never interpolate input as markup."""
    if value is None or value == '' or value == [] or value == {}:
        return '<p class="missing">未提供 / 待补充证据</p>'
    if isinstance(value, dict):
        return '<dl>' + ''.join(f'<dt>{esc(LABELS.get(k, k))}</dt><dd>{render_value(v)}</dd>' for k, v in value.items()) + '</dl>'
    if isinstance(value, list):
        return '<ul>' + ''.join(f'<li>{render_value(v)}</li>' for v in value) + '</ul>'
    if isinstance(value, str):
        return link(value)
    return esc(value)


def cards(value):
    if not value:
        return render_value(None)
    items = value if isinstance(value, list) else [value]
    return '<div class="grid">' + ''.join(f'<article class="card"><span class="index">{i:02d}</span>{render_value(item)}</article>' for i, item in enumerate(items, 1)) + '</div>'


def section(ident, title, body, source):
    return f'<section id="{ident}"><header class="section-head"><span class="exhibit">EXHIBIT {int(ident[1:]) + 1:02d}</span><h2>{title}</h2></header>{body}<p class="source">来源：{esc(source)}</p></section>'


def render_report(analysis, narrative, brief, style):
    if not isinstance(analysis, dict) or not isinstance(narrative, dict):
        raise ValueError('analysis.json 与 narrative.json 顶层必须为对象')
    if style not in STYLES:
        raise ValueError('报告风格必须是规范名称')
    if not isinstance(narrative.get('verdict'), str) or not narrative['verdict'].strip():
        raise ValueError('narrative.json 缺少非空字符串 verdict')
    for key in ('summary', 'actions'):
        if not isinstance(narrative.get(key), list) or not narrative[key]:
            raise ValueError(f'narrative.json 缺少非空数组 {key}')
    title = narrative.get('title') or f"{brief['brand']}竞品打法拆解"
    kpi = analysis.get('kpi') or {}
    metrics = [('样本内容数', kpi.get('total')), ('样本博主数', kpi.get('creators')),
               ('未识别合作信号占比', f"{kpi['organic_share']:.1%}" if isinstance(kpi.get('organic_share'), (int, float)) else None)]
    hero = '<header class="hero"><p class="eyebrow">COMPETITOR FIELD REPORT · ' + esc(analysis.get('window') or '时间窗未提供') + '</p>'
    hero += '<h1>' + esc(title) + '</h1><p class="thesis">' + esc(narrative['verdict']) + '</p>'
    hero += '<p class="source">判词由 narrative.json 提供；样本指标来自 analysis.json，不代表市场全量。</p><div class="metrics">'
    hero += ''.join(f'<div class="metric"><span>{esc(label)}</span><strong>{esc(value) if value is not None else "待补充"}</strong></div>' for label, value in metrics) + '</div></header>'
    titles = ['核心卖点与执行摘要', '差异化与竞品攻防', '社媒渠道打法', '价格与价值格局', '竞品档案', '真实用户吐槽', '自然内容实证与下一步']
    nav = '<nav aria-label="章节目录">' + ''.join(f'<a href="#s{i}">{i:02d} {title}</a>' for i, title in enumerate(titles)) + '</nav>'
    body = section('s0', titles[0], cards(narrative.get('pillars')) + '<h3>执行摘要</h3>' + cards(narrative['summary']), 'narrative.pillars / summary；缺失核心卖点不自动推断')
    body += section('s1', titles[1], cards(narrative.get('battlecards')), 'narrative.battlecards')
    body += section('s2', titles[2], cards(narrative.get('channel_playbook') or narrative.get('channels')) + '<details><summary>平台统计与内容方向原始数据</summary>' + render_value({'plat': analysis.get('plat'), 'content_matrix': analysis.get('content_matrix')}) + '</details>', 'narrative.channel_playbook / channels；analysis.plat / content_matrix')
    body += section('s3', titles[3], cards(narrative.get('pricing')) + '<p class="missing">未提供可比价格、币种、规格、采集日期和成本时，不作性价比结论。</p>', 'narrative.pricing；不从互动数推导价格或 ROI')
    body += section('s4', titles[4], cards(narrative.get('competitors')) + '<details><summary>对标数据与我方定位</summary>' + render_value({'me': analysis.get('me'), 'benchmarks': analysis.get('benchmarks')}) + '</details>', 'narrative.competitors；analysis.me / benchmarks（不默认视为同期可比）')
    body += section('s5', titles[5], cards(narrative.get('weaknesses')) + '<details><summary>评论样本覆盖</summary>' + render_value(analysis.get('comments')) + '</details>', 'narrative.weaknesses；analysis.comments；未提供评论时不推断痛点')
    body += section('s6', titles[6], cards(narrative.get('organic_proof')) + '<h3>建议动作</h3>' + cards(narrative['actions']), 'narrative.organic_proof / actions；自然内容分类不等于已确认未付费')
    body += '<section id="appendix"><h2>证据明细、来源与局限</h2>' + render_value({'来源': narrative.get('sources'), '口径与局限': narrative.get('method_notes'), '规模口径': narrative.get('scale_notes'), '修订记录': narrative.get('revisions')})
    body += '<details><summary>完整分析数据（含内容原帖链接）</summary>' + render_value(analysis) + '</details><details><summary>完整叙述数据</summary>' + render_value(narrative) + '</details></section>'
    with open(os.path.join(SKILL_DIR, 'assets', 'report_template.html'), encoding='utf-8') as f:
        template = f.read()
    replacements = {'__TITLE__': esc(title), '__STYLE__': style, '__BODY__': hero + nav + body,
                    '__DATA__': safe_json(analysis), '__NARRATIVE__': safe_json(narrative)}
    # One pass avoids interpreting placeholder-like strings within user data.
    return re.sub(r'__(?:TITLE|STYLE|BODY|DATA|NARRATIVE)__', lambda m: replacements[m[0]], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brief', required=True)
    parser.add_argument('--style', choices=('auto',) + STYLES + tuple(ALIASES))
    parser.add_argument('--out', help='输出路径；相对路径以 brief 所在目录为基准')
    args = parser.parse_args()
    try:
        brief = load_brief(args.brief)
        with open(os.path.join(brief['_base'], 'analysis.json'), encoding='utf-8') as f:
            analysis = json.load(f)
        with open(os.path.join(brief['_base'], 'narrative.json'), encoding='utf-8') as f:
            narrative = json.load(f)
        if not isinstance(narrative, dict):
            raise ValueError('narrative.json 顶层必须为对象')
        style, why = resolve_style(args.style, narrative, brief)
        report = render_report(analysis, narrative, brief, style)
        slug = re.sub(r'[^\w.-]+', '-', str(brief.get('slug') or brief['brand'])).strip('.-') or 'brand'
        name = args.out or (f'{slug}-report-{style}.html' if args.style and args.style != 'auto' else f'{slug}-report.html')
        out = os.path.join(brief['_base'], name)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(report)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'报告生成失败：{exc}\n请检查 analysis.json / narrative.json，格式见 references/report-spec.md。\n')
    print(f'已生成 {out} · 风格：{STYLE_NAMES[style]}（{style}，{why}）')


if __name__ == '__main__':
    main()
