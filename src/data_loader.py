import os
import rasterio
import numpy as np

def load_elevation_data(file_path):
    """
    Wczytuje Numeryczny Model Terenu (DEM) z pliku GeoTIFF.
    
    Zasada czarnej skrzynki: Funkcja przyjmuje ścieżkę do pliku, 
    a zwraca czystą macierz numpy (wysokości w metrach) oraz metadane 
    potrzebne do ewentualnego nałożenia na mapę.
    
    Parametry:
    file_path (str): Ścieżka do pliku .tif z modelem terenu.
    
    Zwraca:
    tuple: (elevation_matrix, metadata)
           elevation_matrix - dwuwymiarowa macierz numpy z wysokościami
           metadata - słownik z informacjami przestrzennymi (CRS, transform)
    """
    
    # Sprawdzenie, czy plik w ogóle istnieje
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ BŁĄD: Nie znaleziono pliku pod ścieżką: {file_path}")
        
    print(f"Baza: Rozpoczynam wczytywanie pliku: {file_path}...")
    
    with rasterio.open(file_path) as dataset:
        # Odczytujemy pierwszą "warstwę" (band 1), bo DEM to obraz w skali szarości
        elevation_matrix = dataset.read(1)
        
        # Pobieramy metadane (georeferencje, rozdzielczość piksela)
        metadata = dataset.profile
        
        # Opcjonalne: Czyszczenie danych (NoData)
        # Zdarza się, że tło mapy ma wartość np. -9999. Zamieniamy to na "Not a Number" (NaN),
        # żeby nie popsuło nam później obliczania spadków (matematyki).
        nodata_value = dataset.nodata
        if nodata_value is not None:
            # Konwersja na float, aby móc użyć np.nan
            elevation_matrix = elevation_matrix.astype(np.float32)
            elevation_matrix[elevation_matrix == nodata_value] = np.nan
            
    print(f"✅ Sukces! Wczytano macierz o wymiarach: {elevation_matrix.shape}")
    
    return elevation_matrix, metadata

# ==========================================
# SEKCJA TESTOWA (Uruchomi się tylko, gdy odpalisz ten plik bezpośrednio)
# ==========================================
if __name__ == "__main__":
    
    # 1. Pobieramy absolutną ścieżkę do folderu, w którym jest ten skrypt (czyli do folderu 'src')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Budujemy bezpieczną ścieżkę: z 'src' cofamy się o poziom wyżej (".."), wchodzimy do 'data', potem do 'raw' i szukamy pliku.
    test_file = os.path.join(BASE_DIR, "..", "data", "raw", "DTM.tif")
    
    print(f"🔧 System szuka pliku dokładnie tutaj:\n{test_file}\n")
    
    try:
        macierz, meta = load_elevation_data(test_file)
        print("\nPróbka danych (lewy górny róg 3x3 piksele):")
        print(macierz[:3, :3])
    except FileNotFoundError as e:
        print("❌ Nie znaleziono pliku!")
        print("Upewnij się, że wrzuciłeś plik 'DTM.tif' do folderu 'data/raw/'!")
