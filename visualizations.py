import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def heatmaps(monthly_df):
    # lista miast
    cities = [c for c in monthly_df.columns.levels[0] if c not in ['miesiąc', 'rok']]
    n = len(cities)

    # siatka podwykresów
    cols = 4
    rows = int(np.ceil(n / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
    axes = axes.flatten()

    for ax, city in zip(axes, cities):
        
        # średnie wartości miesięczne dla miasta 
        city_data = monthly_df[city].mean(axis=1)
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


if __name__ == "__main__":
    pass