import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# wykres porównujący średnie miesięczne poziomy PM2.5
def plot_average(monthly_df_grouped, years, cities):
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

# heatmapy średnich miesięcznych poziomów PM2.5 dla wszystkich miast
def heatmaps(monthly_df_grouped):
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


# wykres słupkowy dla 3 stacji z najmniejszą i 3 z największą liczbą dni przekroczenia normy
def bar_plots(norms_df, year):
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


if __name__ == "__main__":
    pass