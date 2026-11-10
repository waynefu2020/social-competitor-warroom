"""YouTube Long-Window Sponsor Fingerprint Radar (TikHub + yt-dlp Hybrid Enrichment).

Distilled from real-world 1-year YouTube sponsorship audits (e.g., Granola, Manus, Wispr Flow, Gamma, Genspark, Plaud).
- Searches both explicit sponsor disclosures ("sponsored by <brand>") and custom tracking shortlinks
  (e.g., "go.granola.ai", "manus.im/redeem", "ref.wisprflow.ai", "gamma.yt.link").
- Automatically enriches missing publish_date / view_count / channel_follower_count via local `yt-dlp`.
- Filters out "not sponsored / unsponsored" disclaimers, homonym noise, and separates "固定工具栏外链/联盟" from core paid sponsorships.
- Uses standard Chinese placement terminology: 「口播植入」 vs 「专场测评/教程」 (never "中插").
"""
import argparse
import concurrent.futures as cf
import csv
import datetime
import json
import math
import os
import re
import statistics
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tikhub  # noqa: E402
from normalize import NEGATED_SIGNAL as NEG_SPON, signal_text  # noqa: E402

FOOTER_TOOL_LIST = re.compile(r"my top tools|tools i use|favorite tools|affiliate links", re.I)


def parse_num(s):
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        return int(s) if not isinstance(s, bool) and math.isfinite(s) and s >= 0 else None
    m = re.search(r"(-?[\d.,]+)\s*([KMB]?)", str(s))
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", "")) * {"K": 1e3, "M": 1e6, "B": 1e9, "": 1}[m.group(2)]
        return int(value) if math.isfinite(value) and value >= 0 else None
    except ValueError:
        return None


def first_count(*values):
    """Use the first known count, including a genuine zero."""
    for value in values:
        count = parse_num(value)
        if count is not None:
            return count
    return None


def search_query(q, pages):
    tok = None
    found = []
    for _ in range(pages):
        params = dict(search_query=q, order_by="this_year")
        if tok:
            params["continuation_token"] = tok
        d = tikhub.require_success(tikhub.get("/api/v1/youtube/web/search_video", params))
        vids = (d.get("data") or {}).get("videos") or []
        found.extend(vids)
        tok = (d.get("data") or {}).get("continuation_token")
        if not vids or not tok:
            break
    return q, found


