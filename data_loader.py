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


# funkcja do ściągania wielu archiwów
def download_gios_archives(years, gios_ids, filenames, gios_archive_url=None):

    if gios_archive_url is None:
        gios_archive_url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"

    data = {}
    for year in years:
        df = download_gios_archive(year, gios_ids[year], filenames[year], gios_archive_url)
        data[year] = df
    
    return data



# usuwanie niepotrzebnych wierszy
# ujednolicanie struktury danych
def edit_df(df_dict):

    out = {} 

    for year, df in df_dict.items():
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
        df_edited['Kod stacji'] = df_edited['Kod stacji'].dt.floor('h') # zaokrąglij do najbliższej godziny w dół
        df_edited.set_index('Kod stacji', inplace=True) # ustaw kolumnę z kodami stacji jako indeks
        # Zamiana przecinka na kropkę i konwersja wszystkich kolumn na liczby
        for col in df_edited.columns:
            df_edited[col] = pd.to_numeric(df_edited[col].astype(str).str.replace(',', '.'), errors='coerce')
    
        out[year] = df_edited

    return out

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
def create_code_map(gios_metadata, df_dict):
    codes = gios_metadata[['Stary Kod stacji \n(o ile inny od aktualnego)', 'Kod stacji']]
    codes = codes.dropna()

    # rozdzielamy stare kody przecinkami
    codes['Stary_Kod_List'] = codes['Stary Kod stacji \n(o ile inny od aktualnego)'].str.split(',')

    # każdy stary kod w osobnym wierszu
    codes_long = codes.explode('Stary_Kod_List')
    codes_long['Stary_Kod_List'] = codes_long['Stary_Kod_List'].str.strip()


    code_map = dict(zip(codes_long['Stary_Kod_List'], codes_long['Kod stacji']))

    for df in df_dict.values():
        df.rename(columns=code_map, inplace=True)
    return df_dict



# dodanie nazw miejscowości jako multiindexu kolumn
def multiindex_code_city(df_dict, metadata):

    meta = (
        metadata[['Kod stacji', 'Miejscowość']]
        .dropna()
        .drop_duplicates()
        .set_index('Kod stacji')
    )

    out = {}

    for year, df in df_dict.items():
        # zachowujemy kolejność kolumn DF
        cities = meta.loc[df.columns, 'Miejscowość']

        df_new = df.copy()
        df_new.columns = pd.MultiIndex.from_arrays(
            [cities, df.columns],
            names=['Miejscowość', 'Kod stacji']
        )

        out[year] = df_new

    return out


# korekta indeksu daty i godziny (przesunięcie rekordów o 00:00:00 n 23:59:59 poprzedniego dnia)
def correct_datetime_index(df_dict):
    for year, df in df_dict.items():
        df.index = df.index - pd.to_timedelta((df.index.hour == 0).astype(int), unit='s')
    return df_dict


# scalenie danych z poszczególnych lat i zapis do pliku CSV
def save_combined_data(df_dict, filename):

    df_list = list(df_dict.values())

    df_all = pd.concat(df_list, join='inner', ignore_index=False)
    df_all.to_csv(filename, index=True)

    # sprawdzenie liczby unikalnych dni w każdym roku

    count_days = df_all.index.normalize().unique() # normalizacja do daty (bez godziny)
    count_days = pd.Series(count_days)
    count_days = count_days.groupby(count_days.dt.year).count()

    return df_all

if __name__ == "__main__":
    pass