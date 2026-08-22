# 🍛 Calorie Calculator

A lightweight, mobile-friendly calorie tracker for Indian foods. Built with
Python + Streamlit, stores everything in CSV files — no database, no login.

**Features**

- 281-item Indian food database (veg + non-veg) with per-serving calories
- Log foods per day with quantity; per-food and daily totals computed automatically
- Configurable daily calorie target with remaining-calories display
- 14-day intake trend chart with target line and over/under coloring
- Add your own foods from the app (or edit `data/foods.csv` directly)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. To use it from your phone on the same Wi-Fi, run
`streamlit run app.py --server.address 0.0.0.0` and open
`http://<your-pc-ip>:8501` on the phone, then "Add to Home Screen".

## Deploy (GitHub + Streamlit Community Cloud)

```bash
git init            # already done if you cloned this repo
git add .
git commit -m "Calorie calculator"
gh repo create calorie-calculator --private --source . --push   # or create the repo on github.com and push
```

Then:

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → select the repo and branch → main file path `app.py` → **Deploy**.
3. Every `git push` auto-redeploys.

> ⚠️ **Persistence note:** Streamlit Cloud's filesystem is ephemeral — entries
> logged on the cloud instance are lost on restart/redeploy. For reliable
> history, run the app locally (data lives in `data/` on your disk) and use the
> cloud instance casually, or periodically commit `data/consumption_log.csv`.
> See `ARCHITECTURE.md` §10 for details.

## Project layout

```
app.py                   # Streamlit UI (3 tabs: Log / Trends / Foods)
src/data_store.py        # all CSV/JSON file I/O
src/calculations.py      # calorie math
src/analytics.py         # 14-day trend + chart
data/foods.csv           # food database — edit freely
data/consumption_log.csv # your history (created on first entry)
```

Full architecture, schemas, data flow, and limitations: [ARCHITECTURE.md](ARCHITECTURE.md).
