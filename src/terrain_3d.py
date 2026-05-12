import numpy as np

def calculate_slope(elevation_matrix, cell_size=1.0):
    """
    KROK 1: Oblicza nachylenie terenu w procentach.
    
    Parametry:
    elevation_matrix (numpy.ndarray): Macierz wysokości (z data_loader.py).
    cell_size (float): Rozmiar piksela w metrach (domyślnie 1 m dla danych z Geoportalu).
    
    Zwraca:
    numpy.ndarray: Macierz ze spadkami terenu wyrażonymi w procentach (%).
    """
    print("Silnik 3D: Obliczam gradienty terenu (spadki)...")
    
    # gradient() liczy różnice wysokości w pionie (dy) i poziomie (dx)
    dy, dx = np.gradient(elevation_matrix, cell_size, cell_size)
    
    # Obliczanie wektora spadku (Twierdzenie Pitagorasa)
    slope_fraction = np.sqrt(dx**2 + dy**2)
    
    # Zamiana ułamka na procenty (np. 0.05 -> 5%)
    slope_percent = slope_fraction * 100.0
    
    return slope_percent

def score_topography(slope_matrix, optimal_slope=2.0, max_slope=8.0):
    """
    KROK 2: Ocenia przydatność terenu na podstawie spadków (0.0 - 1.0).
    Miękkie ograniczenia dla toru wyścigowego.
    
    Parametry:
    slope_matrix: Macierz spadków w %.
    optimal_slope: Spadek <= tej wartości dostaje 100% punktów (1.0).
    max_slope: Spadek >= tej wartości dostaje 0% punktów (0.0).
    """
    print(f"Silnik 3D: Oceniam przydatność (Optymalnie < {optimal_slope}%, Maksimum {max_slope}%)...")
    
    # Tworzymy pustą macierz wypełnioną zerami
    score_matrix = np.zeros_like(slope_matrix)
    
    # 1. Tereny idealne (np. spadek <= 2%) -> dostają 1.0
    score_matrix[slope_matrix <= optimal_slope] = 1.0
    
    # 2. Tereny akceptowalne, ale wymagające robót ziemnych (np. między 2% a 8%)
    # Ich ocena spada liniowo z 1.0 w stronę 0.0
    mask_mid = (slope_matrix > optimal_slope) & (slope_matrix <= max_slope)
    score_matrix[mask_mid] = 1.0 - ((slope_matrix[mask_mid] - optimal_slope) / (max_slope - optimal_slope))
    
    # 3. Tereny zbyt strome (> 8%) zostają jako 0.0 (domyślna wartość macierzy)
    
    # Zabezpieczenie przed pikselami typu NoData (NaN) z mapy bazowej
    score_matrix[np.isnan(slope_matrix)] = 0.0
    
    return score_matrix