import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from normalize import classify, signal_text
import yt_sponsor_radar as radar


class ClassificationTests(unittest.TestCase):
    def test_positive_signals(self):
        for text, expected in [('Sponsored by Brand', 'paid'), ('#ad Brand', 'paid'),
                               ('广告合作 Brand', 'paid'), ('Brand gifted this', 'gifted'),
                               ('品牌赠送 Brand', 'gifted'), ('affiliate link Brand', 'affiliate')]:
            with self.subTest(text=text):
                self.assertEqual(classify(text, False, False, False), expected)

    def test_negated_signals(self):
        for text in ('not sponsored by Brand', 'not an ad', "isn't sponsored by Brand",
                     'not a sponsored video', 'unsponsored Brand review', '非广告 Brand',
                     '没有赞助 Brand', '不是付费合作 Brand', 'not gifted Brand',
                     'no affiliate links', 'non-sponsored Brand review',
                     'not sponsored or gifted', 'not financially sponsored by Brand',
                     'not directly sponsored or commercially gifted'):
            with self.subTest(text=text):
                self.assertEqual(classify(text, False, False, False), 'organic')

    def test_negation_does_not_hide_other_evidence(self):
        self.assertEqual(classify('Not sponsored, but affiliate links below', False, False, False), 'affiliate')
        self.assertEqual(classify('Not sponsored by A; sponsored by Brand', False, False, False), 'paid')
        self.assertEqual(classify('Not sponsored', True, False, False), 'paid')
        self.assertEqual(classify('Brand', False, False, True), 'collab')
        self.assertEqual(classify('I bought Brand at Sephora on Amazon', False, False, False), 'organic')

    def test_radar_shared_negation_and_missing_metrics(self):
        rx = re.compile(r'sponsored by Brand', re.I)
        self.assertIsNone(rx.search(signal_text('not sponsored by Brand')))
        self.assertIsNotNone(rx.search(signal_text('not sponsored by A; sponsored by Brand')))
        self.assertIsNone(radar.parse_num(None))
        self.assertIsNone(radar.parse_num('unknown'))
        self.assertEqual(radar.parse_num('0'), 0)
        self.assertEqual(radar.parse_num(0), 0)
        for invalid in (float('nan'), float('inf'), -1, '-1', True, '.', '1.2.3'):
            with self.subTest(invalid=invalid):
                self.assertIsNone(radar.parse_num(invalid))

    def test_radar_fallback_preserves_zero_counts(self):
        self.assertEqual(radar.first_count(0, None), 0)
        self.assertEqual(radar.first_count('0', 100), 0)
        self.assertEqual(radar.first_count(None, 0), 0)
        self.assertEqual(radar.first_count(None, '1K'), 1000)
        self.assertIsNone(radar.first_count(None, 'unknown'))


if __name__ == '__main__':
    unittest.main()
