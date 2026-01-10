
import matplotlib.pyplot as plt
import seaborn as sns


# obliczanie średnich miesięcznych dla każdego roku i stacji



def monthly_mean(df):
    df_copy = df.copy()
    df_copy['miesiąc'] = df_copy.index.month
    df_copy['rok'] = df_copy.index.year
    df_copy = df_copy.set_index(['rok', 'miesiąc'])

    # średnia miesięczna
    monthly_mean = df_copy.groupby(level=['rok', 'miesiąc']).mean()
    return monthly_mean





# wykres porównujący średnie miesięczne poziomy PM2.5 w Warszawie i Katowicach w 2014 i 2024 roku
def plot_avreage(monthly_df,years_with_labels, cities):
    # średnie dla stacji
    colors = plt.cm.Set2.colors
    for city in cities:
        for year,label in years_with_labels:
            label = monthly_df.loc[year, city].mean(axis = 1)
            plt.plot(label.index, label.values, label=label, marker='o', color=colors[0])
    
    plt.xlabel('Miesiąc')
    plt.xticks(range(1,13))
    plt.ylabel('Średni poziom PM2.5')
    plt.title('Średni miesięczny poziom PM2.5 w Warszawie i Katowicach (2014 vs 2024)')
    plt.legend()
    plt.show()
    return 



## Wersja ze średnimi dziennymi zamiast maksymalnych (tak jak sugeruje WHO) ##
def find_above_norm(df_all, norm):
    norm = norm
    norms = {}
    df_all_days = df_all.copy().sort_index()
    df_all_days['data'] = pd.to_datetime(df_all_days.index.date)
    df_all_days = df_all_days.set_index('data')
    df_all_max = df_all_days.groupby(['data']).mean() ### TUTAJ JEDYNA ZMIANA  ###

    for year in [2014, 2019, 2024]:
        df_station = df_all_max[df_all_max.index.year == year] # dane dla danego roku
        norms[year] = np.array((df_station>norm).sum().values) # liczba dni przekroczenia normy dla każdej stacji

    norms_df = pd.DataFrame(norms, index=df_all_max.columns)
    norms_df.sort_values(by=2024) # sortowanie według liczby dni przekroczenia normy w 2024
    return norms_df

# wykres słupkowy dla 3 stacji z najmniejszą i 3 z największą liczbą dni przekroczenia normy w 2024 roku
def wykresy_słupkowe(norms_df, year):
    min_stations = norms_df[year].nsmallest(3).index.get_level_values(1).tolist()
    max_stations = norms_df[year].nlargest(3).index.get_level_values(1).tolist()
    stations = min_stations + max_stations

    idx = pd.IndexSlice
    plot_df = norms_df.loc[idx[:, stations], :].reset_index()

    # melt, żeby mieć kolumny: miasto, stacja, rok, liczba_dni
    plot_df = plot_df.melt(id_vars=['level_0', 'level_1'], var_name='rok', value_name='liczba_dni')
    plot_df = plot_df.rename(columns={'level_0': 'miasto', 'level_1': 'stacja'})

    # połącz miasto i kod w jedną kolumnę
    plot_df['miasto_stacja'] = plot_df['miasto'] + '\n' + plot_df['stacja']

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