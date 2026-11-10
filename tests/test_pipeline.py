"""Offline smoke test of the documented normalize -> analyze -> report workflow."""
import csv
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_imported_six_platform_sample_to_report(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / 'raw').mkdir()
            brief = {'brand': 'SampleBrand', 'brand_regex': 'SampleBrand',
                     'slug': 'samplebrand', 'end_date': '2026-11-10', 'window_days': 30}
            (base / 'brief.json').write_text(json.dumps(brief), encoding='utf-8')
            platforms = ('YouTube', 'TikTok', 'Instagram', '小红书', '抖音', 'B站')
            posts = [dict(platform=p, id=str(i), handle=f'creator{i}',
                          followers=500, views=None if p in ('小红书', '抖音') else 1000,
                          likes=10, ts=int(datetime.datetime(2026, 11, 1).timestamp()),
                          text='SampleBrand: not financially sponsored or gifted',
                          url=f'https://example.com/{i}', source='offline-fixture')
                     for i, p in enumerate(platforms)]
            (base / 'raw/posts_extra.jsonl').write_text('\n'.join(json.dumps(p) for p in posts) + '\n')
            with (base / 'labels.csv').open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['平台', '博主', '内容形式'])
                writer.writerows((p['platform'], p['handle'], '测评') for p in posts)
            narrative = {'verdict': '离线样例，证据不足。', 'summary': [{'finding': '六平台小样本'}],
                         'actions': [{'title': '先核实合作披露'}]}
            (base / 'narrative.json').write_text(json.dumps(narrative))
            for name in ('normalize', 'analyze', 'build_report'):
                result = subprocess.run([sys.executable, '-B', str(ROOT / f'scripts/{name}.py'),
                                         '--brief', str(base / 'brief.json')],
                                        capture_output=True, text=True,
                                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(result.returncode, 0, result.stderr)
            analysis = json.loads((base / 'analysis.json').read_text())
            self.assertEqual(set(analysis['plat']), set(platforms))
            self.assertEqual(analysis['kpi']['paid_share'], 0)
            self.assertIn('证据不足', analysis['kpi']['archetype'])
            self.assertEqual(len(analysis['content_matrix']), 6)
            self.assertEqual({r['median'] for r in analysis['content_matrix']}, {10, 1000})
            self.assertTrue((base / 'samplebrand-report.html').is_file())


if __name__ == '__main__':
    unittest.main()
