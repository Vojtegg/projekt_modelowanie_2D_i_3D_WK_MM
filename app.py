import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from rasterio.plot import show

# Importy z Twojego folderu src
from src import data_loader 
from src import terrain_3d
from src import filter_2d

# ==========================================
# KONFIGURACJA APLIKACJI 
# ==========================================
st.set_page_config(page_title="Generator Torów F1", layout="wide")

if 'aktualna_strona' not in st.session_state:
    st.session_state['aktualna_strona'] = 'Glowna'

# ==========================================
# PASEK BOCZNY (Tylko duże, czyste przyciski!)
# ==========================================
with st.sidebar:
    try:
        st.image("logo.jpg", use_container_width=True)
    except:
        st.warning("⚠️ Brak pliku 'logo.jpg' w folderze projektu.")
        
    st.title("📌 Menu Nawigacyjne")
    
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
    
    with st.expander("📖 Jak używać aplikacji?"):
        st.markdown("""
        **Krok 1:** Przejdź do Panelu Głównego.
        **Krok 2:** Wgraj pliki `.shp` / `.gpkg` oraz Numeryczny Model Terenu.
        **Krok 3:** Dostosuj bufory i maksymalny spadek.
        **Krok 4:** Kliknij *Uruchom analizę*.
        """)
    
    with st.expander("📥 Skąd pobrać dane?"):
        st.markdown("""
        Dane przestrzenne do analizy pobierzesz całkowicie za darmo z oficjalnych rejestrów:
        
        * **BDOT10k (Budynki, Wody):** [Geoportal.gov.pl](https://mapy.geoportal.gov.pl/) 
        * **NMT (Model Terenu 3D):** [Geoportal.gov.pl](https://mapy.geoportal.gov.pl/) 
        * **Corine Land Cover:** [Copernicus Land Monitoring](https://land.copernicus.eu/en/products/corine-land-cover)
        """)

    st.markdown("---")

    st.info("""
    **O projekcie:**
    Aplikacja do wielokryterialnej analizy przestrzennej, optymalizująca lokalizację torów wyścigowych z użyciem danych GIS.
    
    👨‍💻 **Autorzy i role:**
    * **Michał Medyński** – Interfejs (Streamlit), analizy wektorowe 2D i maski wykluczeń.
    * **Wojtek Kobiela** – Analiza wysokościowa 3D (NMT), fuzja danych i algorytmy tras.
    """)

