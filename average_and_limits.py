import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# obliczanie średnich miesięcznych dla każdego roku i stacji
def monthly_mean(df):
    df_copy = df.copy()
    df_copy['miesiąc'] = df_copy.index.month
    df_copy['rok'] = df_copy.index.year
    df_copy = df_copy.set_index(['rok', 'miesiąc'])

    # średnia miesięczna
    monthly_mean = df_copy.groupby(level=['rok', 'miesiąc']).mean()
    return monthly_mean


# dni z przekroczeniem normy PM2.5 dla każdej stacji i roku
def find_above_norm(df, years, sort_by, norm=15):
    norms = {}

    df_days = df.copy().sort_index()
    df_days['data'] = pd.to_datetime(df_days.index.date)
    df_days = df_days.set_index('data')
    df_max = df_days.groupby(['data']).mean()

    for year in years:
        df_station = df_max[df_max.index.year == year] # dane dla danego roku
        norms[year] = np.array((df_station>norm).sum().values) # liczba dni przekroczenia normy dla każdej stacji

    norms_df = pd.DataFrame(norms, index=df_max.columns)
    norms_df = norms_df.sort_values(by=sort_by) # sortowanie według liczby dni przekroczenia normy w 2024
    return norms_df


if __name__ == "__main__":
    pass