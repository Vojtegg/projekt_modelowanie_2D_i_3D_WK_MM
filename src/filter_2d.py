import geopandas as gpd
import pandas as pd
import streamlit as st
import re  # Moduł do wyszukiwania wzorców (nasze CODE_**)

def wygeneruj_maske_wykluczen(bdot_gdf, clc_gdf, buf_bud, buf_rek, buf_woda, wycinka_lasow, budowa_mostow):
    """
    Funkcja generująca obszary wykluczone pod budowę toru F1.
    Zwraca jeden połączony poligon (obszar niedozwolony).
    """
    lista_wykluczen = []
    # TYMCZASOWY PODGLĄD DANYCH BDOT
    st.info("👀 Podgląd wczytanych danych BDOT:")
    st.write(bdot_gdf.head(5))

    # =========================================
    # 1. ANALIZA BDOT10k (Bufory i Bezpieczeństwo)
    # =========================================
    if bdot_gdf is not None and 'klasa' in bdot_gdf.columns:
        
        # A. BUDYNKI - suwak buf_bud
        budynki = bdot_gdf[bdot_gdf['klasa'] == 'budynek']
        if not budynki.empty:
            lista_wykluczen.append(budynki.geometry.buffer(buf_bud).unary_union)

        # B. REKREACJA - suwak buf_rek
        rekreacja = bdot_gdf[bdot_gdf['klasa'] == 'rekreacja']
        if not rekreacja.empty:
            lista_wykluczen.append(rekreacja.geometry.buffer(buf_rek).unary_union)

        # C. WODY - suwak buf_woda + opcja mostów
        if not budowa_mostow:
            wody = bdot_gdf[bdot_gdf['klasa'] == 'woda']
            if not wody.empty:
                lista_wykluczen.append(wody.geometry.buffer(buf_woda).unary_union)
                
        # D. DROGI I TORY - stały bufor bezpieczeństwa (15m)
        infrastruktura = bdot_gdf[bdot_gdf['klasa'].isin(['jezdnia', 'tor'])]
        if not infrastruktura.empty:
            lista_wykluczen.append(infrastruktura.geometry.buffer(15).unary_union)

    # =========================================
    # 2. ANALIZA CORINE LAND COVER (Makro-wykluczenia)
    # =========================================
    # Szukamy kolumny CODE_...
    # =========================================
    # 2. ANALIZA CORINE LAND COVER (Makro-wykluczenia)
    # =========================================
    kolumna_clc = next((col for col in clc_gdf.columns if re.match(r'(?i)^code_\d{2}$', str(col))), None)
    
    if kolumna_clc:
        # Twarde zakazy (bez rzek!): 
        # 111-Centra, 122-Drogi, 123-Porty, 141-Parki, 142-Sport, 4xx-Bagna, 512-Jeziora, 52x-Morza, 331-Plaże, 332-Skały
        kody_wykluczone = [
            '111', '122', '123', '141', '142', 
            '411', '412', '421', '422', '423', 
            '512', '521', '522', '523',
            '331', '332'
        ]
        
        # Opcjonalne: Lasy (311, 312, 313)
        if not wycinka_lasow:
            kody_wykluczone.extend(['311', '312', '313'])
            
        # Opcjonalne: RZEKI (511) - TYLKO JEŚLI NIE BUDUJEMY MOSTÓW
        if not budowa_mostow:
            kody_wykluczone.append('511')
            
        niechciane_tereny = clc_gdf[clc_gdf[kolumna_clc].isin(kody_wykluczone)]
        if not niechciane_tereny.empty:
            lista_wykluczen.append(niechciane_tereny.geometry.unary_union)

    # =========================================
    # 3. ŁĄCZENIE WSZYSTKIEGO W JEDNĄ MASKĘ
    # =========================================
    if len(lista_wykluczen) > 0:
        maska_koncowa = gpd.GeoSeries(pd.concat([gpd.GeoSeries(g) for g in lista_wykluczen])).unary_union
        return maska_koncowa
    else:
        return None