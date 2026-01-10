import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# obliczanie średnich miesięcznych dla każdego roku i stacji
def monthly_mean(df):
    monthly_mean = df.groupby([df.index.year, df.index.month]).mean()
    monthly_mean.index.names = ['rok', 'miesiąc']  # nadajemy nazwy poziomom indeksu
    return monthly_mean


# dni z przekroczeniem normy PM2.5 dla każdej stacji i roku
def find_above_norm(df, years, sort_by, norm=15):
    norms = {}

    df_group = df.groupby(df.index.date).mean() 

    for year in years:
        df_station = df_group[pd.to_datetime(df_group.index).year == year] # dane dla danego roku
        norms[year] = np.array((df_station>norm).sum().values) # liczba dni przekroczenia normy dla każdej stacji

    norms_df = pd.DataFrame(norms, index=df_group.columns)
    norms_df = norms_df.sort_values(by=sort_by) # sortowanie według liczby dni przekroczenia normy w 2024
    return norms_df


if __name__ == "__main__":
    pass