"""Offline report contract and HTML injection regressions (standard library only)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_report as report


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.brief = {'brand': '测试品牌'}
        self.analysis = {'window': '2026-01-01 → 2026-02-01', 'kpi': {'total': 0, 'creators': 0, 'organic_share': 0},
                         'rows': [{'u': 'https://example.com/post?a=1&b=2', 'v': 0}]}
        self.narrative = {'verdict': '有限样本，无法判断效果。', 'summary': [{'finding': '缺价格', 'sowhat': '先验证'}],
                          'actions': [{'title': '补采样', 'priority': '高'}]}

    def test_all_styles_are_offline_and_have_seven_sections(self):
        for style in report.STYLES:
            with self.subTest(style=style):
                rendered = report.render_report(self.analysis, self.narrative, self.brief, style)
                document = Document(rendered)
                self.assertIn(('body', {'class': style}), document.tags)
                ids = {attrs.get('id') for _, attrs in document.tags}
                self.assertTrue({f's{i}' for i in range(7)}.issubset(ids))
                self.assertFalse(any(tag == 'link' or 'src' in attrs for tag, attrs in document.tags))
                self.assertIn('未提供 / 待补充证据', rendered)
                self.assertIn('https://example.com/post?a=1&amp;b=2', rendered)
                self.assertIn('<strong>0</strong>', rendered)

    def test_style_precedence_and_aliases(self):
        self.assertEqual(report.resolve_style(None, {}, {})[0], 'editorial')
        self.assertEqual(report.resolve_style('swiss', {'style': 'editorial'}, {})[0], 'swiss')
        self.assertEqual(report.resolve_style('auto', {'style': 'mckinsey'}, {})[0], 'mckinsey')
        self.assertEqual(report.resolve_style(None, {'purpose': '小红书视频'}, {})[0], 'xhs-craft')
        for old, new in report.ALIASES.items():
            self.assertEqual(report.resolve_style(old, {}, {})[0], new)
        with self.assertRaises(ValueError):
            report.resolve_style('bad', {}, {})

    def test_inputs_cannot_inject_markup_or_placeholders(self):
        attack = '</script><script>alert(1)</script><img src=x onerror=alert(1)>'
        self.narrative['title'] = attack + '__DATA__'
        self.narrative['verdict'] = attack
        self.narrative['sources'] = [{'url': 'javascript:alert(1)'}, {'url': 'data:text/html,bad'}]
        self.analysis['rows'].append({'t': attack})
        rendered = report.render_report(self.analysis, self.narrative, self.brief, 'editorial')
        tags = Document(rendered).tags
        self.assertEqual(sum(tag == 'script' for tag, _ in tags), 2)
        self.assertFalse(any(tag == 'img' for tag, _ in tags))
        self.assertTrue(all(attrs.get('type') == 'application/json' for tag, attrs in tags if tag == 'script'))
        self.assertFalse(any(attrs.get('href', '').startswith(('javascript:', 'data:')) for _, attrs in tags))
        self.assertIn('__DATA__</title>', rendered)
        self.assertEqual(json.loads(report.safe_json(self.analysis)), self.analysis)

    def test_required_narrative_is_not_fabricated(self):
        for value in ({}, [], {'verdict': 'ok', 'summary': [], 'actions': []}):
            with self.assertRaises(ValueError):
                report.render_report({}, value, self.brief, 'editorial')
        self.assertEqual(report.render_value(None), report.render_value([]))
        self.assertEqual(report.render_value(0), '0')

    def test_cli_writes_existing_output_convention(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name, value in [('brief', self.brief), ('analysis', self.analysis), ('narrative', self.narrative)]:
                (base / f'{name}.json').write_text(json.dumps(value), encoding='utf-8')
            for style in report.STYLES:
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_report.py'), '--brief', str(base / 'brief.json'), '--style', style], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((base / f'测试品牌-report-{style}.html').is_file())
            (base / 'narrative.json').unlink()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_report.py'), '--brief', str(base / 'brief.json')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('narrative.json', result.stderr)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
