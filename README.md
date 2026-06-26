# Nigeria Weather Forecast Dashboard

A searchable weather dashboard built on top of the Kwara State University
PSO Feature Selection + Random Forest weather forecasting project.

Search any state to see:
- Its 14-day precipitation forecast (interactive chart)
- Historical trends (yearly, monthly, seasonal, last 90 days)
- The model's accuracy for that state (R², MAE, RMSE) vs. other states
- A map of tomorrow's forecast across the country

## Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL it prints (usually http://localhost:8501).

## Deploy it live (free)
See [DEPLOY.md](DEPLOY.md) for step-by-step instructions using Streamlit
Community Cloud.

## Data coverage
26 of 37 states/FCT currently have weather data (the rest were missing
from the NASA POWER download — see the **About** tab in the app for
details on how to add them later).
