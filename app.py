import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import os

# ==========================================
# IMPORTY Z TWOICH MODUŁÓW (Logika 3D)
# ==========================================
from src import data_loader
from src import terrain_3d

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Optymalizator Torów Wyścigowych 2D/3D",
    page_icon="🏎️",
    layout="wide"
)

def main():
    st.title("🏎️ System Analizy Przestrzennej: Lokalizacja Toru Wyścigowego")
    st.markdown("""
    Aplikacja służy do wielokryterialnej analizy przestrzennej. 
    Łączy twarde wykluczenia 2D (zabudowa, wody, lasy ochronne) z analizą kosztów 3D (spadki terenu), 
    aby znaleźć optymalną ścieżkę dla toru wyścigowego.
    """)

    st.markdown("---")
    st.subheader("🌍 Interaktywna mapa torów F1 na sezon 2026")

    # Tworzymy mapę bazową
    m = folium.Map(location=[30.0, 15.0], zoom_start=2)

    # Kalendarz wyścigów
    f1_tracks_2026 = {
        "1. Melbourne (Australia)": [-37.8497, 144.9680],
        "2. Szanghaj (Chiny)": [31.3389, 121.2200],
        "3. Suzuka (Japonia)": [34.8431, 136.5390],
        "4. Sakhir (Bahrajn)": [26.0325, 50.5106],
        "5. Dżudda (Arabia Saudyjska)": [21.6319, 39.1044],
        "6. Miami (USA)": [25.9581, -80.2389],
        "7. Montreal (Kanada)": [45.5000, -73.5228],
        "8. Monte Carlo (Monako)": [43.7347, 7.4206],
        "9. Barcelona (Hiszpania)": [41.5700, 2.2611],
        "10. Spielberg (Austria)": [47.2197, 14.7647],
        "11. Silverstone (Wielka Brytania)": [52.0786, -1.0169],
        "12. Spa-Francorchamps (Belgia)": [50.4372, 5.9697],
        "13. Budapeszt (Węgry)": [47.5800, 19.2486],
        "14. Zandvoort (Holandia)": [52.3888, 4.5446],
        "15. Monza (Włochy)": [45.6156, 9.2811],
        "16. Madryt - IFEMA (Nowość 2026!)": [40.4660, -3.6160], 
        "17. Baku (Azerbejdżan)": [40.3725, 49.8533],
        "18. Marina Bay (Singapur)": [1.2914, 103.8640],
        "19. Austin (USA)": [30.1328, -97.6411],
        "20. Mexico City (Meksyk)": [19.4042, -99.0907],
        "21. Interlagos (Brazylia)": [-23.7036, -46.6997],
        "22. Las Vegas (USA)": [36.1147, -115.1728],
        "23. Lusajl (Katar)": [25.4842, 51.4542],
        "24. Yas Marina (Abu Zabi)": [24.4672, 54.6031]
    }

    for name, coords in f1_tracks_2026.items():
        folium.Marker(
            location=coords,
            tooltip=name,
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(m)

    # Wyświetlamy mapę w Streamlit
    st_folium(m, use_container_width=True, height=500)

    # --- PASEK BOCZNY (SIDEBAR) - PARAMETRY ---
    st.sidebar.header("⚙️ Parametry Analizy")
    
    st.sidebar.subheader("Wykluczenia 2D")
    buffer_distance = st.sidebar.slider("Bufor od zabudowy [m]", min_value=50, max_value=500, value=200, step=50)
    exclude_water = st.sidebar.checkbox("Wyklucz tereny wodne", value=True)
    exclude_forests = st.sidebar.checkbox("Wyklucz tereny leśne", value=True)
    
    st.sidebar.subheader("Analiza 3D (Twój Silnik)")
    # TUTAJ JEST ZMIENNA TWOJEGO KOLEGI:
    max_slope = st.sidebar.slider("Maksymalny spadek terenu [%]", min_value=1.0, max_value=20.0, value=8.0, step=1.0)

    st.sidebar.markdown("---")
    run_analysis = st.sidebar.button("🚀 Uruchom Analizę", type="primary")

    # --- GŁÓWNA LOGIKA APLIKACJI ---
    if run_analysis:
        with st.spinner("Przetwarzanie prawdziwych danych przestrzennych..."):
            
            # KROK 1: Wczytanie danych 3D (Twoja działka)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, "data", "raw", "DTM.tif")
            
            try:
                elevation_matrix, metadata = data_loader.load_elevation_data(file_path)
                st.success("Krok 1: Wczytano prawdziwą mapę DTM!")
            except Exception as e:
                st.error(f"Nie znaleziono pliku DTM.tif w data/raw/. Błąd: {e}")
                st.stop()
            
            # Nasza siatka dopasowuje się do prawdziwej wielkości mapy
            grid_shape = elevation_matrix.shape
            
            # KROK 2: Logika 2D (Działka kolegi - na razie losowa symulacja)
            # Pamiętajmy, że 0 - wolne, 1 - wykluczone
            exclusion_mask = np.random.choice([0, 1], size=grid_shape, p=[0.9, 0.1])
            st.success("Krok 2: Wygenerowano twarde maski wykluczeń 2D")
            
            # KROK 3: Logika 3D (TWOJA DZIAŁKA - Prawdziwe obliczenia)
            # Używamy Twoich funkcji i zmiennej 'max_slope' ze slidera!
            slope_matrix = terrain_3d.calculate_slope(elevation_matrix, cell_size=1.0)
            score_matrix = terrain_3d.score_topography(slope_matrix, optimal_slope=2.0, max_slope=max_slope)
            st.success(f"Krok 3: Obliczono ocenę terenu (max dopuszczalny spadek: {max_slope}%)")
            
            st.success("Krok 4: Wyznaczono optymalną trasę! (Przygotowanie pod algorytm ścieżki)")

            # --- WIZUALIZACJA ---
            st.subheader("📊 Wyniki Analizy")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Wykluczenia 2D (Maska)**")
                fig1, ax1 = plt.subplots()
                ax1.imshow(exclusion_mask, cmap='Reds', interpolation='none')
                ax1.set_title("Czerwone = Wykluczone")
                ax1.axis('off')
                st.pyplot(fig1)
                
            with col2:
                # Zmienione na TWOJĄ paletę (Zielone = Dobrze, Czerwone = Źle)
                st.markdown("**Przydatność Terenu 3D**")
                fig2, ax2 = plt.subplots()
                im2 = ax2.imshow(score_matrix, cmap='RdYlGn')
                ax2.set_title("1.0 (Zielony) = Idealnie płasko")
                ax2.axis('off')
                st.pyplot(fig2)
                
            with col3:
                st.markdown("**Fuzja (Wynik końcowy)**")
                # Kopiujemy Twoją mapę ocen, ale w miejscach wykluczeń 2D (budynki) wstawiamy NaN (brak danych)
                final_vis = np.copy(score_matrix)
                final_vis[exclusion_mask == 1] = np.nan 
                
                fig3, ax3 = plt.subplots()
                ax3.set_facecolor('black')
                # Używamy RdYlGn, żeby było widać, gdzie jest płasko, a na czarno znikną budynki/rzeki
                ax3.imshow(final_vis, cmap='RdYlGn')
                ax3.set_title("Czarny = Budynki/Woda")
                ax3.axis('off')
                st.pyplot(fig3)

if __name__ == "__main__":
    main()
