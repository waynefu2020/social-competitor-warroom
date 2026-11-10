"""Offline API/cache regressions: no credentials or paid calls."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect
import comments
import domestic
import tikhub


class ResponseTests(unittest.TestCase):
    def test_http_200_api_error_is_not_success(self):
        for payload in ({'code': 429, 'message': 'rate limited', 'data': {}},
                        {'success': False, 'data': {}}, {'error': 'timeout'},
                        {'code': 200, 'data': None}, [], {}):
            with self.subTest(payload=payload):
                self.assertIsNotNone(tikhub.response_error(payload))
                with self.assertRaises(RuntimeError):
                    tikhub.require_success(payload)

    def test_empty_success_is_valid(self):
        for payload in ({'code': 200, 'data': {}}, {'code': 0, 'data': []}, {'data': {'videos': []}}):
            self.assertIsNone(tikhub.response_error(payload))

    def test_get_catches_business_error(self):
        response = io.StringIO(json.dumps({'code': 402, 'message': 'insufficient balance'}))
        with patch.object(tikhub, 'api_key', return_value='test'), patch.object(tikhub.urllib.request, 'urlopen', return_value=response):
            self.assertIn('402', tikhub.get('/test')['error'])

    def test_domestic_post_catches_business_error(self):
        response = io.StringIO(json.dumps({'code': 429, 'message': 'rate limited'}))
        with patch.object(tikhub, 'api_key', return_value='test'), patch.object(domestic.urllib.request, 'urlopen', return_value=response):
            self.assertIn('429', domestic.post('/test', {})['error'])


class CacheTests(unittest.TestCase):
    def test_success_only_cache_and_corrupt_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            path.write_text('{invalid')
            self.assertIsNone(tikhub.read_cache(path))
            path.write_text(json.dumps({'error': 'long ' * 100}))
            self.assertIsNone(tikhub.read_cache(path))
            good = {'code': 200, 'data': {'videos': []}}
            tikhub.save_cache(path, good)
            self.assertEqual(tikhub.read_cache(path), good)
            with self.assertRaises(RuntimeError):
                tikhub.save_cache(path, {'error': 'timeout'})
            self.assertEqual(tikhub.read_cache(path), good)

    def test_failed_detail_is_retried_and_success_is_reused(self):
        for function, folder, identity in ((collect.yt_detail, 'ytinfo', 'abc'),
                                           (collect.ig_profile, 'igprof', 'creator')):
            with self.subTest(function=function.__name__), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / folder
                target.mkdir()
                path = target / f'{identity}.json'
                path.write_text(json.dumps({'error': 'failure ' * 50}))
                brief = {'_raw': directory}
                success = {'data': {'title': 'ok'}}
                with patch.object(tikhub, 'get', return_value=success) as get:
                    function(brief, identity)
                    function(brief, identity)
                    get.assert_called_once()
                self.assertEqual(tikhub.read_cache(path), success)

    def test_failed_search_is_not_silently_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'th').mkdir()
            with patch.object(tikhub, 'get', return_value={'error': 'timeout'}):
                with self.assertRaises(RuntimeError):
                    collect.youtube_job({'_raw': directory}, 0, 'brand')
            self.assertFalse((Path(directory) / 'th/yt_0_p0.json').exists())

    def test_domestic_failed_cache_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'cn').mkdir()
            path = Path(directory) / 'cn/xhs_0_general_p1.json'
            path.write_text(json.dumps({'code': 429, 'data': {}}))
            with patch.object(tikhub, 'get', return_value={'data': {'data': {'items': []}}}) as get:
                domestic.xhs_search({'_raw': directory}, 0, 'brand', 'general', 1)
                domestic.xhs_search({'_raw': directory}, 0, 'brand', 'general', 1)
                get.assert_called_once()

    def test_comment_errors_do_not_become_empty_success(self):
        with patch.object(tikhub, 'get', return_value={'error': 'timeout'}):
            with self.assertRaises(RuntimeError):
                comments.fetch({'platform': 'YouTube', 'id': 'abc'}, 1)
        with patch.object(tikhub, 'get', return_value={'data': {'comments': []}}):
            self.assertEqual(comments.fetch({'platform': 'YouTube', 'id': 'abc'}, 1), [])

    def test_legacy_empty_comments_are_refetched_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'comments.json'
            path.write_text('[]')
            self.assertIsNone(comments.read_comment_cache(path))
            path.write_text('{"complete": true, "comments": []}')
            self.assertEqual(comments.read_comment_cache(path), [])
            path.write_text('[["hello", 10]]')
            self.assertEqual(comments.read_comment_cache(path), [['hello', 10]])


if __name__ == '__main__':
    unittest.main()
