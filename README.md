# AGOI™ ESG Platform — MVP

**Africa Green Opportunity Index** — an interactive ESG decision-support dashboard
that scores all 54 African countries 0–100 across six weighted pillars, with full
data provenance and confidence flags.

Built for **Natural Eco Capital**. This is the Phase 1–5 MVP described in the
*AGOI™ Technical Development Manual v2.0*: a faithful implementation of the
six-pillar scoring engine, served as a Streamlit web app.

---

## What it does

- **Continental ranking** of 54 African countries by AGOI score, coloured by opportunity band.
- **Country profile** — pillar radar, scores, and the full **audit trail** behind every number.
- **Africa map** — choropleth by AGOI score or data coverage.
- **Pillar comparison** — radar overlay of up to five countries.
- **Scenario tool** — adjust pillar weights and watch the ranking re-rank instantly (Tier 1 weight sensitivity).
- **Export centre** — download scores, the audit trail, and an Excel workbook; full methodology published in-app.

### Data modes (chosen in the sidebar)
| Mode | What it shows |
|------|---------------|
| **Mixed** (default) | Live World Bank data, with any gaps filled by clearly-flagged demo values. |
| **Live** | World Bank only. |
| **Demo** | Synthetic, deterministic sample data — always labelled, never presented as real. |

Every value carries a confidence flag (`measured` / `interpolated` / `proxy` / `default`)
and each country gets a **data-coverage score** so real data is always distinguishable
from fallbacks.

---

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Then open http://localhost:8501

---

## Deploy free on Streamlit Community Cloud

1. **Create a GitHub repo** and push this folder to it:
   ```bash
   git init
   git add .
   git commit -m "AGOI ESG Platform MVP"
   git branch -M main
   git remote add origin https://github.com/<your-username>/agoi-platform.git
   git push -u origin main
   ```
2. Go to **https://share.streamlit.io** and sign in with GitHub (free).
3. Click **New app** → pick your repo → set:
   - **Branch:** `main`
   - **Main file path:** `app/streamlit_app.py`
4. Click **Deploy**. First build takes a few minutes. You get a public URL like
   `https://<your-app>.streamlit.app` that you can share with the board / clients.

> Streamlit Cloud has open internet access, so **Live / Mixed modes will pull real
> World Bank data** once deployed (unlike a restricted local sandbox).

### Alternative free host: Render
- New → **Web Service** → connect repo.
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`

---

## Project structure

```
agoi-platform/
  agoi/                      # the scoring engine (importable package)
    config.py                # weights, bands, thresholds  (tune here, not in code)
    registry.py              # 54 countries (ISO alpha-3) + indicator registry
    pipeline.py              # orchestration: live → mix → demo fallback
    data_sources/
      worldbank.py           # live World Bank API pull (keyed on ISO alpha-3)
      demo.py                # deterministic, flagged synthetic data
    scoring/
      normalization.py       # direction → winsorize → min-max (0–100)
      engine.py              # pillar aggregation + AGOI + audit table + coverage
  app/
    streamlit_app.py         # home / continental ranking
    _shared.py               # shared data loader + helpers
    pages/
      1_Country_Profile.py
      2_Africa_Map.py
      3_Pillar_Comparison.py
      4_Scenario_Tool.py
      5_Export_and_Methodology.py
  requirements.txt
  README.md
```

---

## Methodology (summary)

Each indicator flows through one consistent pipeline:

```
raw value → direction alignment → winsorization (5th/95th pct)
          → min-max scale to 0–100 → weighted pillar aggregation
          → weighted AGOI score → opportunity band
```

**Pillar weights:** Sectoral 25% · Policy 20% · Finance 20% · Bankability 15% ·
Resilience 10% · Inclusive 10%.

**Bands:** Core Green (80–100) · Growth Green (60–80) · Emerging (40–60) ·
High-Friction (20–40) · Red (0–20).

Full methodology, indicator registry and band readings are published on the
**Export & methodology** page inside the app.

---

## Data sources

| Source | Module | Feeds | Access |
|--------|--------|-------|--------|
| World Bank (WDI / WGI) | `data_sources/worldbank.py` | All six pillars | Free public JSON API, keyed on ISO alpha-3 |
| AfDB project/lending | `data_sources/afdb.py` | **Bankability pillar** | IATI Datastore (AfDB reporting-org `46002`), aggregated per country |
| Demo (synthetic) | `data_sources/demo.py` | Gap-fill / offline | Deterministic, always flagged `default` |

### ⚠️ One-time AfDB verification (do this after first deploy)

The AfDB connector targets the public **IATI Datastore**, but the live response
shape can vary and could not be reached from the build sandbox. After deploying:

1. Open the app on Streamlit Cloud in **Live** or **Mixed** mode.
2. Go to **Country profile → Nigeria → Audit trail** and look for the row
   *"AfDB active project commitments (proxy)"*.
   - If its **Source** reads `AfDB (IATI Datastore)` → live AfDB data is flowing. ✅
   - If it reads `DEMO (synthetic)` → the live pull returned nothing; the platform
     safely fell back. Paste me a sample of what the IATI endpoint returns and I'll
     adjust the parser in `_parse_activities()` (the single place that needs it).

AfDB values are flagged `confidence="proxy"` because project commitments are an
indirect signal of bankability, not a direct market measure.

## Notes & roadmap

- This MVP implements the **sovereign** scoring layer. The NGX corporate ESG module,
  public validation portal, monitoring/alerting engine and the AGOF™ fund layer are
  specified in the *AGOI™ ESG Platform — Full Product Specification v1.0* and are the
  next build phases.
- Some World Bank governance indicator codes (rule of law, regulatory quality) should
  be validated against the current WB catalogue; the engine degrades gracefully if a
  series returns empty.
- The scoring engine is in `agoi/` and is independent of the UI — it can be reused by
  a future FastAPI backend without change.

© Natural Eco Capital. Internal MVP build.
