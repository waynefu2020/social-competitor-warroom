import csv
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import analyze


class AnalysisTests(unittest.TestCase):
    def test_matrix_separates_platforms_and_counts_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'labels.csv'
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['平台', '博主', '内容形式'])
                for platform in ('TikTok', '小红书', 'B站'):
                    writer.writerow([platform, 'creator', '测评'])
            posts = [dict(platform='TikTok', handle='creator', views=1000),
                     dict(platform='小红书', handle='creator', likes=10),
                     dict(platform='小红书', handle='creator', likes=None),
                     dict(platform='B站', handle='creator', views=200)]
            rows = {r['platform']: r for r in analyze.content_matrix(posts, path)}
            self.assertEqual(rows['TikTok']['median'], 1000)
            self.assertEqual(rows['B站']['median'], 200)
            self.assertEqual(rows['小红书']['median'], 10)
            self.assertEqual(rows['小红书']['n'], 2)
            self.assertEqual(rows['小红书']['metric_n'], 1)
            self.assertEqual(rows['小红书']['unit'], '点赞')
            self.assertEqual(rows['TikTok']['unit'], '播放')

    def test_missing_views_or_high_ratio_cannot_establish_causality(self):
        for ratio in (None, 0.5, 20):
            label, reason = analyze.archetype(dict(total=200, organic_share=.9,
                                                  brandled_vs_organic_views=ratio))
            self.assertNotIn('自来水型', label)
            self.assertNotIn('买量型', label)
        self.assertEqual(analyze.archetype(dict(total=4, organic_share=0,
                                               affiliate_of_commercial=1))[0], '证据不足')

    def test_missing_and_invalid_metrics_are_not_zero(self):
        self.assertEqual(analyze.med([None, True, -1, float('nan'), 0]), [0, 1])
        self.assertIsNone(analyze.metric(dict(platform='B站', views=None, likes=10)))
        self.assertIn('B站', analyze.PLATS)

    def test_tier_performance_rejects_mixed_platforms(self):
        with self.assertRaises(ValueError):
            analyze.tier_perf([dict(platform='TikTok'), dict(platform='小红书')])
        result = analyze.tier_perf([dict(platform='TikTok', cat='paid', followers=100,
                                        views=10, handle='a')])
        self.assertIsNone(result['best_ratio'])
        self.assertIn('不代表', result['ratio_note'])


if __name__ == '__main__':
    unittest.main()
