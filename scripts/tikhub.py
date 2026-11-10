import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://api.tikhub.io'
PRICE_PER_CALL = 0.0011  # observed average across TikTok/IG/YouTube endpoints


def api_key():
    k = os.environ.get('TIKHUB_API_KEY', '').strip()
    if not k:
        p = os.path.expanduser('~/.config/tikhub/key')
        if os.path.exists(p):
            k = open(p).read().strip()
    if not k:
        raise SystemExit('缺少 TikHub API Key：设置环境变量 TIKHUB_API_KEY，或写入 ~/.config/tikhub/key（权限 600）。'
                         '没有 Key 时改走免费兜底方案，见 references/fallback-agent-reach.md。')
    return k


def response_error(data):
    """Check TikHub's envelope, including failures returned with HTTP 200."""
    if not isinstance(data, dict):
        return 'API response is not a JSON object'
    if data.get('error') or data.get('errors') or data.get('success') is False:
        return str(data.get('error') or data.get('errors') or data.get('message') or 'API request failed')
    for field in ('code', 'status_code'):
        code = data.get(field)
        if code is not None and str(code) not in ('0', '200'):
            return f'API {field}={code}: {data.get("message") or "request failed"}'
    if data.get('status') in ('error', 'failed', 'failure'):
        return str(data.get('message') or 'API request failed')
    if not any(isinstance(data.get(k), (dict, list)) for k in ('data', 'user_data')):
        return 'API response has no data payload'
    return None


def require_success(data):
    error = response_error(data)
    if error:
        raise RuntimeError(error)
    return data


def read_cache(path):
    """Ignore corrupt/failed legacy caches so the next run can fetch again."""
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if response_error(data) is None else None


def save_cache(path, data):
    require_success(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def get(path, params=None, retries=3):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    # TikHub's edge rejects Python's default User-Agent with 403.
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + api_key(), 'User-Agent': 'curl/8.7.1',
                                               'Accept': 'application/json'})
    err = ''
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
                error = response_error(data)
                return {'error': error} if error else data
        except urllib.error.HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code in (400, 401, 402, 403, 404, 422):
                break
        except Exception as e:  # network hiccups, timeouts
            err = str(e)
        if attempt + 1 < retries:
            time.sleep(2 + attempt * 3)
    return {'error': err}


def balance():
    d = get('/api/v1/tikhub/user/get_user_info')
    u = d.get('user_data') or d.get('data') or {}
    return u.get('balance'), d.get('error')
