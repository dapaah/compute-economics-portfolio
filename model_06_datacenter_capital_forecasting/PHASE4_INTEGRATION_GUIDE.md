# Phase 4 Integration Guide

1. Copy the Phase 4 patch over the Phase 3 local repository.
2. Install the two added presentation dependencies:
   ```bash
   pip install -r model_06_datacenter_capital_forecasting/requirements.txt
   ```
3. Regenerate all model outputs:
   ```bash
   cd model_06_datacenter_capital_forecasting
   python run_model.py
   python run_phase2.py
   python run_phase3.py
   python run_phase4.py
   pytest -q
   ```
4. Open `data/outputs/dashboard/executive_dashboard.html` in a browser.
5. Run the interactive application with:
   ```bash
   streamlit run dashboard/app.py
   ```
6. Review the generated executive brief and KPI JSON before committing.

Do not push until the root README links and relative paths have been reviewed in the live repository context.
