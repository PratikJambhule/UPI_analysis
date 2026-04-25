"""
Time-series forecasting for UPI transaction volumes.
Uses ARIMA and seasonal decomposition (Prophet optional).

Models:
1. ARIMA(1,1,1) — baseline for trending data with differencing
2. Seasonal decomposition — multiplicative model (trend × seasonal × residual)
3. Prophet (if installed) — robust, interpretable forecasting with Indian holidays
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.info("Prophet not installed — using ARIMA + seasonal decomposition only")

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose


class UPIForecaster:
    """Forecasts future UPI transaction volumes using ARIMA (and optionally Prophet)."""

    def __init__(self):
        self.silver_path = Path("data/silver")
        self.output_path = Path("data/gold/exports")
        self.forecast_horizon = 12  # months ahead

    def run(self) -> bool:
        try:
            df = self._load_data()
            if df is None or len(df) < 6:
                logger.warning("Insufficient data for forecasting")
                return True

            prophet_forecast = self._run_prophet(df)
            arima_forecast = self._run_arima(df)
            decomposition = self._seasonal_decomposition(df)

            self._save_forecasts(df, prophet_forecast, arima_forecast, decomposition)
            return True

        except Exception as e:
            logger.exception(f"Forecasting failed: {e}")
            return False

    def _load_data(self) -> pd.DataFrame:
        """Load monthly UPI volume data."""
        npci_file = self.silver_path / "transactions" / "npci_monthly_volumes.parquet"

        if not npci_file.exists():
            logger.warning("NPCI monthly volumes not found")
            return None

        df = pd.read_parquet(npci_file)
        df = df[["date", "transaction_volume_billions"]].dropna()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def _run_prophet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run Prophet forecasting model."""
        if not PROPHET_AVAILABLE:
            logger.info("Skipping Prophet (not installed)")
            return pd.DataFrame()

        prophet_df = df.rename(columns={
            "date": "ds",
            "transaction_volume_billions": "y",
        })

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_mode="multiplicative",
        )
        model.add_country_holidays(country_name="IN")
        model.fit(prophet_df)

        future = model.make_future_dataframe(
            periods=self.forecast_horizon, freq="MS"
        )
        forecast = model.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result.columns = [
            "date", "forecast_volume_bn",
            "forecast_lower_bn", "forecast_upper_bn",
        ]
        result["is_forecast"] = result["date"] > df["date"].max()

        logger.info(f"Prophet forecast: {self.forecast_horizon} months ahead")
        logger.info(f"  Predicted volume: "
                    f"{result.iloc[-1]['forecast_volume_bn']:.2f} billion transactions")
        return result

    def _run_arima(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run ARIMA(1,1,1) model."""
        y = df.set_index("date")["transaction_volume_billions"]
        y.index = pd.DatetimeIndex(y.index).to_period("M")

        try:
            model = ARIMA(y, order=(1, 1, 1))
            fitted = model.fit()

            fc = fitted.get_forecast(steps=self.forecast_horizon)
            forecast_vals = fc.predicted_mean
            conf_int = fc.conf_int()

            last_date = df["date"].max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=self.forecast_horizon,
                freq="MS",
            )

            result = pd.DataFrame({
                "date": future_dates,
                "arima_forecast_bn": forecast_vals.values,
                "arima_lower_bn": conf_int.iloc[:, 0].values,
                "arima_upper_bn": conf_int.iloc[:, 1].values,
            })

            logger.info(f"ARIMA(1,1,1) forecast complete | AIC: {fitted.aic:.2f}")
            logger.info(f"  Predicted volume in {self.forecast_horizon} months: "
                        f"{result.iloc[-1]['arima_forecast_bn']:.2f} billion")
            return result

        except Exception as e:
            logger.warning(f"ARIMA failed: {e}")
            return pd.DataFrame()

    def _seasonal_decomposition(self, df: pd.DataFrame) -> dict:
        """Decompose time series into trend, seasonal, and residual."""
        y = df.set_index("date")["transaction_volume_billions"]
        y.index = pd.DatetimeIndex(y.index)

        if len(y) < 24:
            logger.warning("Insufficient data for seasonal decomposition (need 24+ months)")
            return {}

        try:
            decomposition = seasonal_decompose(y, model="multiplicative", period=12)

            # Identify strongest seasonal months
            seasonal_series = decomposition.seasonal.dropna()
            seasonal_avg = seasonal_series.groupby(seasonal_series.index.month).mean()
            peak_month = seasonal_avg.idxmax()
            trough_month = seasonal_avg.idxmin()

            month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                           7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

            logger.info(f"Seasonal analysis:")
            logger.info(f"  Peak month: {month_names.get(peak_month, peak_month)} "
                        f"(factor: {seasonal_avg[peak_month]:.3f})")
            logger.info(f"  Trough month: {month_names.get(trough_month, trough_month)} "
                        f"(factor: {seasonal_avg[trough_month]:.3f})")

            return {
                "seasonal_factors": seasonal_avg.to_dict(),
                "peak_month": int(peak_month),
                "trough_month": int(trough_month),
            }

        except Exception as e:
            logger.warning(f"Seasonal decomposition failed: {e}")
            return {}

    def _build_forecast_combined(self, silver_df: pd.DataFrame, arima_fc: pd.DataFrame) -> pd.DataFrame:
        """Combine silver actuals with ARIMA forecasts into a unified table.

        Schema: date (datetime), volume_bn (float), is_forecast (bool)
        """
        # Silver side: cast date, select & rename, flag as actual
        actuals = silver_df[["date", "transaction_volume_billions"]].copy()
        actuals["date"] = pd.to_datetime(actuals["date"])
        actuals = actuals.rename(columns={"transaction_volume_billions": "volume_bn"})
        actuals["is_forecast"] = False

        # ARIMA side: select & rename, flag as forecast
        forecasts = arima_fc[["date", "arima_forecast_bn"]].copy()
        forecasts["date"] = pd.to_datetime(forecasts["date"])
        forecasts = forecasts.rename(columns={"arima_forecast_bn": "volume_bn"})
        forecasts["is_forecast"] = True

        combined = pd.concat([actuals, forecasts], ignore_index=True)
        combined = combined.sort_values("date").reset_index(drop=True)
        return combined

    def _save_forecasts(self, silver_df, prophet_fc, arima_fc, decomposition):
        """Save forecast results."""
        self.output_path.mkdir(parents=True, exist_ok=True)

        if not prophet_fc.empty:
            prophet_fc.to_parquet(
                self.output_path / "prophet_forecast.parquet", index=False
            )
            logger.success("Prophet forecast saved")

        if not arima_fc.empty:
            arima_fc.to_parquet(
                self.output_path / "arima_forecast.parquet", index=False
            )
            logger.success("ARIMA forecast saved")

            # Build and save forecast_combined (actuals + ARIMA forecasts)
            combined = self._build_forecast_combined(silver_df, arima_fc)
            combined.to_parquet(
                self.output_path / "forecast_combined.parquet", index=False
            )
            logger.success(f"forecast_combined saved — {len(combined)} rows "
                           f"(actuals: {(~combined['is_forecast']).sum()}, "
                           f"forecasts: {combined['is_forecast'].sum()})")

        if decomposition:
            seasonal_df = pd.DataFrame({
                "month": list(decomposition["seasonal_factors"].keys()),
                "seasonal_factor": list(decomposition["seasonal_factors"].values()),
            })
            seasonal_df.to_parquet(
                self.output_path / "seasonal_factors.parquet", index=False
            )
            logger.success("Seasonal factors saved")

        logger.success("Forecasts saved to Gold layer")
