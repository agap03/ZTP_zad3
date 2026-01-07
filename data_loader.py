import pandas as pd
import requests
import zipfile
import io, os
import re
import calendar



# funkcja do ściągania podanego archiwum
def download_gios_archive(year, gios_id, filename, gios_archive_url):
    # Pobranie archiwum ZIP do pamięci
    url = f"{gios_archive_url}{gios_id}"
    response = requests.get(url)
    response.raise_for_status()  # jeśli błąd HTTP, zatrzymaj
    
    # Otwórz zip w pamięci
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # znajdź właściwy plik z PM2.5
        if not filename:
            print(f"Błąd: nie znaleziono {filename}.")
        else:
            # wczytaj plik do pandas
            with z.open(filename) as f:
                try:
                    df = pd.read_excel(f, header=None)
                except Exception as e:
                    print(f"Błąd przy wczytywaniu {year}: {e}")
    return df



# usuwanie niepotrzebnych wierszy
# ujednolicanie struktury danych

def edit_df(df, year):
    df_edited = df.copy()
    pattern_date = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}") # wzorzec daty i godziny do usuwania niepotrzebnych wierszy
    rows_to_drop = []
    header_row_id = None

    for i in range(len(df_edited)):
        
        row = df_edited.iloc[i, 0]
        if row == 'Kod stacji': # znalezienie indeksu z kodami stacji (aby ustawić jako nagłówki kolumn)
            header_row_id = i
        elif not pattern_date.match(str(row)):
            rows_to_drop.append(i)


    df_edited.drop(labels=rows_to_drop, axis=0, inplace=True) # usuń niepotrzebne wiersze
    df_edited.columns = df.loc[header_row_id] # ustaw nagłówki kolumn
    df_edited.drop(labels=[header_row_id], axis=0, inplace=True) # usuń wiersz z nagłówkami
    df_edited.reset_index(drop=True, inplace=True) # zresetuj indeksy
    df_edited['Kod stacji'] = pd.to_datetime(df_edited['Kod stacji']) # zmień typ kolumny z kodami stacji na datetime
    df_edited.set_index('Kod stacji', inplace=True) # ustaw kolumnę z kodami stacji jako indeks


    # sprawdzenie liczby dni w roku po edycji
    num_of_days = (365 + calendar.isleap(year)) * 24
    if num_of_days == len(df_edited):
        print(f"Liczba dni w {year} się zgadza")
    else: 
        print("Liczba dni się nie zgadza")
    print()

    return df_edited



# pobieranie metadanych stacji pomiarowych

def download_gios_metadata(url):
    response = requests.get(url)
    response.raise_for_status()
    with io.BytesIO(response.content) as f:
        try:
            gios_metadata = pd.read_excel(f, header=0)
            return gios_metadata
        except Exception as e:
            print(f"Błąd przy wczytywaniu metadanych: {e}")
            return None




# stworzenie słownika mapującego stare kody stacji na nowe
def create_code_map(gios_metadata, df_list):
    codes = gios_metadata[['Stary Kod stacji \n(o ile inny od aktualnego)', 'Kod stacji']]
    codes = codes.dropna()

    code_map = {}
    for old_codes, new_code in zip(codes['Stary Kod stacji \n(o ile inny od aktualnego)'], codes['Kod stacji']):
        for old_code in str(old_codes).split(','): # niektóre stare kody są rozdzielone przecinkami
            code_map[old_code.strip()] = new_code

    for df in df_list:
        df.rename(columns=code_map, inplace=True)

    return code_map, df_list


# wspólne kolumny
def find_common_columns(df_list):
    common_cols = set(df_list[0].columns)
    for df in df_list[1:]:
        common_cols = common_cols.intersection(set(df.columns))

    common_cols = list(common_cols)

    # wybierz tylko wspólne kolumny
    for i in range(len(df_list)):
        df_list[i] = df_list[i][common_cols]

    # sprawdzenie liczby kolumn po ujednoliceniu
    col_len = len(common_cols)
    for df in df_list:
        if df.shape[1] != col_len:
            print("Liczba kolumn się nie zgadza")
            return None, None
    
    print(f"Liczba kolumn się zgadza: {col_len}")
    return common_cols, df_list


# dodanie nazw miejscowości jako multiindexu kolumn

def multiindex_code_city(df_list, metadata, columns):

    cities = metadata[['Kod stacji', 'Miejscowość']] # nazwy miejscowości
    cities = cities.dropna()
    cities.drop_duplicates(inplace=True)

    first_level = cities['Kod stacji']
    second_level = cities['Miejscowość']

    # wybieramy tylko kolumny, które istnieją
    mask = first_level.isin(columns)
    first_level = first_level[mask]
    second_level = second_level[mask]

    first_level = list(first_level)
    second_level = list(second_level)

    # tworzymy MultiIndex
    for df in df_list:
        df.columns = pd.MultiIndex.from_arrays([second_level, first_level])

    return df_list


# korekta indeksu daty i godziny (przesunięcie rekordów o 00:00:00 na poprzedni dzień)
def correct_datetime_index(df):
    df.index = df.index - pd.to_timedelta((df.index.hour == 0).astype(int), unit='d')
    return df

# scalenie danych z poszczególnych lat i zapis do pliku CSV
def save_combined_data(df_list, filename):

    df_all = pd.concat(df_list, ignore_index=False)
    df_all.to_csv(filename, index=False)

    # sprawdzenie liczby unikalnych dni w każdym roku

    count_days = df_all.index.normalize().unique() # normalizacja do daty (bez godziny)
    count_days = pd.Series(count_days)
    count_days = count_days.groupby(count_days.dt.year).count()
    print(count_days)

    # sprawdzenie rozmiarów

    for df in df_list:
        print(df.shape)
  
    print(df_all.shape)

    sum = 0
    for df in df_list:
        sum += df.shape[0]
    print(sum)

    return df_all

if __name__ == "__main__":
    pass