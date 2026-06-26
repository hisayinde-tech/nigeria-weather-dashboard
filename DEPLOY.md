# Deploying the Weather Dashboard (Streamlit Community Cloud — free)

This folder is a ready-to-deploy website. Streamlit Community Cloud hosts
Python data apps like this one for free, permanently, with a public URL
(e.g. `https://your-app-name.streamlit.app`).

## What's in this folder
```
weather_site/
├── app.py                  <- the website
├── requirements.txt        <- Python packages it needs
├── preprocess.py           <- regenerates data/by_state/*.csv if you update the raw data
├── .streamlit/config.toml  <- server settings
└── data/
    ├── states_meta.json
    ├── tables/              <- table1-table11 from the pipeline
    └── by_state/            <- one lean CSV per state (26 states currently)
```

## Step 1 — Put this folder on GitHub
1. Go to https://github.com and sign in (or create a free account).
2. Click the **+** in the top right → **New repository**. Name it
   e.g. `nigeria-weather-dashboard`. Keep it **Public**. Click **Create repository**.
3. On the new repo page, click **uploading an existing file**.
4. Drag in every file and folder from this `weather_site/` folder
   (including the `data/` folder and the hidden `.streamlit/` folder —
   if your file browser hides dot-folders, use GitHub Desktop or the
   `git` command line instead, see note below).
5. Click **Commit changes**.

   *Command-line alternative (handles hidden folders automatically):*
   ```bash
   cd weather_site
   git init
   git add -A
   git commit -m "Initial weather dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/nigeria-weather-dashboard.git
   git push -u origin main
   ```

## Step 2 — Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with your GitHub account.
2. Click **New app**.
3. Pick the repository you just created, branch `main`, and main file
   path `app.py`.
4. Click **Deploy**. The first build takes 1-3 minutes while it installs
   `requirements.txt`.
5. You'll get a live public URL — share it with anyone, no login needed
   to view it.

That's it — it's free, stays live continuously, and redeploys
automatically every time you push a change to GitHub.

## Updating the data later
If you re-download the missing states and re-run the pipeline:
1. Replace the CSVs in `data/tables/` with the new `table10`/`table11`
   (and others if changed).
2. Replace `all_states_combined.csv` and re-run `python preprocess.py`
   locally to regenerate `data/by_state/*.csv` and `states_meta.json`.
3. Commit and push the updated `data/` folder to GitHub — Streamlit
   Cloud redeploys automatically within a minute or two.

## Alternative hosting
If you outgrow the free tier or want a custom domain, the same `app.py`
runs unchanged on **Render.com** (free web service tier, add a
`Procfile` with `web: streamlit run app.py --server.port=$PORT
--server.address=0.0.0.0`) or **Railway**. Streamlit Cloud is the
easiest starting point and is sufficient for this dashboard's traffic
and data size (~20 MB).
