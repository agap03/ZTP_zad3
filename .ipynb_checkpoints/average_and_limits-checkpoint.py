import numpy as np
import pandas as pd

"""
average_and_limits.py
--------------
Moduł służy do obliczania średnich czasowych wartości PM2.5 oraz zliczania liczby dni z przekroczeniem normy
jakości powietrza. 
"""


def monthly_mean(df):
    """
    Funkcja oblicza średnie mieięczne dla każdego roku i stacji 

    Args:
        df (pd.DataFrame) : DataFrame z indexem DatetimeIndex oraz scalonymi danymi ze wszystkich badanych lat i stacji. 

    Returns:
        pd.DataFrame: Obiekt z MultiIndexem ['rok', 'miesiąc'] zawierający średnie miesięczne dla każdej stacji.
    """
    monthly_mean = df.groupby([df.index.year, df.index.month]).mean()
    monthly_mean.index.names = ['rok', 'miesiąc']  # nadajemy nazwy poziomom indeksu
    return monthly_mean


def find_above_norm(df, years, sort_by, norm=15):
    """
    Funkcja dla każdej stacji i roku liczy liczbę dni, w których średnie dobowe stężenie PM2.5 przekroczyło normę.  

    Funkcja najpierw sprowadza dane do średnich dobowych, a następnie zlicza wystąpienia przekroczeń 
    dla każdej stacji w poszczególnych latach.

    Args:
        df (pd.DataFrame): Ramka danych z pomiarami (DatetimeIndex).
        years (list[int]): Lista lat, dla których ma zostać przeprowadzona analiza.
        sort_by (int):  Rok według którego zostawnie posortowana tabela wynikowa
        norm (int, optional): Dobowa norma PM2.5. Domyślnie 15 µg/m³.

    Returns:
        pd.dataFrame : Wiersze to miejscowości i kody stacji, a kolumny to lata z liczbą dni przekroczenia normy  
    """
    
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

# zadanie z województwami:

PREFIX_TO_VOIVODESHIP = {
    "Zp": "zachodniopomorskie",
    "Pd": "podlaskie",
    "Mz": "mazowieckie",
    "Pm": "pomorskie",
    "Kp": "kujawsko-pomorskie",
    "Ds": "dolnośląskie",
    "Op": "opolskie",
    "Sl": "śląskie",
    "Ld": "łódzkie",
    "Wm": "warmińsko-mazurskie",
    "Lu": "lubuskie",
    "Pk": "podkarpackie",
    "Mp": "małopolskie",
    "Wp": "wielkopolskie",
    "Lb": "lubelskie",
}

def voivodeship_exceedances(
    norms_df: pd.DataFrame,
    station_col: str = "Kod stacji",
    years=(2015, 2018, 2021, 2024),
) -> pd.DataFrame:
    """
    Zwraca liczbę dni z przekroczeniem normy PM2.5 zagregowaną po województwach.
    """
    df = norms_df.reset_index().copy()

    # województwo z prefiksu kodu stacji
    df["Województwo"] = (
        df[station_col].astype(str).str[:2].map(PREFIX_TO_VOIVODESHIP)
    )
    years = [y for y in years if y in df.columns]

    # agregacja: suma dni przekroczeń po województwach
    voiv_df = (
        df.dropna(subset=["Województwo"])
          .groupby("Województwo", as_index=False)[years]
          .sum()
    )

    return voiv_df
