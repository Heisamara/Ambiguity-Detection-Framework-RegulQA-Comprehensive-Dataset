"""
T1 download helpers (robust to different file types on Zenodo).
"""
from pathlib import Path
import requests, zipfile, io, re
import pandas as pd
from bs4 import BeautifulSoup

DATA = Path(__file__).resolve().parents[2] / "data" / "raw"

PURE_RECORD_PAGE = "https://zenodo.org/records/1414117"        # PURE
PROMISE_PLUS_PAGE = "https://zenodo.org/records/12805484"       # Promise+ (PROMISE_exp expansion)
TRICK_SRS_URL = "https://nasa.github.io/trick/documentation/software_requirements_specification/SRS.html"

def _download(url: str, timeout=120) -> bytes:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content

def _download_first_matching_from_record(page_url: str, exts=("zip",)):
    """
    Parse a Zenodo record HTML page and download the first file whose href ends with
    one of the given extensions (case-insensitive). Returns (filename, bytes).
    """
    html = requests.get(page_url, timeout=60)
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")
    # File rows are anchor tags in the "Files" section
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # normalize to absolute
        if href.startswith("//"):
            href_norm = "https:" + href
        elif href.startswith("/"):
            href_norm = "https://zenodo.org" + href
        else:
            href_norm = href

        # skip non-file links
        if "/files/" not in href_norm:
            continue

        # extension check
        for ext in exts:
            if href_norm.lower().endswith(f".{ext}") or f".{ext}?" in href_norm.lower():
                # add ?download=1 if missing (zenodo supports both)
                if "download=1" not in href_norm:
                    sep = "&" if "?" in href_norm else "?"
                    href_norm = href_norm + f"{sep}download=1"
                content = _download(href_norm)
                # try to get a sane filename from the URL tail
                fname = href_norm.split("/files/")[-1].split("?")[0]
                return fname, content

    raise RuntimeError(f"No file with extensions {exts} found on {page_url}")

def download_pure(outdir=DATA / "t1_pure"):
    outdir.mkdir(parents=True, exist_ok=True)
    print("Resolving PURE (requirements.zip or requirements-xml.zip)…")
    # PURE offers .zip files → prefer zips
    fname, content = _download_first_matching_from_record(PURE_RECORD_PAGE, exts=("zip",))
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(outdir)
    print(f"PURE → {outdir} (extracted from {fname})")

def download_promise_plus(outdir=DATA / "t1_promise_exp"):
    outdir.mkdir(parents=True, exist_ok=True)
    print("Resolving Promise+ (may be .arff/.xlsx)…")
    # Promise+ provides .arff and .xlsx (no zip); accept either
    fname, content = _download_first_matching_from_record(PROMISE_PLUS_PAGE, exts=("arff","xlsx","csv","zip"))
    (outdir / fname).write_bytes(content)
    print(f"Promise+ → {outdir/fname}")

def scrape_trick_srs(outdir=DATA / "t1_nasa_srs"):
    import re
    from bs4 import BeautifulSoup
    outdir.mkdir(parents=True, exist_ok=True)
    print("Scraping NASA Trick SRS…")
    html = _download(TRICK_SRS_URL).decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    lines = []
    for li in soup.select("li"):
        t = re.sub(r"\s+", " ", li.get_text(" ", strip=True))
        if re.search(r"\bshall\b", t, flags=re.I):
            lines.append(t)
    pd.DataFrame({"document": "TRICK_SRS", "req_text": lines}).to_csv(outdir / "trick_srs_requirements.csv", index=False)
    print(f"NASA Trick SRS → {outdir/'trick_srs_requirements.csv'} (rows={len(lines)})")

if __name__ == "__main__":
    download_pure(); download_promise_plus(); scrape_trick_srs()