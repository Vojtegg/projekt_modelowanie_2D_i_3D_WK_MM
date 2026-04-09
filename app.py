import streamlit as st
import geopandas as gpd
import os
import tempfile
import zipfile  
import shutil    
import folium
from streamlit_folium import st_folium

# --- IMPORT TWOJEGO MODUŁU 2D ---
from src import filter_2d

# ==========================================
# UNIWERSALNE FUNKCJE ŁADUJĄCE DANE (OBSŁUGA .ZIP)
# ==========================================

def wczytaj_wektor_z_uploadu(uploaded_file):
    """
    Sprytna funkcja do ładowania wektorów (BDOT10k, CLC).
    Obsługuje zarówno czyste pliki (.shp, .gpkg) jak i paczki .zip.
    """
    if uploaded_file is None:
        return None
        
    nazwa_pliku = uploaded_file.name
    rozszerzenie = os.path.splitext(nazwa_pliku)[1].lower()
    
    # Tworzymy ukryty folder na dysku
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Zapisujemy to, co wrzucił użytkownik
        temp_file_path = os.path.join(temp_dir, nazwa_pliku)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # JEŚLI TO ZIP: Wypakuj i poszukaj SHP lub GPKG
        if rozszerzenie == '.zip':
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Przeszukujemy wypakowane pliki
            znaleziony_plik = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.shp', '.gpkg')):
                        znaleziony_plik = os.path.join(root, file)
                        break # Znaleziono, przerywamy pętlę
                if znaleziony_plik:
                    break
                    
            if znaleziony_plik:
                return gpd.read_file(znaleziony_plik)
            else:
                st.error(f"❌ W paczce {nazwa_pliku} nie znaleziono żadnego pliku .shp ani .gpkg!")
                return None
                
        # JEŚLI TO ZWYKŁY PLIK: Czytaj od razu
        elif rozszerzenie in ['.gpkg', '.shp']:
            return gpd.read_file(temp_file_path)

    finally:
        # Zawsze na koniec (niezależnie od błędów) kasujemy folder!
        shutil.rmtree(temp_dir, ignore_errors=True)

def wczytaj_raster_z_uploadu(uploaded_file):
    """
    Sprytna funkcja do ładowania NMT (Model Terenu).
    Wyszukuje pliki .tif wewnątrz paczek .zip i przekazuje do modułu data_loader.
    """
    if uploaded_file is None:
        return None, None
        
    nazwa_pliku = uploaded_file.name
    rozszerzenie = os.path.splitext(nazwa_pliku)[1].lower()
    temp_dir = tempfile.mkdtemp()
    
    try:
        temp_file_path = os.path.join(temp_dir, nazwa_pliku)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
            
        if rozszerzenie == '.zip':
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            znaleziony_plik = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.tif', '.tiff')):
                        znaleziony_plik = os.path.join(root, file)
                        break
                if znaleziony_plik:
                    break
                    
            if znaleziony_plik:
                # Używamy funkcji z pliku data_loader.py!
                return data_loader.load_elevation_data(znaleziony_plik)
            else:
                st.error(f"❌ W paczce {nazwa_pliku} nie znaleziono pliku .tif z modelem terenu!")
                return None, None
                
        elif rozszerzenie in ['.tif', '.tiff']:
            return data_loader.load_elevation_data(temp_file_path)
            
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# Konfiguracja strony
st.set_page_config(page_title="Generator Torów F1", layout="wide")

# 1. Inicjalizacja "pamięci" aplikacji (domyślnie startujemy na stronie głównej)
if 'aktualna_strona' not in st.session_state:
    st.session_state['aktualna_strona'] = 'Glowna'

