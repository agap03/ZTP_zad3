import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
"""
visualizations.py
--------------
Moduł służący do wizualizacji danych o stężeniu pyłów PM2.5.
Zawiera funkcje do generowania wykresów liniowych, map ciepła (heatmaps) 
oraz zestawień słupkowych dla wybranych stacji pomiarowych.

"""
def plot_average(monthly_df_grouped, years, cities):
    """
        Funkcja rysująca wykres liniowy pokazujący trend średnich miesięcznych wartości PM2.5 dla wybranych lat i miast  

    Args:
        monthly_df_grouped (pd.DataFrame): Zgrupowana po miastach ramka danych z uśrednionymi miesięcznymi wartościami PM2.5 
        years (list[int]): lista lat które będą analizowane  
        cities(list[str]): lista analizowanych miast 
   
    Returns:
        None
    """
    # średnie dla stacji
    colors = plt.cm.Set2.colors
    color_index = 0

    df = monthly_df_grouped[cities]
    
    for year in years:
        df_year = df.loc[year]
        for city in cities:
            plt.plot(range(1,13), df_year[city], label=f'{city} {year}', marker='o', color=colors[color_index])
            color_index += 1

    plt.xlabel('Miesiąc')
    plt.xticks(range(1,13))
    plt.ylabel('Średni poziom PM2.5')
    plt.title(f'Średni miesięczny poziom PM2.5 w miastach: {", ".join(cities)} w latach: {", ".join(map(str, years))}')
    plt.legend()
    plt.show()
    return 

def heatmaps(monthly_df_grouped):
    """
        Funkcja rysująca heatmapy średnich miesięcznych wartości PM2.5 dla wszystkich miast
    
    Args:
        monthly_df_grouped (DataFrame): Zgrupowana po misatach ramka danych z uśrednionymi wartościami PM2.5 po wszytkich stacjach z danego miasta 
    
    Returns:
        None
    """
    # lista miast
    cities = [c for c in monthly_df_grouped.columns if c not in ['miesiąc', 'rok']]
    n = len(cities)

    # siatka podwykresów
    cols = 4
    rows = int(np.ceil(n / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
    axes = axes.flatten()

    for ax, city in zip(axes, cities):
        
        # średnie wartości miesięczne dla miasta 
        city_data = monthly_df_grouped[city]
        city_data = city_data.reset_index()
        city_data.columns = ['rok', 'miesiąc', 'PM2.5']
        city_data['PM2.5'] = pd.to_numeric(city_data['PM2.5'])

        df_pivot = city_data.pivot(index='rok', columns='miesiąc', values='PM2.5')

        sns.heatmap(df_pivot, cmap='YlOrRd', ax=ax)
        ax.set_title(f'{city} - średnie miesięczne PM2.5')
        ax.set_xlabel('Miesiąc')
        ax.set_ylabel('Rok')

    # Jeśli zostały puste osie, wyłączamy je
    for ax in axes[n:]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()
    return



def bar_plots(norms_df, year):
    """
        Funkcja przygotowująca wykres słupkowy grupowany ze wszytkich analizowanych lat dla 3 stacji z najmniejszą i 3 z największą liczbą dni przekroczenia normy w wybranym roku, gdzie oś X – stacje,
        a oś Y – liczba dni z przekroczeniem normy
    
    Args:
        norms_df (pd.DataFrame): Dataframe z z MultiIndexem (['Miejscowość', 'Kod stacji']. 
            Kolumny to lata, wartości to liczba dni powyżej normy.
        year (int): Rok referencyjny dla wyboru stacji ekstremalnych. 
    
    Returns:
        None
    """
    min_stations = norms_df[year].nsmallest(3).index.get_level_values(1).tolist()
    max_stations = norms_df[year].nlargest(3).index.get_level_values(1).tolist()
    stations = min_stations + max_stations

    idx = pd.IndexSlice
    plot_df = norms_df.loc[idx[:, stations], :].reset_index()

    # melt, żeby mieć kolumny: miasto, stacja, rok, liczba_dni
    plot_df = plot_df.melt(id_vars=['Miejscowość', 'Kod stacji'], var_name='rok', value_name='liczba_dni')

    # połącz miasto i kod w jedną kolumnę
    plot_df['miasto_stacja'] = plot_df['Miejscowość'] + '\n' + plot_df['Kod stacji']

    # wykres
    plt.figure(figsize=(10, 6))
    sns.barplot(data=plot_df, x='miasto_stacja', y='liczba_dni', hue='rok', palette='Pastel2')
    plt.xticks(rotation=45)
    plt.ylabel('Liczba dni z przekroczeniem normy')
    plt.title('Dni z przekroczeniem normy PM2.5 dla wybranych stacji')
    plt.legend(title='Rok')
    plt.tight_layout()
    plt.show()
    return 


#wizualizacja do zad. 5 z województwami:
def plot_voivodeship_exceedances(voiv_df, years=(2015, 2018, 2021, 2024), figsize=(12, 6)):
    """
    Wykres słupkowy: liczba dni, w których średnia dobowa PM2.5 w województwie (średnia po stacjach) przekroczyła normę.
    """
    years = [y for y in years if y in voiv_df.columns]
    df = voiv_df[years]
    ax = df.plot(kind="bar", figsize=figsize)
    ax.set_title("Liczba dni z przekroczeniem normy PM2.5 dla średniej dobowej województwa")
    ax.set_xlabel("Województwo")
    ax.set_ylabel("Liczba dni z przekroczeniem")
    ax.legend(title="Rok", loc="center left", bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    plt.show()
    
if __name__ == "__main__":
    pass