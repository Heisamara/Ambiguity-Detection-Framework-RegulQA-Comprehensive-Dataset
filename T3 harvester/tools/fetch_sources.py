"""
Fetch T3 sources (PDF/HTML/TXT) listed in config/sources_t3.yaml.
Usage:
  python tools/fetch_sources.py
Optional args:
  --only NAME1,NAME2
  --skip-existing
"""
import argparse, sys, time
from pathlib import Path
import requests, yaml
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "config" / "sources_t3.yaml"
OUT_DIR = ROOT / "data" / "raw" / "t3_domain" / "downloads"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_ext(url, content_type, forced_type):
    if forced_type and forced_type != "auto":
        return {"pdf":".pdf","html":".html","txt":".txt"}.get(forced_type, "")
    if content_type:
        if "pdf" in content_type: return ".pdf"
        if "html" in content_type: return ".html"
        if "text/plain" in content_type: return ".txt"
    path = urlparse(url).path.lower()
    for ext in [".pdf",".html",".htm",".txt"]:
        if path.endswith(ext): return ".html" if ext==".htm" else ext
    return ""

def fetch_one(name, url, forced_type="auto", skip_existing=False):
    hdr = {"User-Agent":"RegulQA-Harvester/1.0"}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=hdr, timeout=90)
            r.raise_for_status()
            ctype = r.headers.get("Content-Type","").lower()
            ext = sanitize_ext(url, ctype, forced_type)
            if not ext:
                if r.content[:4] == b"%PDF": ext = ".pdf"
                else: ext = ".html"
            out = OUT_DIR / f"{name}{ext}"
            if skip_existing and out.exists():
                print(f"[skip] {name} exists:", out.name)
                return out
            out.write_bytes(r.content)
            print(f"[ok] {name} → {out}")
            return out
        except Exception as e:
            print(f"[warn] {name} attempt {attempt+1}: {e}")
            time.sleep(2*(attempt+1))
    print(f"[fail] {name}")
    return None

def main(only_names=None, skip_existing=False):
    cfg = yaml.safe_load(CONF.read_text())
    srcs = cfg.get("sources", [])
    if only_names:
        allow = set(n.strip() for n in only_names.split(","))
        srcs = [s for s in srcs if s.get("name") in allow]
    downloaded = []
    for s in srcs:
        out = fetch_one(s.get("name"), s.get("url"), s.get("type","auto"), skip_existing=skip_existing)
        if out: downloaded.append(str(out))
    (OUT_DIR / "manifest.json").write_text(__import__("json").dumps({"downloaded": downloaded}, indent=2))
    print("Downloaded:", len(downloaded))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", dest="only", default=None)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    sys.exit(main(args.only, args.skip_existing))
