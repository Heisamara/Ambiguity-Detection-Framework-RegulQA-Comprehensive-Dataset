"""
T1 download helpers.
Note: Run locally with internet access.
"""
from pathlib import Path
import requests, zipfile, io, pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data" / "raw"

# Verify these URLs before running locally (Zenodo often stable):
PURE_ZIP = "https://zenodo.org/records/7118517/files/PURE-dataset.zip?download=1"
PROMISE_PLUS_ZIP = "https://zenodo.org/records/12805484/files/promise_plus_dataset.zip?download=1"
TRICK_SRS_URL = "https://nasa.github.io/trick/documentation/software_requirements_specification/SRS.html"

def _download(url: str) -> bytes:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content

def download_pure(outdir=DATA / "t1_pure"):
    outdir.mkdir(parents=True, exist_ok=True)
    content = _download(PURE_ZIP)
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(outdir)
    print("PURE →", outdir)

def download_promise_plus(outdir=DATA / "t1_promise_exp"):
    outdir.mkdir(parents=True, exist_ok=True)
    content = _download(PROMISE_PLUS_ZIP)
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(outdir)
    print("Promise+ →", outdir)

def scrape_trick_srs(outdir=DATA / "t1_nasa_srs"):
    import re
    from bs4 import BeautifulSoup
    outdir.mkdir(parents=True, exist_ok=True)
    html = _download(TRICK_SRS_URL).decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    lines = []
    for li in soup.select("li"):
        t = re.sub(r"\s+", " ", li.get_text(" ", strip=True))
        if re.search(r"\bshall\b", t, flags=re.I):
            lines.append(t)
    pd.DataFrame({"document":["TRICK_SRS"]*len(lines),"req_text":lines}).to_csv(outdir/"trick_srs_requirements.csv", index=False)
    print("NASA Trick SRS →", outdir/"trick_srs_requirements.csv")

if __name__ == "__main__":
    download_pure(); download_promise_plus(); scrape_trick_srs()
