import matplotlib
from streamlit import header
matplotlib.use("Agg") # nie wyświetlaj okienek z wykresami

import pytest
import pandas as pd
import numpy as np

"""
test_ztp.py
-----------
Moduł zawierający testy dla projektu analizy jakości powietrza PM2.5.
"""

# TEST 1

from data_loader import multiindex_code_city

def test_multiindex_code_city():
    """
    Testuje funkcję multiindex_code_city().
    Test tworzy symulowane dane i metadane, a następnie wywołuje funkcję.
    Sprawdza, czy kolumny wynikowej ramki danych są MultiIndexem z odpowiednimi nazwami poziomów.
    """

    df = pd.DataFrame(
        [[1,2]],
        columns=["A1", "B1"]
    )
    df_dict = {2023: df}

    meta = pd.DataFrame({
        "Kod stacji": ["A1", "B1"],
        "Miejscowość": ["X", "Y"]
    })

    out = multiindex_code_city(df_dict, meta)

    cols = out[2023].columns
    assert isinstance(cols, pd.MultiIndex), "Błąd kolumn w multiindex_code_city"
    assert cols.names == ["Miejscowość", "Kod stacji"], "Błędne nazwy poziomów kolumn w multiindex_code_city"


# TEST 2

from average_and_limits import monthly_mean

@pytest.mark.parametrize(
    "values, expected",
    [([1, 1, 1, 1], 1.0),
     ([1, 2, 3, 4], 2.5),
     ([10, 20, 30], 20.0),
     ([5, 15, 25, 35, 45], 25.0),]
)
def test_monthly_mean(values, expected):
    """
    Testuje funkcje monthly_mean().
    
    Args:
        values (list): Lista wartości PM2.5 do uśrednienia.
        expected (float): Oczekiwana wartość średnia.
    """
    dates = pd.date_range(start="2023-01-01", periods=len(values), freq="d")
    series = pd.DataFrame({'A': values}, index=dates)
    result = monthly_mean(series)
    assert np.isclose(result['A'], expected), f"Expected {expected}, got {result['A']} in monthly_mean"


# TEST 3

from average_and_limits import find_above_norm

def test_find_above_norm():
    """Testuje funkcję find_above_norm().
    
    Test tworzy symulowane dane dla 2 dni (48 godzin). Sprawdza, czy funkcja 
    poprawnie rozpoznaje dni, w których średnia dobowa przekroczyła próg (norm).
    """
    idx = pd.date_range("2024-01-01", periods=48, freq="h")  #2 dni
    df = pd.DataFrame(
        {"S1": [20] * 48,  # zawsze powyżej normy
        "S2": [5] * 48,},   # nigdy powyżej normy
        index=idx
    )

    result = find_above_norm(df, years=[2024], sort_by=2024, norm=15)

    assert result.loc["S1", 2024] == 2
    assert result.loc["S2", 2024] == 0


# TEST 4

from visualizations import plot_average

def test_plot_average():
    """
   Testuje funkcję plot_average().
    """
    index = pd.MultiIndex.from_product(
        [[2023], range(1, 13)],
        names=["rok", "miesiąc"]
    )
    df = pd.DataFrame({"Miejscowość1": range(12)}, index=index)

    plot_average(df, years=[2023], cities=["Miejscowość1"]) # sprawdzenie czy funkcja działa bez błędów


### TESTY, które były ukryte w funkcjach

# TEST 5

from data_loader import edit_df
import calendar

def test_edit_df():
    """Testuje funkcję edit_df()."""
    dates = pd.date_range("2023-01-01", periods=365*24, freq="h")
    data = np.ones((365*24, 2))
    df = pd.DataFrame(data, columns=["A", "B"])
    df.insert(0, "Kod stacji", dates)
    header = pd.DataFrame([df.columns.tolist()], columns=df.columns)
    df = pd.concat([header, df], ignore_index=True)

    df_dict = {2023: df}

    out = edit_df(df_dict)
    edited = out[2023]
    print(edited)

    # liczba wierszy powinna = 365*24
    assert edited.shape[0] == 365*24

    # sprawdzenie liczby unikalnych dni
    num_of_days = (365 + calendar.isleap(2023)) * 24
    assert num_of_days == len(edited)

# TEST 6
from data_loader import save_combined_data

def test_save_combined_data(tmp_path):
    """Testuje funkcję scalania i zapisu danych save_combined_data().
    
    Test wykorzystuje 'tmp_path' do  zapisu pliku tymczasowego. Sprawdza poprawność rozmiarów oraz 
    unikalność dni w scalonym indeksie.
    
    Args:
        tmp_path: Ścieżka do katalogu tymczasowego dostarczona przez pytest.
    """
    # dwa df
    idx1 = pd.date_range("2023-01-01", periods=24, freq="h")
    df1 = pd.DataFrame(np.ones((24,2)), index=idx1, columns=["A","B"])

    idx2 = pd.date_range("2024-01-01", periods=48, freq="h")
    df2 = pd.DataFrame(np.ones((48,2)), index=idx2, columns=["A","B"])

    df_dict = {2023: df1, 2024: df2}

    filename = tmp_path / "combined.csv"
    combined = save_combined_data(df_dict, filename)

    # sprawdzenie rozmiarów
    sum = 0
    for df in df_dict.values():
        sum += df.shape[0]
    assert combined.shape[0] == sum

    # sprawdzenie liczby unikalnych dni
    unique_days = combined.index.normalize().unique()
    assert len(unique_days) == 3  # 1 dzień w 2023 i 2 dni w 2024
