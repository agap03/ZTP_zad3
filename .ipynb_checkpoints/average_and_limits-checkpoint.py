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

# zadanie z województwami:
import pandas as pd

def voivodeship_exceedances(df, voiv_map, years=(2015, 2018, 2021, 2024),norm = 15.0, station_col = "Kod stacji"):
    """
    Liczy liczbę dni w roku, w których dobowa średnia PM2.5 uśredniona 
    po wszystkich stacjach w danym województwie przekroczyła normę.
    """
    # Średnia dobowa na stację:
    df_daily = df.resample("D").mean()

    # Wyciąganie kodów stacji z kolumn
    if isinstance(df_daily.columns, pd.MultiIndex):
        station_codes = df_daily.columns.get_level_values("Kod stacji")
    else:
        station_codes = pd.Index(df_daily.columns)

    # mapowanie województw dla stacji
    voiv_for_station = station_codes.map(voiv_map)

    # Średnia dobowa po województwach
    df_voiv_daily = (df_daily.T.groupby(voiv_for_station).mean().T)

    # Zliczanie dni powyżej normy w każdym roku
    out = {}
    for y in years:
        df_y = df_voiv_daily[df_voiv_daily.index.year == y]
        out[y] = (df_y > norm).sum()  
        
    return pd.DataFrame(out).sort_index()


if __name__ == "__main__":
    pass

