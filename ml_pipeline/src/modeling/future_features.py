import numpy as np
import pandas as pd 
from scipy.interpolate import interp1d

from modeling.config import FEATURES

LAGS = (1, 2, 3, 6, 12)
ROLLING_WINDOWS = (3, 6, 12)
KEY_COLUMNS = ['bairro', 'categoria']

def find_last_month(
        df:          pd.DataFrame,
        data_column: str,
    ) -> float:

    last_data = df[data_column].max()

    return float(last_data.month)

def check_month(
        df: pd.DataFrame,
        data_column: str,
    ) -> bool:

    return find_last_month(df, data_column) == 12.0 

def find_target_date(
        df: pd.DataFrame,
        data_column: str,
    ) -> pd.Timestamp:

    last_date = pd.Timestamp(df[data_column].max())
    last_month = int(find_last_month(df, data_column))

    target_month = last_month + 1
    target_year = last_date.year 

    if target_month == 13:
        target_month = 1
        target_year += 1

    return pd.Timestamp(
        year=target_year,
        month=target_month,
        day=1,
    )

def linear_extrapolation(
        df: pd.DataFrame,
        target_column: str,
        target_year: int,
    ) -> pd.DataFrame:

    target = df.loc[
        df['ano'].isin([2010, 2022]),
        ['bairro', 'ano', target_column]
    ].pivot_table(
        index='bairro',
        columns='ano',
        values=target_column,
        aggfunc='first',
    )

    source_values = target[[2010, 2022]].to_numpy(dtype=float)

    extrapolate = interp1d(
        [2010, 2022],
        source_values,
        axis=1,
        kind='linear'
    )

    target_estimated = extrapolate(target_year)

    return pd.DataFrame({
        'bairro': target.index,
        target_column: target_estimated,
    }).reset_index(drop=True)

def evaluate_extrapolation_columns(
        df: pd.DataFrame,
        data_column: str, 
        target_date: pd.Timestamp,
        columns: list[str],
    ) -> pd.DataFrame:

    target_year = target_date.year 

    if not check_month(df, data_column):
        return (
            df.loc[
                df[data_column].dt.year == target_year,
                ['bairro', *columns],
            ]
            .drop_duplicates('bairro')
            .reset_index(drop=True)
        )

    extrapolated_columns = []

    for target_column in columns:
        values = linear_extrapolation(
            df=df,
            target_column=target_column,
            target_year=target_year
        )

        extrapolated_columns.append(
            values.set_index('bairro')
        )

    return (
        pd.concat(extrapolated_columns, axis=1)
        .reset_index(drop=False)
    )

def fourier_features(
        df:          pd.DataFrame,
        data_column: str, 
        harmonics:   int = 2,
        period:      int = 12,
    ) -> dict[str, float]:

    target_month = int(find_last_month(df, data_column)) % period + 1

    features = {}

    for harmonic in range(1, harmonics + 1):
        angle = 2 * np.pi * harmonic * target_month / float(period)

        features[f'mes_sin_{harmonic}'] = np.sin(angle)
        features[f'mes_cos_{harmonic}'] = np.cos(angle)

    return features 

def lag_features(
      df: pd.DataFrame,
      data_column: str,
      target_date: pd.Timestamp,
    ) -> pd.DataFrame:
      
    future = (
        df[KEY_COLUMNS]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    for lag in LAGS:
        lag_date = target_date - pd.DateOffset(months=lag)
        feature_name = f"log1p_lag_{lag}"

        lag_values = (
            df.loc[
                df[data_column].eq(lag_date),
                [*KEY_COLUMNS, "y"],
            ]
            .rename(columns={"y": feature_name})
        )

        lag_values[feature_name] = np.log1p(
            lag_values[feature_name]
        )

        future = future.merge(
            lag_values,
            on=KEY_COLUMNS,
            how='left',
            validate='one_to_one',
        )

    return future

def rolling_mean_features(
    df: pd.DataFrame,
    data_column: str,
    target_date: pd.Timestamp,
    ) -> pd.DataFrame:
    features = []

    for window in ROLLING_WINDOWS:
        start_date = target_date - pd.DateOffset(months=window)
        feature_name = f"log1p_media_{window}"

        mean_values = (
            df.loc[
                df[data_column].between(
                    start_date,
                    target_date,
                    inclusive="left",
                )
            ]
            .groupby(KEY_COLUMNS)["y"]
            .mean()
            .map(np.log1p)
            .rename(feature_name)
        )

        features.append(mean_values)

    return pd.concat(features, axis=1).reset_index()


def calculate_target_tempo(
        df: pd.DataFrame,
        data_column: str,
    ) -> int:
    last_date = df[data_column].max()

    last_tempo = df.loc[
        df[data_column].eq(last_date),
        'tempo'
    ].iloc[0]

    return int(last_tempo) + 1

def build_future_features(
        df: pd.DataFrame,
        data_column: str = 'data',
    ) -> pd.DataFrame:
    df = df.copy()
    df[data_column] = pd.to_datetime(df[data_column])

    #########
    df['ano'] = df[data_column].dt.year 

    target_date = find_target_date(
        df=df,
        data_column=data_column
    )

    future = (
        df[KEY_COLUMNS]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    lags = lag_features(
        df=df,
        data_column=data_column,
        target_date=target_date,
    )

    future = future.merge(
        lags,
        on=KEY_COLUMNS,
        how='left',
        validate='one_to_one',
    )

    rolling_means = rolling_mean_features(
        df=df,
        data_column=data_column,
        target_date=target_date
    )

    future = future.merge(
        rolling_means,
        on=KEY_COLUMNS,
        how='left',
        validate='one_to_one'
    )

    socioeconomic = evaluate_extrapolation_columns(
        df=df,
        data_column=data_column,
        target_date=target_date,
        columns=['iqv', 'log_pop'],
    )

    future = future.merge(
        socioeconomic,
        on='bairro',
        how='left',
        validate='many_to_one',
    )

    future['tempo'] = calculate_target_tempo(
        df=df,
        data_column=data_column
    )

    future = future.assign(
        **fourier_features(
            df=df,
            data_column=data_column,
            harmonics=2,
            period=12,
        )
    )

    future['data'] = target_date

    return (
        future.loc[:, ["data", *FEATURES]]
        .sort_values(KEY_COLUMNS)
        .reset_index(drop=True)
        )