# ==========================================
# PASEK BOCZNY (Nawigacja, Logo, Instrukcja, Autorzy)
# ==========================================
with st.sidebar:
    # --- LOGO ---
    try:
        st.image("logo.jpg", use_container_width=True)
    except:
        st.warning("⚠️ Brak pliku 'logo.jpg' w folderze projektu.")
        
    st.title("Menu Nawigacyjne")
    
    # --- PRZYCISKI NAWIGACJI ---
    if st.button("🏠 Panel Główny (Narzędzia)", use_container_width=True):
        st.session_state['aktualna_strona'] = 'Glowna'
        st.rerun() 
        
    if st.button("ℹ️ Jak działa program", use_container_width=True):
        st.session_state['aktualna_strona'] = 'Opis'
        st.rerun()
        
    if st.button("🗺️ Interaktywna mapa torów F1", use_container_width=True):
        st.session_state['aktualna_strona'] = 'Mapa'
        st.rerun()

    st.markdown("---")
    
    # --- INSTRUKCJA (Rozwijana) ---
    with st.expander("📖 Jak używać aplikacji?"):
        st.markdown("""
        **Krok 1:** Przejdź do Panelu Głównego.
        **Krok 2:** Wgraj pliki `.shp` / `.gpkg` oraz Numeryczny Model Terenu.
        **Krok 3:** Dostosuj bufory i maksymalny spadek.
        **Krok 4:** Kliknij *Uruchom analizę*.
        """)
    
    # --- ŹRÓDŁA DANYCH (Rozwijana) - NOWE! ---
    with st.expander("📥 Skąd pobrać dane?"):
        st.markdown("""
        Dane przestrzenne do analizy pobierzesz całkowicie za darmo z oficjalnych rejestrów:
        
        * **BDOT10k (Budynki, Wody):** [Geoportal.gov.pl](https://mapy.geoportal.gov.pl/) 
            *(Wybierz z menu po prawej: POBIERANIE DANYCH -> Baza Danych Obiektów Topograficznych)*
        * **NMT (Model Terenu 3D):** [Geoportal.gov.pl](https://mapy.geoportal.gov.pl/) 
            *(Wybierz z menu po prawej: POBIERANIE DANYCH -> Numeryczny Model Terenu - polecamy format GeoTIFF)*
        * **Corine Land Cover:** [Copernicus Land Monitoring](https://land.copernicus.eu/en/products/corine-land-cover) lub polski portal [GIOŚ](https://clc.gios.gov.pl/).
        """)

    st.markdown("---")

    # --- INFO O AUTORACH ---
    st.info("""
    **O projekcie:**
    Aplikacja do wielokryterialnej analizy przestrzennej, optymalizująca lokalizację torów wyścigowych z użyciem danych GIS.
    
    👨‍💻 **Autorzy i role:**
    * **[Michał Medyński]** – Interfejs (Streamlit), analizy wektorowe 2D i maski wykluczeń.
    * **[Wojtek Kobiela]** – Analiza wysokościowa 3D (NMT), fuzja danych i algorytmy tras.
    """)

# ==========================================
# GŁÓWNA CZĘŚĆ EKRANU
# ==========================================

# --- PODSTRONA 1: PANEL GŁÓWNY ---
if st.session_state['aktualna_strona'] == 'Glowna':
    st.title("Optymalizator Torów Wyścigowych")
    st.markdown("Wgraj dane i ustaw parametry do analizy przestrzennej (2D & 3D).")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("📂 Wczytywanie Map")
        bdot_file = st.file_uploader("Wgraj bazę BDOT10k (.gpkg, .shp, .zip)", key="bdot")
        clc_file = st.file_uploader("Wgraj Corine Land Cover", key="clc")
        nmt_file = st.file_uploader("Wgraj Numeryczny Model Terenu (NMT)", key="nmt")
        
    with col2:
        st.header("⚙️ Parametry Analizy")
        st.subheader("Wykluczenia 2D")
        bufor_budynki = st.slider("Bufor od budynków mieszkalnych (m)", 0, 500, 100)
        bufor_wody = st.slider("Bufor od wód powierzchniowych (m)", 0, 200, 50)
        
        st.subheader("Koszty 3D")
        spadek_max = st.slider("Maksymalny spadek terenu (%)", 1, 20, 10)

        st.markdown("**Opcje zaawansowane**")
        wycinka_lasow = st.checkbox("Zezwalaj na wycinkę lasów")
        budowa_mostow = st.checkbox("Uwzględnij budowę mostów")
   
    # PRZYCISK ANALIZY
    run_analysis = st.button("🚀 Uruchom analizę przestrzenną", use_container_width=True)

    if run_analysis:
        # Sprawdzamy, czy użytkownik wgrał chociaż podstawowe pliki 2D
        if bdot_file is None or clc_file is None:
            st.error("⚠️ Proszę wgrać pliki BDOT10k oraz Corine Land Cover (najlepiej w formacie .zip) przed uruchomieniem analizy!")
        else:
            st.info("Rozpoczynam analizę danych... Proszę czekać.")
            
           # --- ETAP 1: ANALIZA 2D ---
            with st.spinner("Rozpakowywanie i wczytywanie map wektorowych (BDOT i CLC)..."):
                # 1. BUDYNKI (Kod: BUBD)
                budynki_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="BUBD")
                if budynki_gdf is not None: budynki_gdf['klasa'] = 'budynek'
                
                # 2. TERENY REKREACYJNE (Kody: PTZB, KUSK, PTUT)
                ptzb_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="PTZB")
                kusk_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="KUSK")
                ptut_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="PTUT")
                
                rekreacja_list = [df for df in [ptzb_gdf, kusk_gdf, ptut_gdf] if df is not None]
                if rekreacja_list:
                    rekreacja_gdf = gpd.GeoDataFrame(pd.concat(rekreacja_list, ignore_index=True))
                    rekreacja_gdf['klasa'] = 'rekreacja'
                else:
                    rekreacja_gdf = None

                # 3. WODY (Kod: PTWP)
                wody_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="PTWP")
                if wody_gdf is not None: wody_gdf['klasa'] = 'woda'
                
                # 4. DROGI I TORY (Kody: SKJZ, SKTR - Wykluczenia automatyczne)
                jezdnie_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="SKJZ")
                if jezdnie_gdf is not None: jezdnie_gdf['klasa'] = 'jezdnia'
                
                tory_gdf = wczytaj_wektor_z_uploadu(bdot_file, slowo_kluczowe="SKTR")
                if tory_gdf is not None: tory_gdf['klasa'] = 'tor'
                
                # Sklejamy wszystko do jednego obiektu bdot_gdf
                wszystkie_warstwy = [budynki_gdf, rekreacja_gdf, wody_gdf, jezdnie_gdf, tory_gdf]
                bdot_obiekty = [df for df in wszystkie_warstwy if df is not None and not df.empty]
                
                if bdot_obiekty:
                    bdot_gdf = gpd.GeoDataFrame(pd.concat(bdot_obiekty, ignore_index=True))
                else:
                    bdot_gdf = None

                # Wczytanie CLC (bez zmian)
                clc_gdf = wczytaj_wektor_z_uploadu(clc_file)