# ==========================================
# PODSTRONA 1: GŁÓWNA CZĘŚĆ EKRANU (ANALIZA)
# ==========================================
if st.session_state['aktualna_strona'] == 'Glowna':
    st.title("Optymalizator Torów Wyścigowych")
    st.markdown("Wgraj dane i ustaw parametry do analizy przestrzennej (2D & 3D).")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("📂 Wczytywanie Map")
        bdot_file = st.file_uploader("Wgraj bazę BDOT10k (.gpkg, .shp, .zip)", key="bdot")
        clc_file = st.file_uploader("Wgraj Corine Land Cover", key="clc")
        
        # Opcja na wgranie wielu kafelków NMT
        nmt_file = st.file_uploader("Wgraj NMT (Wiele plików .zip / .asc)", key="nmt", accept_multiple_files=True)
        
    with col2:
        st.header("⚙️ Parametry Analizy")
        st.subheader("Wykluczenia 2D")
        bufor_budynki = st.slider("Bufor od budynków mieszkalnych (m)", 0, 500, 100)
        bufor_rekreacja = st.slider("Bufor od terenów rekreacyjnych (m)", 0, 300, 50)
        
        # SPRAWDZAMY STAN CHECKBOXA (zanim jeszcze narysujemy go na dole)
        czy_mosty = st.session_state.get("mosty_key", False)
        
        # SUWAK WODY: Parametr 'disabled' blokuje go, gdy czy_mosty == True
        bufor_wody = st.slider("Bufor od wód powierzchniowych (m)", 0, 200, 50, disabled=czy_mosty)
        
        st.subheader("Koszty 3D")
        spadek_max = st.slider("Maksymalny spadek terenu (%)", 1, 20, 10)

        st.markdown("**Opcje zaawansowane**")
        wycinka_lasow = st.checkbox("Zezwalaj na wycinkę lasów")
        
        # CHECKBOX: Dodajemy 'key', żeby Streamlit zapamiętał jego kliknięcie
        budowa_mostow = st.checkbox("Uwzględnij budowę mostów", key="mosty_key")
   
    run_analysis = st.button("🚀 Uruchom analizę przestrzenną", use_container_width=True)

    if run_analysis:
        if bdot_file is None or clc_file is None:
            st.error("⚠️ Proszę wgrać pliki BDOT10k oraz Corine Land Cover przed uruchomieniem analizy!")
        else:
            st.info("Rozpoczynam analizę danych... Proszę czekać.")
            with st.spinner("Przetwarzanie map wektorowych (BDOT i CLC)..."):
                try:
                    bdot_slownik = data_loader.wczytaj_wszystkie_warstwy_bdot(bdot_file)
                    clc_gdf = data_loader.wczytaj_wektor_z_uploadu(clc_file)
                    
                    if bdot_slownik is not None and clc_gdf is not None:
                        st.write("🛡️ Generowanie mapy wykluczeń (2D)...")
                        maska = filter_2d.wygeneruj_maske_wykluczen(
                            bdot_slownik=bdot_slownik, clc_gdf=clc_gdf,
                            buf_bud=bufor_budynki, buf_rek=bufor_rekreacja, buf_woda=bufor_wody,
                            wycinka_lasow=wycinka_lasow, budowa_mostow=budowa_mostow
                        )
                        
                        if maska is not None:
                            st.success("✅ Analiza 2D zakończona pomyślnie!")
                            
                            if nmt_file: 
                                with st.spinner("Łączenie kafelków NMT i obliczanie spadków..."):
                                    try:
                                        macierz_wysokosci, raster_transform, raster_crs = data_loader.wczytaj_raster_z_uploadu(nmt_file)
                                        if macierz_wysokosci is not None:
                                            macierz_spadkow = terrain_3d.calculate_slope(macierz_wysokosci, cell_size=1.0)
                                            mapa_kosztow_3d = terrain_3d.score_topography(macierz_spadkow, optimal_slope=2.0, max_slope=spadek_max)
                                            
                                            st.success("✅ Analiza wysokościowa (3D) zakończona pomyślnie!")
                                            st.balloons()
                                            
                                            st.write("🗺️ **Poniżej znajduje się wygenerowana mapa wyników (Zintegrowana 2D + 3D):**")
                                            
                                            # GŁÓWNA MAPA
                                            fig, ax = plt.subplots(figsize=(8, 6))
                                            show(mapa_kosztow_3d, transform=raster_transform, ax=ax, cmap='RdYlGn', title="Znalezione lokalizacje dla Toru F1")
                                            
                                            if hasattr(maska, 'empty') and not maska.empty:
                                                maska.plot(ax=ax, color='black', alpha=0.5, edgecolor='red', hatch='///')
                                            elif hasattr(maska, 'is_empty') and not maska.is_empty:
                                                gpd.GeoSeries([maska]).plot(ax=ax, color='black', alpha=0.5, edgecolor='red', hatch='///')
                                                
                                            wysokosc, szerokosc = macierz_wysokosci.shape
                                            lewy_gorny_x, lewy_gorny_y = raster_transform * (0, 0)
                                            prawy_dolny_x, prawy_dolny_y = raster_transform * (szerokosc, wysokosc)

                                            ax.set_xlim(min(lewy_gorny_x, prawy_dolny_x), max(lewy_gorny_x, prawy_dolny_x))
                                            ax.set_ylim(min(lewy_gorny_y, prawy_dolny_y), max(lewy_gorny_y, prawy_dolny_y))
                                            
                                            ax.axis('off') 
                                            st.pyplot(fig, use_container_width=False)
                                            
                                            # ==========================================
                                            # PRZYWRÓCONE 3 MAPKI Z PATHFINDERA
                                            # ==========================================
                                            st.markdown("---")
                                            st.subheader("📊 Analiza 3D krok po kroku (Podgląd modelu)")
                                            st.write("Poniżej przedstawiono surowe etapy przetwarzania modelu Numerycznego Modelu Terenu:")
                                            
                                            fig_szczegoly, axes = plt.subplots(1, 3, figsize=(16, 5))
                                            
                                            im1 = axes[0].imshow(macierz_wysokosci, cmap='terrain')
                                            axes[0].set_title("1. Model Terenu (Wysokość)")
                                            axes[0].axis('off')
                                            fig_szczegoly.colorbar(im1, ax=axes[0], label="m n.p.m.")
                                            
                                            im2 = axes[1].imshow(macierz_spadkow, cmap='Reds', vmin=0, vmax=15)
                                            axes[1].set_title("2. Spadki Terenu (%)")
                                            axes[1].axis('off')
                                            fig_szczegoly.colorbar(im2, ax=axes[1], label="% nachylenia")
                                            
                                            im3 = axes[2].imshow(mapa_kosztow_3d, cmap='RdYlGn', vmin=0, vmax=1)
                                            axes[2].set_title("3. Ocena przydatności (0-1)")
                                            axes[2].axis('off')
                                            fig_szczegoly.colorbar(im3, ax=axes[2], label="Wynik (Tylko 3D)")
                                            
                                            st.pyplot(fig_szczegoly, use_container_width=True)
                                            
                                        else:
                                            st.error("❌ Błąd: Nie udało się wczytać macierzy z NMT.")
                                    except Exception as e:
                                        st.error(f"❌ Wystąpił błąd podczas analizy 3D: {e}")
                            else:
                                st.warning("⚠️ Nie wgrano pliku NMT. Ominięto analizę 3D.")
                        else:
                            st.error("❌ Błąd: Funkcja filtrująca 2D nie zwróciła wyniku.")
                    else:
                        st.error("❌ Błąd: Nie udało się wczytać map wektorowych.")
                except Exception as e:
                    st.error(f"❌ Wystąpił błąd podczas analizy 2D: {e}")

# ==========================================
# PODSTRONA 2: INSTRUKCJA I OPIS
# ==========================================
elif st.session_state['aktualna_strona'] == 'Opis':
    col_tytul, col_przycisk = st.columns([4, 1])
    with col_tytul:
        st.title("ℹ️ Metodologia badawcza i opisy analiz")
    with col_przycisk:
        st.write("") 
        if st.button("⬅️ Wróć do Panelu", key="wroc_z_opisu"):
            st.session_state['aktualna_strona'] = 'Glowna'
            st.rerun()
            
    st.markdown("---")
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

# ==========================================
# PODSTRONA 3: MAPA POGLĄDOWA (FOLIUM)
# ==========================================
elif st.session_state['aktualna_strona'] == 'Mapa':
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

    st_folium(m, use_container_width=True, height=700)