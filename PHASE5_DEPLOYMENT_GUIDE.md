# Phase 5 — GitHub Publication Guide

## 1. Validate locally

From the repository root:

```bash
python -m pip install -r requirements.txt
cd model_06_datacenter_capital_forecasting
python run_model.py
python run_phase2.py
python run_phase3.py
python run_phase4.py
python -m unittest discover -s tests -p 'test_*.py'
cd ..
```

## 2. Review the change set

```bash
git status
git diff -- README.md requirements.txt .gitignore
git diff --stat
```

Confirm that no credentials, private data, virtual environments, notebook checkpoints, or machine-specific files are present.

## 3. Commit and push

```bash
git add README.md requirements.txt PHASE5_DEPLOYMENT_GUIDE.md docs model_06_datacenter_capital_forecasting
git commit -m "Expand portfolio with datacenter capital forecasting engine"
git push origin main
```

## 4. Enable GitHub Pages

In GitHub:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select branch **main** and folder **/docs**.
4. Save.
5. Verify the published URL after deployment.

Expected URL if the owner is `dapaah` and the repository is `compute-economics-portfolio`:

`https://dapaah.github.io/compute-economics-portfolio/`

## 5. Deploy Streamlit

In Streamlit Community Cloud:

1. Create a new app from the GitHub repository.
2. Select branch `main`.
3. Set the entry point to:
   `model_06_datacenter_capital_forecasting/dashboard/app.py`
4. Deploy and copy the public app URL.
5. Add that URL to the root README under **Start here**.

## 6. Public verification checklist

- Root README renders correctly.
- GitHub Pages dashboard loads in a signed-out browser.
- Streamlit app loads without local files or secrets.
- All dashboard tabs and charts render.
- Executive-brief and source links resolve.
- Models 1–5 remain unchanged and downloadable.
- All 14 Model 6 tests pass from a clean environment.