# --- PODSTRONA 2: JAK DZIAŁA PROGRAM ---
elif st.session_state['aktualna_strona'] == 'Opis':
    
    # Nagłówek i przycisk powrotu (tak jak w mapie)
    col_tytul, col_przycisk = st.columns([4, 1])
    with col_tytul:
        st.title("ℹ️ Metodologia badawcza i opisy analiz")
    with col_przycisk:
        st.write("") 
        if st.button("⬅️ Wróć do Panelu", key="wroc_z_opisu"):
            st.session_state['aktualna_strona'] = 'Glowna'
            st.rerun()
            
    st.markdown("---")
    
    # Treść opisu
    st.markdown("""
    ### Cel projektu
    Nasza aplikacja służy do wyznaczania optymalnych lokalizacji dla nowych torów Formuły 1 na podstawie danych przestrzennych (GIS). 
    
    ### Analiza 2D (Twarde wykluczenia)
    Używamy bazy BDOT10k do odrzucenia terenów, na których budowa jest niemożliwa lub nieopłacalna. 
    * **Budynki mieszkalne:** Tworzymy strefy buforowe, aby uniknąć hałasu.
    * **Wody powierzchniowe:** Omijamy rzeki i jeziora, aby zminimalizować koszty inżynieryjne.
    
    ### Analiza 3D (Modelowanie spadków terenu)
    Na podstawie Numerycznego Modelu Terenu (NMT) generujemy mapę spadków (Slope). 
    * Upewniamy się, że maksymalne nachylenie toru nie przekracza dopuszczalnych norm wyścigowych.
    """)


# --- PODSTRONA 3: MAPA POGLĄDOWA ---
elif st.session_state['aktualna_strona'] == 'Mapa':
    
    # Nagłówek i przycisk powrotu
    col_tytul, col_przycisk = st.columns([4, 1])
    with col_tytul:
        st.title("🌍 Interaktywna mapa torów F1 na sezon 2026")
    with col_przycisk:
        st.write("") 
        if st.button("⬅️ Wróć do Panelu", key="wroc_z_mapy"):
            st.session_state['aktualna_strona'] = 'Glowna'
            st.rerun()
            
    st.markdown("---") 
    
    m = folium.Map(location=[25.0, 10.0], zoom_start=2)

    # TWOJA PEŁNA LISTA 24 TORÓW
    f1_tracks_2026 = {
        "1. Sakhir (Bahrajn)": [26.0325, 50.5106],
        "2. Dżudda (Arabia Saudyjska)": [21.6319, 39.1044],
        "3. Melbourne (Australia)": [-37.8497, 144.9680],
        "4. Suzuka (Japonia)": [34.8431, 136.5410],
        "5. Szanghaj (Chiny)": [31.3389, 121.2200],
        "6. Miami (USA)": [25.9581, -80.2389],
        "7. Imola (Włochy)": [44.3439, 11.7167],
        "8. Monte Carlo (Monako)": [43.7347, 7.4206],
        "9. Montreal (Kanada)": [45.5000, -73.5228],
        "10. Barcelona (Hiszpania)": [41.5700, 2.2611],
        "11. Spielberg (Austria)": [47.2197, 14.7647],
        "12. Silverstone (Wielka Brytania)": [52.0786, -1.0169],
        "13. Budapeszt (Węgry)": [47.5822, 19.2486],
        "14. Spa-Francorchamps (Belgia)": [50.4372, 5.9714],
        "15. Zandvoort (Holandia)": [52.3888, 4.5409],
        "16. Monza (Włochy)": [45.6156, 9.2811],
        "17. Baku (Azerbejdżan)": [40.3725, 49.8533],
        "18. Singapur (Singapur)": [1.2914, 103.8640],
        "19. Austin (USA)": [30.1328, -97.6411],
        "20. Meksyk (Meksyk)": [19.4042, -99.0907],
        "21. Sao Paulo (Brazylia)": [-23.7036, -46.6997],
        "22. Las Vegas (USA)": [36.1147, -115.1728],
        "23. Lusail (Katar)": [25.4900, 51.4542],
        "24. Yas Marina (Abu Zabi)": [24.4672, 54.6031]
    }

    for name, coords in f1_tracks_2026.items():
        folium.Marker(
            location=coords,
            tooltip=name,
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(m)

    st_folium(m, use_container_width=True, height=1000)

