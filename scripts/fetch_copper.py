#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions 用：抓取长江现货1#铜价，追加到 copper.json 的 history。
无需第三方依赖，仅用标准库。
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

URL = "https://m.ccmn.cn/cu/"
UA = ("Mozilla/5.0 (Linux; Android 13; HUAWEI) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")
CST = timezone(timedelta(hours=8))
PATH = "copper.json"


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def parse(html):
    m = re.search(
        r"<li>\s*<p>长江现货</p>\s*<p>1#铜</p>\s*<p>([\d,]+)</p>\s*"
        r"<p[^>]*>([-+]?[\d,]+)</p>\s*<p>([\d-]+)</p>", html)
    if not m:
        return None
    avg = int(m.group(1).replace(",", ""))
    chg = int(m.group(2).replace(",", ""))
    ds = m.group(3)
    mm = re.match(r"(\d{1,2})-(\d{1,2})$", ds)
    if not mm:
        return None
    now = datetime.now(CST)
    year = now.year
    mon, day = int(mm.group(1)), int(mm.group(2))
    if mon == 12 and now.month == 1:
        year -= 1
    return f"{year:04d}-{mon:02d}-{day:02d}", avg, chg


def save(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main():
    res = parse(fetch())
    if not res:
        print("PARSE_FAIL: 未匹配到长江现货1#铜")
        sys.exit(1)
    date, price, chg = res

    try:
        with open(PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    hist = data.get("history") or []

    if hist and date < hist[0][0]:
        print(f"stale: page {date} < latest {hist[0][0]}，跳过")
        return

    if hist and date == hist[0][0]:
        if hist[0][1] == price and hist[0][2] == chg:
            print(f"unchanged {date} {price} {chg:+d}")
        else:
            hist[0] = [date, price, chg]
            print(f"corrected {date} {price} {chg:+d}")
    else:
        hist.insert(0, [date, price, chg])
        print(f"added {date} {price} {chg:+d}")

    data["history"] = hist
    data["latest"] = {"date": date, "price": price, "chg": chg}
    data["updated"] = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    save(data)
    print(f"rows={len(hist)}")


if __name__ == "__main__":
    main()
