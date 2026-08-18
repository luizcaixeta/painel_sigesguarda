from sklearn.model_selection import TimeSeriesSplit
import pandas as pd

def make_time_series_split(
        df: pd.DataFrame,
        date_col: str = "data",
        validation_start: str | pd.Timestamp = "2017-01-01",
    ) -> TimeSeriesSplit:

    dates = pd.to_datetime(df[date_col])
    validation_start = pd.Timestamp(validation_start)

    months = dates.dt.to_period("M")
    rows_per_month = months.value_counts(sort=False)

    validation_month = validation_start.to_period("M")
    n_splits = months[months >= validation_month].nunique()

    return TimeSeriesSplit(
        n_splits=n_splits,
        test_size = int(rows_per_month.iloc[0]),
        gap=0,
    )
