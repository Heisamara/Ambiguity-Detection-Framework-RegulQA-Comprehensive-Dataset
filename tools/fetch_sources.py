"""
Fetch T3 sources (PDF/HTML/TXT) listed in config/sources_t3.yaml.

Usage:
  python tools/fetch_sources.py
Options:
  --only NAME1,NAME2        Fetch only listed sources
  --skip-existing           Skip already downloaded files
  --ca-bundle PATH          Custom CA bundle (e.g., from certifi)
  --insecure                Disable SSL verification (NOT recommended)
"""
import argparse, sys, time
from pathlib import Path
import requests, yaml, certifi
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
        if path.endswith(ext):
            return ".html" if ext==".htm" else ext
    return ""

def fetch_one(name, url, forced_type="auto", skip_existing=False, verify=True):
    """Download one source file with retries and SSL control."""
    hdr = {"User-Agent":"RegulQA-Harvester/1.0"}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=hdr, timeout=90, verify=verify)
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

def main(only_names=None, skip_existing=False, ca_bundle=None, insecure=False):
    """Main entry point."""
    try:
        cfg = yaml.safe_load(CONF.read_text())
    except Exception as e:
        print("Error loading config:", e)
        return 1

    verify = False if insecure else (ca_bundle or certifi.where())
    srcs = cfg.get("sources", [])
    if only_names:
        allow = set(n.strip() for n in only_names.split(","))
        srcs = [s for s in srcs if s.get("name") in allow]

    downloaded = []
    for s in srcs:
        out = fetch_one(
            s.get("name"),
            s.get("url"),
            s.get("type", "auto"),
            skip_existing=skip_existing,
            verify=verify
        )
        if out:
            downloaded.append(str(out))

    # Write manifest
    import json
    (OUT_DIR / "manifest.json").write_text(json.dumps({"downloaded": downloaded}, indent=2))
    print("Downloaded:", len(downloaded))
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", dest="only", default=None)
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--ca-bundle", default=None, help="Path to a CA bundle (e.g., from certifi)")
    ap.add_argument("--insecure", action="store_true", help="Disable TLS verification (not recommended)")
    args = ap.parse_args()
    sys.exit(main(args.only, args.skip_existing, args.ca_bundle, args.insecure))