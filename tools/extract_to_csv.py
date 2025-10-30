"""
Extract requirement-like sentences from T3 downloads into CSVs.
Usage:
  python tools/extract_to_csv.py [--min-len 15] [--max-len 500] [--regex "..."]
"""
import argparse, re, csv
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "data" / "raw" / "t3_domain" / "downloads"
OUT = ROOT / "data" / "raw" / "t3_domain" / "harvested"
OUT.mkdir(parents=True, exist_ok=True)

def sentences_from_text(text):
    import re
    parts = re.split(r'(?<=[.?!])\s+(?=[A-Z0-9])', text)
    return [re.sub(r'\s+', ' ', p).strip() for p in parts if p and len(p.strip())>0]

def from_pdf(path):
    import fitz
    doc = fitz.open(path)
    for page in doc:
        txt = page.get_text("text")
        for s in sentences_from_text(txt):
            yield s

def from_html(path):
    from bs4 import BeautifulSoup
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    tags = soup.find_all(["li","p"]) or soup.find_all(text=True)
    for tag in tags:
        t = tag.get_text(" ", strip=True) if hasattr(tag, "get_text") else str(tag)
        t = ' '.join(t.split())
        if t:
            yield t

def from_txt(path):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    for s in sentences_from_text(txt):
        yield s

def process_file(path, rx_req, min_len, max_len):
    ext = path.suffix.lower()
    if ext == ".pdf":
        gen = from_pdf(path)
    elif ext in (".html",".htm"):
        gen = from_html(path)
    else:
        gen = from_txt(path)
    keep = []
    for s in gen:
        if min_len <= len(s) <= max_len and rx_req.search(s):
            keep.append(s)
    # dedup preserve order
    seen = set(); dedup = []
    for s in keep:
        if s not in seen:
            seen.add(s); dedup.append(s)
    return dedup

def main(min_len=15, max_len=500, regex=r"\b(shall|should|must)\b"):
    rx_req = re.compile(regex, re.I)
    summary = []
    for path in sorted(DL.glob("*")):
        if path.suffix.lower() not in (".pdf",".html",".htm",".txt"):
            continue
        rows = process_file(path, rx_req, min_len, max_len)
        if not rows:
            print("[empty]", path.name); continue
        out = OUT / f"{path.stem}.csv"
        with out.open("w", newline='', encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["document","req_text"])
            for s in rows:
                w.writerow([path.name, s])
        print("[ok]", path.name, "→", out.name, "rows:", len(rows))
        summary.append({"file": path.name, "rows": len(rows)})
    # merged
    all_csvs = list(OUT.glob("*.csv"))
    if all_csvs:
        frames = [pd.read_csv(c) for c in all_csvs]
        merged = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["req_text"])
        merged.to_csv(OUT.parent / "ALL_t3_harvested.csv", index=False)
        print("ALL_t3_harvested.csv rows:", len(merged))
    import json
    (OUT / "manifest.json").write_text(json.dumps(summary, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-len", type=int, default=15)
    ap.add_argument("--max-len", type=int, default=500)
    ap.add_argument("--regex", type=str, default=r"\b(shall|should|must)\b")
    args = ap.parse_args()
    main(args.min_len, args.max_len, args.regex)
