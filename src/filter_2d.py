import geopandas as gpd
import pandas as pd
import streamlit as st
import re 

def wygeneruj_maske_wykluczen(bdot_slownik, clc_gdf, buf_bud, buf_rek, buf_woda, wycinka_lasow, budowa_mostow):
    """
    Funkcja przyjmuje słownik z gotowymi warstwami BDOT i maskuje zakazane obszary.
    """
    lista_wykluczen = []

    # 1. ANALIZA BDOT10k 
    
    if bdot_slownik is not None:
        
        # A. BUDYNKI 
        if bdot_slownik['budynki'] is not None and not bdot_slownik['budynki'].empty:
            lista_wykluczen.append(bdot_slownik['budynki'].geometry.buffer(buf_bud).unary_union)

        # B. REKREACJA 
        if bdot_slownik['rekreacja'] is not None and not bdot_slownik['rekreacja'].empty:
            lista_wykluczen.append(bdot_slownik['rekreacja'].geometry.buffer(buf_rek).unary_union)

        # C. WODY (Opcja mostów)
        if not budowa_mostow and bdot_slownik['wody'] is not None and not bdot_slownik['wody'].empty:
            lista_wykluczen.append(bdot_slownik['wody'].geometry.buffer(buf_woda).unary_union)

        # D. OMINIĘCIE ISTNIEJĄCYCH JEZDNI 
        if bdot_slownik['jezdnie'] is not None and not bdot_slownik['jezdnie'].empty:
            jezdnie = bdot_slownik['jezdnie']
            
            # Szukamy kolumny
            kolumna_nawierzchni = None
            for col in jezdnie.columns:
                if 'naw' in col.lower() or 'rodz' in col.lower() or 'typ' in col.lower():
                    kolumna_nawierzchni = col
                    break
            
            if kolumna_nawierzchni:
                # ODWRÓCONA LOGIKA: Zostawiamy w spokoju TYLKO drogi, które mają w nazwie 
                # 'bitum' (masa bitumiczna to asfalt), 'beton' lub 'kostk' (kostka). 
                # Cała reszta (żwir, grunt, tłuczeń) znika z radaru przeszkód
                twarde_drogi = jezdnie[jezdnie[kolumna_nawierzchni].astype(str).str.contains('bitum|beton|kostk', case=False, na=False, regex=True)]
            else:
                # Jak nie wiemy co to za droga, to jej nie blokujemy
                twarde_drogi = gpd.GeoDataFrame(geometry=[], crs=jezdnie.crs) 
                
            # Nakładamy bufor tylko na ten prawdziwy, twardy asfalt/kostkę
            if not twarde_drogi.empty:
                lista_wykluczen.append(twarde_drogi.geometry.buffer(10).unary_union)
            
        if bdot_slownik['tory'] is not None and not bdot_slownik['tory'].empty:
            lista_wykluczen.append(bdot_slownik['tory'].geometry.buffer(10).unary_union)
    
    # 2. ANALIZA CORINE LAND COVER 
    
    kolumna_clc = next((col for col in clc_gdf.columns if re.match(r'(?i)^code_\d{2}$', str(col))), None)
    
    if kolumna_clc:
        kody_wykluczone = ['111', '122', '123', '141', '142', '411', '412', '421', '422', '423', '512', '521', '522', '523', '331', '332']
        if not wycinka_lasow: kody_wykluczone.extend(['311', '312', '313'])
            
        obszary_zabronione = clc_gdf[clc_gdf[kolumna_clc].astype(str).isin(kody_wykluczone)]
        if not obszary_zabronione.empty:
            lista_wykluczen.append(obszary_zabronione.geometry.unary_union)

    if not lista_wykluczen:
        return None

    # Scalenie wszystkich wykluczeń w jeden obiekt poligonowy
    wszystkie_wykluczenia = gpd.GeoSeries(lista_wykluczen).unary_union
    return gpd.GeoDataFrame(geometry=[wszystkie_wykluczenia], crs=clc_gdf.crs)
