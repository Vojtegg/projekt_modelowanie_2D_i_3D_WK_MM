import numpy as np
from skimage.graph import route_through_array
from scipy.ndimage import distance_transform_edt

def generate_track_loop(cost_matrix, num_waypoints=4):
    """
    Szuka optymalnej, zamkniętej pętli (toru) na mapie kosztów.
    Zwraca tuple: (trasa_numpy, statystyki_slownik)
    """
    print("Pathfinder: Rozpoczynam wyznaczanie pętli...")
    
    bezpieczna_macierz = np.where(np.isinf(cost_matrix), 99999, cost_matrix)
    wysokosc, szerokosc = bezpieczna_macierz.shape
    
    # NAPRAWA 3: Niewidzialna ściana wokół mapy (Zakaz ucieczek)
    
    grubosc_ramki = 20
    bezpieczna_macierz[:grubosc_ramki, :] = 99999
    bezpieczna_macierz[-grubosc_ramki:, :] = 99999
    bezpieczna_macierz[:, :grubosc_ramki] = 99999
    bezpieczna_macierz[:, -grubosc_ramki:] = 99999
    
    maska_bezpieczna = (bezpieczna_macierz < 99999).astype(int)
    dystans_do_przeszkod = distance_transform_edt(maska_bezpieczna)
    center_y, center_x = np.unravel_index(np.argmax(dystans_do_przeszkod), dystans_do_przeszkod.shape)
    
    maksymalny_bezpieczny_promien = dystans_do_przeszkod[center_y, center_x]
    waypoints = []
    
    # Losowy obrót "szkieletu" toru o dowolny kąt (0 - 360 stopni)
    offset_kata = np.random.uniform(0, 2 * np.pi) 
    
    # Lekko przesuwamy sam środek ciężkości (do 20% maksymalnego promienia)
    przesuniecie_y = int(maksymalny_bezpieczny_promien * np.random.uniform(-0.2, 0.2))
    przesuniecie_x = int(maksymalny_bezpieczny_promien * np.random.uniform(-0.2, 0.2))
    
    for i in range(num_waypoints):
        # Każdy waypoint otrzymuje swój własny, lekko przesunięty kąt
        angle = (2 * np.pi * i / num_waypoints) + offset_kata
        
        # ZMNIEJSZONY ROZRZUT (0.3 do 0.7), żeby nie bić w naszą nową "betonową ścianę"
        losowy_radius = maksymalny_bezpieczny_promien * np.random.uniform(0.3, 0.7)
        
        # Wyliczamy pozycję X i Y z uwzględnieniem przesuniętego środka
        y = int((center_y + przesuniecie_y) + losowy_radius * np.sin(angle))
        x = int((center_x + przesuniecie_x) + losowy_radius * np.cos(angle))
        
        # NAPRAWA 4: Margines (Odrywamy punkty od zera!)
        
        margines = 25
        y = int(np.clip(y, margines, wysokosc - margines - 1))
        x = int(np.clip(x, margines, szerokosc - margines - 1))

        if bezpieczna_macierz[y, x] >= 99999:
            znaleziono_nowy = False
            for r in range(1, 30):
                for dy in range(-r, r+1):
                    for dx in range(-r, r+1):
                        ny = int(np.clip(y + dy, margines, wysokosc - margines - 1))
                        nx = int(np.clip(x + dx, margines, szerokosc - margines - 1))
                        if bezpieczna_macierz[ny, nx] < 99999:
                            y, x = ny, nx
                            znaleziono_nowy = True
                            break
                    if znaleziono_nowy: break
                if znaleziono_nowy: break

        waypoints.append((y, x))

    waypoints.append(waypoints[0])
    full_path = []

    # Tworzymy kopię macierzy do dynamicznego nakładania kar
    dynamiczna_macierz_kosztow = bezpieczna_macierz.copy()

    for i in range(len(waypoints) - 1):
        start = waypoints[i]
        end = waypoints[i+1]

        try:
            # Używamy DYNAMICZNEJ macierzy, która z każdym krokiem ma nowe przeszkody
            path, cost = route_through_array(dynamiczna_macierz_kosztow, start, end, fully_connected=True)
            full_path.extend(path[:-1]) 
            
            # Wylewamy "wirtualny beton" na właśnie wyrysowaną ścieżkę
            for py, px in path:
                dynamiczna_macierz_kosztow[py, px] += 50000 
                
        except ValueError:
            print(f"Pathfinder: Brak przejścia między {start} a {end}.")
            return None, None 

    full_path.append(waypoints[-1])
    
    # Przygotowujemy statystyki do zwrotu
    ROZDZIELCZOSC_METRY = 1.0  
    dlugosc_calkowita = 0.0
    
    for i in range(len(full_path) - 1):
        y1, x1 = full_path[i]
        y2, x2 = full_path[i+1]
        if x1 != x2 and y1 != y2:
            dlugosc_calkowita += 1.414 * ROZDZIELCZOSC_METRY
        else:
            dlugosc_calkowita += 1.0 * ROZDZIELCZOSC_METRY

    dlugosc_km = round(dlugosc_calkowita / 1000, 2)
    
    statystyki_toru = {
        "dlugosc_km": dlugosc_km,
        "ilosc_pikseli": len(full_path)
    }
    
    print(f"Pathfinder: Trasa wygenerowana ({dlugosc_km} km)!")
    
    return np.array(full_path), statystyki_toru