def ytdlp_enrich(vid, out_dir):
    p = os.path.join(out_dir, "ytdlp", f"{vid}.json")
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return json.load(open(p, encoding="utf-8"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        r = subprocess.run(
            ["yt-dlp", "--no-update", "-j", "--skip-download", f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if r.stdout:
            data = json.loads(r.stdout)
            json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return data
    except Exception:
        pass
    return {}


def detect_placement(brand, title, chapters):
    if re.search(re.escape(brand), title or "", re.I):
        return "专场测评/教程"
    if re.search(r"sponsor", chapters or "", re.I):
        return "口播植入(含Sponsor章节)"
    return "口播植入/简介植入"


def main():
    ap = argparse.ArgumentParser(description="YouTube Long-Window Sponsor Fingerprint Radar")
    ap.add_argument("--brand", required=True, help="Brand name, e.g. Granola")
    ap.add_argument("--queries", nargs="+", required=True, help="Sponsor fingerprint queries")
    ap.add_argument("--paid-regex", required=True, help="Regex for explicit paid sponsorship")
    ap.add_argument("--link-regex", required=True, help="Regex for custom tracking shortlinks/codes")
    ap.add_argument("--noise-regex", default="", help="Regex to exclude homonym noise")
    ap.add_argument("--official-handles", nargs="*", default=[], help="Official handles to exclude")
    ap.add_argument("--pages", type=int, default=6, help="Pages per query")
    ap.add_argument("--days", type=int, default=365, help="Lookback window in days (default 365)")
    ap.add_argument("--out-dir", required=True, help="Output directory")
    ap.add_argument("--enrich-missing", action="store_true", help="Use yt-dlp to fill missing dates/views")
    args = ap.parse_args()

    os.makedirs(os.path.join(args.out_dir, "ytinfo"), exist_ok=True)
    rx_paid = re.compile(args.paid_regex, re.I)
    rx_link = re.compile(args.link_regex, re.I)
    rx_noise = re.compile(args.noise_regex, re.I) if args.noise_regex else None
    off_set = {h.lower() for h in args.official_handles}

    cands = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(search_query, q, args.pages) for q in args.queries]
        for fut in cf.as_completed(futs):
            q, items = fut.result()
            print(f"[Search] {q}: {len(items)} hits", flush=True)
            for v in items:
                vid = v.get("video_id")
                if vid:
                    cands.setdefault(vid, v)

    def fetch_info(vid):
        p = os.path.join(args.out_dir, "ytinfo", f"{vid}.json")
        if tikhub.read_cache(p) is None:
            d = tikhub.get("/api/v1/youtube/web_v2/get_video_info", dict(video_id=vid, language_code="en"))
            tikhub.save_cache(p, d)

    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        list(ex.map(fetch_info, cands.keys()))

    now = datetime.date.today()
    date_start = (now - datetime.timedelta(days=args.days)).isoformat()
    date_end = now.isoformat()

    rows = []
    for vid in cands:
        d = (json.load(open(os.path.join(args.out_dir, "ytinfo", f"{vid}.json"), encoding="utf-8")).get("data")) or {}
        pub = (d.get("publish_date") or "")[:10]
        views = parse_num(d.get("view_count"))
        y = {}
        if args.enrich_missing and (not pub or views is None):
            y = ytdlp_enrich(vid, args.out_dir)
            if not pub and y.get("upload_date"):
                ud = y["upload_date"]
                pub = f"{ud[:4]}-{ud[4:6]}-{ud[6:8]}"
            if views is None:
                views = parse_num(y.get("view_count"))

        if not pub or not (date_start <= pub <= date_end):
            continue
        author = d.get("author") or y.get("channel") or ""
        handle = d.get("channel_handle") or y.get("uploader_id") or ""
        if handle.lower() in off_set or author.lower() in off_set:
            continue
        title = d.get("title") or y.get("title") or ""
        desc = d.get("description") or y.get("description") or ""
        if rx_noise and rx_noise.search(f"{title} {desc}"):
            continue

        chapters = " ".join(c.get("title", "") for c in (d.get("chapters") or y.get("chapters") or []))
        clean_text = signal_text(f"{title}\n{desc}\n{chapters}")
        # group(0) keeps complete evidence even when caller regex has groups.
        m_paid = [m.group(0) for m in rx_paid.finditer(clean_text)]
        m_link = [m.group(0) for m in rx_link.finditer(clean_text)]
        if not m_paid and not m_link:
            continue

        if m_paid:
            tier = "明确付费赞助"
        elif FOOTER_TOOL_LIST.search(desc):
            tier = "固定工具栏外链/联盟"
        else:
            tier = "专属短链/兑换码（合作待核实）"

        ev = list(dict.fromkeys([re.sub(r"\s+", " ", str(x)).strip() for x in (m_paid + m_link)]))
        rows.append(
            {
                "品牌": args.brand,
                "合作层级": tier,
                "植入形态": detect_placement(args.brand, title, chapters),
                "发布日期": pub,
                "频道名称": author,
                "频道Handle": handle,
                "粉丝数": first_count(d.get("subscriber_count_text"), y.get("channel_follower_count")),
                "播放量": views,
                "点赞数": first_count(d.get("like_count"), y.get("like_count")),
                "评论数": first_count(d.get("comment_count"), y.get("comment_count")),
                "视频标题": title,
                "合作信号证据": " | ".join(ev[:4]),
                "视频链接": f"https://www.youtube.com/watch?v={vid}",
            }
        )

    rows.sort(key=lambda x: x["播放量"] or 0, reverse=True)
    csv_path = os.path.join(args.out_dir, f"{args.brand.lower()}_youtube_paid.csv")
    if rows:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    core = [x for x in rows if x["合作层级"] == "明确付费赞助"]
    c_views = [x["播放量"] for x in core if x["播放量"] is not None]
    summary = {
        "brand": args.brand,
        "total_matched": len(rows),
        "core_videos": len(core),
        "core_unique_channels": len({x["频道名称"] for x in core}),
        "core_median_views": int(statistics.median(c_views)) if c_views else None,
        "core_views_n": len(c_views),
        "core_views_unit": "播放",
        "core_total_views": sum(c_views) if c_views else None,
        "tier_breakdown": dict(Counter(x["合作层级"] for x in rows)),
        "placement_breakdown": dict(Counter(x["植入形态"] for x in core)),
    }
    json.dump(summary, open(os.path.join(args.out_dir, f"{args.brand.lower()}_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
