#!/usr/bin/env python3
"""Build trader/shariah_universe.txt: US-listed stocks held by SP Funds' Shariah ETFs.

SPUS tracks the S&P 500 Shariah Industry Exclusions Index and SPTE the S&P Global
Technology Shariah index; both are screened by S&P Dow Jones Indices under AAOIFI-based
rules (business activity exclusions plus debt, cash and receivables ratio tests).
We keep holdings whose ticker is in trader/universe.txt (US-listed common stocks).

This is a screen inherited from the index provider, not a fatwa. Standard library only.
"""
import csv, io, json, os, sys, urllib.request, datetime

FUNDS = ["SPUS", "SPTE"]
URL = "https://www.sp-funds.com/wp-content/uploads/data/TidalFG_Holdings_{}.csv"
UNIVERSE = "trader/universe.txt"
OUT = "trader/shariah_universe.txt"
META = "trader/shariah_universe.json"


def fetch(fund):
    req = urllib.request.Request(URL.format(fund), headers={"User-Agent": "Mozilla/5.0 (day-trader-skill)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main():
    if not os.path.exists(UNIVERSE):
        sys.exit(f"missing {UNIVERSE}: run skills/trader-scanner/scan.py universe first")
    us = {}
    for line in open(UNIVERSE):
        if "|" in line:
            s, n = line.rstrip("\n").split("|", 1)
            us[s.strip()] = n.strip()
    picked, dates, failed = {}, {}, []
    for fund in FUNDS:
        try:
            text = fetch(fund)
        except Exception as e:  # keep going with the other fund
            failed.append(f"{fund}: {e}")
            continue
        for row in csv.DictReader(io.StringIO(text)):
            t = (row.get("StockTicker") or "").strip().upper().replace("/", ".").replace(" ", ".")
            if t in us:
                picked.setdefault(t, {"name": us[t], "funds": []})["funds"].append(fund)
                dates[fund] = (row.get("Date") or "").strip()
    if not picked:
        msg = "; ".join(failed) or "no holdings matched the US universe"
        if os.path.exists(OUT):
            print(f"Could not refresh ({msg}); keeping the existing {OUT}.")
            return 0
        sys.exit(f"Could not build the Shariah list: {msg}")
    with open(OUT, "w") as f:
        for t in sorted(picked):
            f.write(f"{t}|{picked[t]['name']}\n")
    meta = {"built": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "holdings_dates": dates,
            "funds": FUNDS, "count": len(picked), "failed": failed,
            "method": "Holdings of SP Funds Shariah ETFs (S&P Shariah indices, AAOIFI-based screens), US-listed only"}
    json.dump(meta, open(META, "w"), indent=2)
    print(f"Shariah universe: {len(picked)} US-listed stocks from {', '.join(f'{k} ({v})' for k, v in dates.items())}."
          + (f" Failed: {'; '.join(failed)}" if failed else ""))
    print(f"Wrote {OUT} (SYMBOL|Name a line) and {META}.")
    print("Screen inherited from S&P's Shariah indices; not a religious ruling. Verify with your own scholar or app if in doubt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
