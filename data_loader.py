import pandas as pd
import requests
import zipfile
import io
import re

"""
data_loader.py
--------------
Moduł obsłukuje wczytywanie danych i przygotowuje je do dalszej analizy 

Funkcje:
- download_gios_archive: pobiera archiwum ZIP i wczytuje arkusz Exel 
- download_multiple_gios_archives: zarządza wczytywaniem danych  
- edit_df: czyści dane i ujednolica format w rankach danych 
- download_gios_metadata: pobiera metadane z opisem i lokalizacją stacji, wyczytuje plik exel
- create_code_map: mapuje nowe kody stacji do nowych i koryguje stare kody w ramkach danych
- multiindex_code_city: Tworzy multiindex z nazwami miejscowości nad kodami stacji 
- correct_datetime_index: Korekta godziny - przesunięcie z 00:00 na 23:59:59 poprzedniego dnia 
- save_combined_data: Łączy ramki danych w jeden DataFrame i zapisuje do pliku CSV
"""

def download_gios_archive(year, gios_id, filename, gios_archive_url):
    """
    Funkcja pobiera archiwum ZIP dla podanego roku z GIOŚ, rozpakowuje je w pamięci i wczytuje arkusz Excel. 
    
    Args:
        year (list[int]): rok dla którgo pobierane są dane
        gios_id (str): id zaspobu 
        filename (str): nazwa pliku (.xlsx) wewnątrz pobranego archiwum ZIP.
        gios_archive_url (str): bazowy adres URL punktu końcowego archiwum GIOŚ
    
    Returns:
        pd.DataFrame: ramka danych z pomiarami godzinowymi wartości PM2.5 dla danego roku
        lub None w przypadku błedu 
    
    Rises:
        requests.exceptions.HTTPError: Jeśli wystąpi problem z połączeniem lub zasób nie istnieje.

    """
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


def download_multiple_gios_archives(years, gios_ids, filenames, gios_archive_url=None):
    """
    Jest to funkcja nadrzędna, która zarządza procesem wczytywania danych dla wielu lat.
    
    Args: 
        years (list[int]): Lista lat do pobrania
        gios_id (dict): Słownik przypisujący identyfikator pliku w bazie GIOŚ (wartość) do roku (klucz)
        file_names (dict): Słownik przypisujący nazwę pliku .xlsx (wartość) do roku (klucz)
        gios_archive_url (str, optional): Podstawowy adres URL API GIOŚ. Domyślna wartość to None
    
    Returns:
        dict : Słownik mapujący ramki danych do każdego roku {rok: df}.
    """
    if gios_archive_url is None:
        gios_archive_url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"

    data = {}
    for year in years:
        df = download_gios_archive(year, gios_ids[year], filenames[year], gios_archive_url)
        data[year] = df
    
    return data




def edit_df(df_dict):
    """
    Funkcja usuwa niepotrzebne wiersze i ujednolica strukturę danych
    Proces obejmuje usuwanie wierszy opisowych, zaokrąglanie czasu do pełnych godzin (w dół)
    i ustawienie daty jako indeksu. 
    
    Args:
        df_dict (dict): słownik mapujący surowe dane w ramkach danych do roku {rok: df}
    
    Returns:
        dict : słownik mapujący ramki danych z oczyszczonymi danymi i DatetimeIndex do roku {rok: df}.
    """
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


def download_gios_metadata(url):
    """
    Funkcja pobiera plik Excel z metadanymi stacji pomiarowych (lokalizacje, kody)
    
    Args:
        url (str): Adres URL do pliku Excel z metadanymi.
    
    Returns:
        pd.DataFrame: Ramka danych z metadanymi lub None w przypadku błędu.
    
    Rises: 
        requests.exceptions.HTTPError: Jeśli wystąpi problem z połączeniem lub zasób nie istnieje.
    """
    response = requests.get(url)
    response.raise_for_status()
    with io.BytesIO(response.content) as f:
        try:
            gios_metadata = pd.read_excel(f, header=0)
            return gios_metadata
        except Exception as e:
            print(f"Błąd przy wczytywaniu metadanych: {e}")
            return None


def create_code_map(gios_metadata, df_dict):
    """
    Mapuje nowe kody stacji do starych i aktualizuje nazwy kolumn w ramkach danych.

    Dba o spójność identyfikatorów stacji w przypadku zmian nazewnictwa na przestrzeni lat.

    Args:
        gios_metadata (pd.DataFrame): Tabela metadanych zawierająca kolumny z kodami.
        df_dict (dict): Słownik mapujący oczyszczone i ujednolicone ramki danych do analizowanych lat

    Returns:
        dict: Zaktualizowany słownik z ujednoliconymi nazwami stacji w ramkach danych.
    
    """
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


def multiindex_code_city(df_dict, metadata):
    """
    Funkcja tworzy MultiIndex kolumn łączący Miejscowość z Kodem stacji.

    Ułatwia czytelną analizę danych poprzez dodanie nazwy miasta nad kodem stacji.

    Args:
        df_dict (dict): Słownik z ramkami danych zmapowanymi do analizowanych lat.
        metadata (pd.DataFrame): Metadane stacji (do powiązania kodu z miastem).

    Returns:
        dict: Słownik ramek danych z MultiIndexem na kolumnach.
    """
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


def correct_datetime_index(df_dict):
    """
    Funkcja koryguje indeks czasu, przesuwając rekordy z godziny 00:00:00 na 23:59:59 poprzedniego dnia.

    Args:
        df_dict (dict): Słownik ramek danych z DatetimeIndex zmapowanych do analizowanych lat.

    Returns:
        dict: Słownik z poprawionymi indeksami czasowymi.
    """
    for year, df in df_dict.items():
        df.index = df.index - pd.to_timedelta((df.index.hour == 0).astype(int), unit='s')
    return df_dict


def save_combined_data(df_dict, filename):
    """
    Funkcja scala dany ze wszytskich lat w jednę ramkę danych i zapisuje ją do pliku CSV.
    Sprawdzą również czy liczba dni w kazdym roku jest prawidłowa.

    Args:
        df_dict (dict): Słownik ramek danych do połączenia.
        filename (str): Nazwa docelowego pliku .csv

    Returns:
        pd.DataFrame: Połączona ramka danych ze wszytkich lat.
    """
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