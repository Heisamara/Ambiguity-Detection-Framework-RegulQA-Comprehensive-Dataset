# RegulQA – Phase 1

A clean, simple scaffold to build **RegulQA‑Ambig v1** with three tiers:
- **T1**: Public academic datasets (PURE, PROMISE_exp/Promise+, NASA Trick SRS page)
- **T2**: Synthetic regulated sentences (ISO 26262, DO‑178C, IEC 62304–style templates)
- **T3**: Domain SRS/manuals (public repos: automotive/medical/aerospace …)

## Quick Start
1. Open `notebooks/01_setup_t1.ipynb` → download & normalize T1 → produces `data/processed/t1_annotation_pool.csv`
2. (Optional) `notebooks/02_t2_synthetic.ipynb` → generate synthetic regulated sentences → `data/raw/t2_synthetic/*.csv`
3. (Optional) `notebooks/03_t3_collect.ipynb` → add public SRS/manuals you find → `data/raw/t3_domain/*.csv`
4. Run `notebooks/04_export_labelstudio.ipynb` → unify all tiers to `data/processed/regulqa_ambig_pool.csv`
5. Import **Label Studio** config from `annotation/labelstudio/regulqa_label_config.xml` and start annotating.

## Annotation Schema (CSV/JSONL)
`id, source, tier, sector, document, req_text, ambig_presence, ambig_type, reg_clause, severity, notes`

- `sector`: `automotive`, `medical`, `aerospace`, `rail`, `finance`, `defense`, `energy`, `general`
- `ambig_presence`: `clear` | `ambiguous`
- `ambig_type`: `lexical` | `syntactic` | `semantic` (use `;` for multi)
- `reg_clause`: `ISO_29148` | `ISO_26262` | `DO_178C` | `IEC_62304` | `NASA_SWEHB` | `NA`
- `severity`: `low` | `medium` | `high`

## Notes
- Use `config/sector_overrides.yaml` to force sector tags per file/document if heuristics are off.
- Everything is modular—feel free to delete T2/T3 if you don’t need them.
