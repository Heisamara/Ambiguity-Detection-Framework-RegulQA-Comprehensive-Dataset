"""
convert_t1_html_xml.py
Convert any HTML/XML files found under data/raw/t1_* into CSVs with a 'req_text' column.
"""
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
REQ_PAT = re.compile(r"\b(shall|should)\b", flags=re.I)

def _normalize(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", (s or "").strip())

def _extract_from_html(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    cands = []
    for sel in ["li", "p", "dd"]:
        for el in soup.select(sel):
            t = _normalize(el.get_text(" ", strip=True))
            if len(t) > 5 and REQ_PAT.search(t):
                cands.append(t)
    cands = list(dict.fromkeys(cands))
    if not cands: 
        return None
    out = path.with_suffix(".csv")
    pd.DataFrame({"document":[path.name]*len(cands),"req_text":cands}).to_csv(out, index=False)
    return out

def _extract_from_xml(path: Path):
    try:
        tree = ET.parse(path); root = tree.getroot()
    except Exception:
        return _extract_from_html(path)

    texts = []
    for el in root.iter():
        tag = (el.tag or "").lower()
        txt = _normalize(" ".join(el.itertext()))
        if len(txt) < 6: 
            continue
        if ("req" in tag or "requirement" in tag or "spec" in tag or REQ_PAT.search(txt)):
            texts.append(txt)
    uniq = []
    seen = set()
    for t in texts:
        if t in seen: continue
        seen.add(t)
        if REQ_PAT.search(t):
            uniq.append(t)
    if not uniq: return None
    out = path.with_suffix(".csv")
    pd.DataFrame({"document":[path.name]*len(uniq),"req_text":uniq}).to_csv(out, index=False)
    return out

def convert_all():
    roots = [RAW/"t1_pure", RAW/"t1_promise_exp", RAW/"t1_nasa_srs"]
    converted = []
    for r in roots:
        if not r.exists(): 
            continue
        for ext in ("*.html","*.htm","*.xml","*.xhtml"):
            for f in r.rglob(ext):
                try:
                    if f.suffix.lower() in [".html",".htm",".xhtml"]:
                        out = _extract_from_html(f)
                    else:
                        out = _extract_from_xml(f)
                    if out:
                        print("Converted:", f.name, "→", out.name)
                        converted.append(str(out))
                except Exception as e:
                    print("Skip:", f, "reason:", e)
    if not converted:
        print("No HTML/XML files converted (none found or no matches).")
    else:
        print("Done. CSVs:", len(converted))

if __name__ == "__main__":
    convert_all()
