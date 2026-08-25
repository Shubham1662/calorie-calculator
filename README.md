# 🍛 Calorie Calculator

A lightweight, mobile-friendly calorie tracker for Indian foods. Built with
Python + Streamlit. Data lives in a Google Sheet when deployed (free,
persistent) and in local CSV files when run without credentials — no server
database, no login.

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

> ⚠️ **Persistence note:** Streamlit Cloud's filesystem is ephemeral — anything
> written to local CSVs there is wiped on restart/redeploy. That's why the
> deployed app must use the Google Sheets backend below.

## Persistent storage with Google Sheets (required on Streamlit Cloud)

One-time setup, ~10 minutes, entirely free:

1. **Create the sheet.** In [Google Sheets](https://sheets.google.com), create a
   blank spreadsheet (name it e.g. `calorie-tracker`). Copy its URL.
2. **Create a Google Cloud project.** Go to
   [console.cloud.google.com](https://console.cloud.google.com), create a
   project (any name).
3. **Enable APIs.** In *APIs & Services → Library*, enable **Google Sheets API**
   and **Google Drive API**.
4. **Get credentials** using ONE of the two routes below.
5. **Add secrets.** In Streamlit Cloud → your app → **Settings → Secrets**,
   paste the matching variant from `.streamlit/secrets.toml.example` with your
   values, including your sheet URL as `spreadsheet`. (For local testing you
   can instead copy it to `.streamlit/secrets.toml`, which is gitignored.)
6. **Reboot the app.** On first load it creates the `foods`, `consumption_log`
   and `settings` worksheets and seeds the 281-item food database
   automatically. From then on, all entries persist in your sheet — which you
   can also open and edit directly.

### Route 1 — OAuth (use this if "service account key creation is disabled")

Signs in as your own Google account; no key file, so the
`iam.disableServiceAccountKeyCreation` policy can't block it.

1. *APIs & Services → OAuth consent screen*: choose **External**, fill in the
   app name and your email, save. Then **Publish app** so its status is
   **In production** (in "Testing" the token dies after 7 days).
2. *APIs & Services → Credentials → Create Credentials → OAuth client ID* →
   type **Desktop app** → create, then **Download JSON**.
3. On your PC run:
   ```bash
   pip install google-auth-oauthlib
   python scripts/get_google_token.py path/to/client_secret_xxx.json
   ```
   A browser opens — sign in, click **Advanced → Continue** past the
   "unverified app" warning (it's your own app), and allow access. The script
   prints a ready-to-paste `[gsheets]` secrets block.
4. No sheet sharing needed — it's your own account.

### Route 2 — service-account key (if your account allows JSON key creation)

1. *APIs & Services → Credentials → Create Credentials → Service account*.
   Name it (e.g. `calorie-app`), skip the optional role/access steps, **Done**.
2. Open the service account → *Keys → Add key → Create new key → JSON*.
3. **Share the sheet**: in your spreadsheet click **Share** and add the service
   account's email (`client_email` in the JSON) as **Editor**.

Without a `[gsheets]` secret the app transparently falls back to local CSVs in
`data/`, so `streamlit run app.py` still works with zero setup.

## Project layout

```
app.py                   # Streamlit UI (3 tabs: Log / Trends / Foods)
src/data_store.py        # storage layer: Google Sheets or CSV/JSON fallback
src/calculations.py      # calorie math
src/analytics.py         # 14-day trend + chart
data/foods.csv           # food database — edit freely
data/consumption_log.csv # your history (created on first entry)
```

Full architecture, schemas, data flow, and limitations: [ARCHITECTURE.md](ARCHITECTURE.md).
