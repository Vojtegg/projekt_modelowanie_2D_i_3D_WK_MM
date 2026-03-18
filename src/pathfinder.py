import os
import matplotlib.pyplot as plt

# Tutaj importujemy TWOJE własne moduły!
import data_loader
import terrain_3d

def analyze_terrain(file_name):
    """
    Główna funkcja analityczna 3D. 
    Łączy wczytywanie pliku z obliczaniem spadków i generuje wykresy.
    """
    # 1. Budujemy bezpieczną ścieżkę do pliku (szukamy w folderze data/raw/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "..", "data", "raw", file_name)
    
    print("--- ETAP 1: Wczytywanie Mapy ---")
    # Wywołujemy funkcję z pliku data_loader.py!
    # Zwraca nam ona gotową macierz wysokości.
    elevation_matrix, metadata = data_loader.load_elevation_data(file_path)
    
    print("\n--- ETAP 2: Analiza 3D (Spadki i Ocena) ---")
    # Przekazujemy wczytaną macierz do pliku terrain_3d.py!
    slope_matrix = terrain_3d.calculate_slope(elevation_matrix, cell_size=1.0)
    score_matrix = terrain_3d.score_topography(slope_matrix, optimal_slope=2.0, max_slope=8.0)
    
    print("\n✅ Obliczenia zakończone! Generuję wizualizację...")
    
    # ==========================================
    # ETAP 3: WIZUALIZACJA (Rysowanie Heatmapy)
    # ==========================================
    # Tworzymy okno z trzema mapami obok siebie
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # MAPA 1: Oryginalny Model Terenu
    ax1 = axes[0].imshow(elevation_matrix, cmap='terrain')
    axes[0].set_title("1. Model Terenu (Wysokość)")
    fig.colorbar(ax1, ax=axes[0], label="m n.p.m.")
    
    # MAPA 2: Spadki w procentach
    # Używamy vmax=15, żeby uciąć skalę kolorów na 15% (lepiej widać różnice na nizinach)
    ax2 = axes[1].imshow(slope_matrix, cmap='Reds', vmin=0, vmax=15)
    axes[1].set_title("2. Spadki Terenu (%)")
    fig.colorbar(ax2, ax=axes[1], label="% nachylenia")
    
    # MAPA 3: Ocena przydatności (Twoje dzieło!)
    # cmap='RdYlGn' to paleta Red-Yellow-Green (Czerwony=źle, Zielony=dobrze)
    ax3 = axes[2].imshow(score_matrix, cmap='RdYlGn') 
    axes[2].set_title("3. Przydatność pod Tor (0 do 1)")
    fig.colorbar(ax3, ax=axes[2], label="1 = Budujemy, 0 = Zakaz")
    
    plt.tight_layout()
    plt.show()

# ==========================================
# URUCHOMIENIE
# ==========================================
if __name__ == "__main__":
    # Tutaj wpisujemy nazwę Twojego pliku, który leży w data/raw/
    analyze_terrain("DTM.tif")
    
