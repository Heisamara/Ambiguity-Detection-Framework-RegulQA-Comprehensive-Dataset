# T3 Harvester

1) Configure sources in `config/sources_t3.yaml`.
2) Download:
   ```bash
   python tools/fetch_sources.py --skip-existing
   ```
3) Extract to CSV:
   ```bash
   python tools/extract_to_csv.py
   ```
Outputs:
- Downloads → `data/raw/t3_domain/downloads/*`
- Per-source CSV → `data/raw/t3_domain/harvested/*.csv`
- Merged CSV → `data/raw/t3_domain/ALL_t3_harvested.csv`

Then rebuild the unified pool with your usual notebook (01_setup_t1) or `src/data/clean_all.py`.
