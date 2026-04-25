"""Page modules for the Streamlit dashboard tabs."""

import importlib

overview = importlib.import_module("src.visualization.pages.00_overview")
executive_summary = importlib.import_module("src.visualization.pages.01_executive_summary")
market_share = importlib.import_module("src.visualization.pages.02_market_share")
geographic_insights = importlib.import_module("src.visualization.pages.03_geographic_insights")
forecasting = importlib.import_module("src.visualization.pages.04_forecasting")
cash_displacement = importlib.import_module("src.visualization.pages.05_cash_displacement")
growth_trends = importlib.import_module("src.visualization.pages.06_growth_trends")
app_dynamics = importlib.import_module("src.visualization.pages.07_app_dynamics")
district_deep_dive = importlib.import_module("src.visualization.pages.08_district_deep_dive")
users_devices = importlib.import_module("src.visualization.pages.09_users_devices")
methodology = importlib.import_module("src.visualization.pages.10_methodology")