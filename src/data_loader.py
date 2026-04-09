import os
import rasterio
import numpy as np
import tempfile
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import streamlit as st

def load_elevation_data(file_path):
    """(Oryginalna funkcja do testów offline z Twojego kodu)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ BŁĄD: Nie znaleziono pliku pod ścieżką: {file_path}")
    with rasterio.open(file_path) as dataset:
        elevation_matrix = dataset.read(1)
        metadata = dataset.profile
        nodata_value = dataset.nodata
        if nodata_value is not None:
            elevation_matrix = elevation_matrix.astype(np.float32)
            elevation_matrix[elevation_matrix == nodata_value] = np.nan
    return elevation_matrix, metadata

def wczytaj_raster_z_uploadu(uploaded_file):
    """
    NOWA WERSJA: Automatycznie radzi sobie z plikami NMT z Geoportalu.
    Rozpakowuje pliki .zip i szuka w nich modeli .tif lub .asc.
    """
    if uploaded_file is None:
        return None, None, None
        
    nazwa_pliku = uploaded_file.name
    temp_dir = tempfile.mkdtemp()
    
    try:
        temp_file_path = os.path.join(temp_dir, nazwa_pliku)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        plik_do_otwarcia = temp_file_path

        # Jeśli wgrano ZIP (Geoportal niemal zawsze pakuje w ZIP)
        if nazwa_pliku.lower().endswith('.zip'):
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            znaleziony_raster = None
            # Przeszukujemy rozpakowane pliki w poszukiwaniu TIF lub ASC
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.tif', '.tiff', '.asc')):
                        znaleziony_raster = os.path.join(root, file)
                        break
                if znaleziony_raster:
                    break
                    
            if znaleziony_raster:
                plik_do_otwarcia = znaleziony_raster
            else:
                st.error("❌ W wgranej paczce ZIP nie znaleziono żadnego modelu wysokości (brak pliku .tif lub .asc)!")
                return None, None, None

        # Otwieramy prawdziwy raster
        with rasterio.open(plik_do_otwarcia) as src:
            macierz_wysokosci = src.read(1)  
            transform = src.transform  
            crs = src.crs   
            nodata = src.nodata
            
            macierz_wysokosci = macierz_wysokosci.astype(np.float32)
            
            # Usuwamy wartości puste/NoData z Geoportalu
            if nodata is not None:
                macierz_wysokosci[macierz_wysokosci == nodata] = np.nan
            # Zabezpieczenie przed tzw. "dziurami" (Geoportal czasem wstawia -9999 jako nodata w plikach .asc)
            macierz_wysokosci[macierz_wysokosci < -100] = np.nan 

        return macierz_wysokosci, transform, crs
        
    except Exception as e:
        st.error(f"❌ Błąd podczas otwierania pliku NMT: {e}")
        return None, None, None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def _bezpieczny_odczyt_wektora(sciezka):
    """Bezpiecznie wczytuje warstwy BDOT (ignoruje puste pliki w których nie ma poligonów)."""
    try:
        gdf = gpd.read_file(sciezka)
        if gdf.empty:
            return None
        return gdf
    except Exception:
        return None

def wczytaj_wektor_z_uploadu(uploaded_file, slowo_kluczowe=None):
    if uploaded_file is None:
        return None
        
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
                    if file.lower().endswith(('.shp', '.gpkg')):
                        if slowo_kluczowe:
                            if slowo_kluczowe.lower() in file.lower():
                                znaleziony_plik = os.path.join(root, file)
                                break
                        else:
                            znaleziony_plik = os.path.join(root, file)
                            break
                if znaleziony_plik:
                    break
                    
            if znaleziony_plik:
                return _bezpieczny_odczyt_wektora(znaleziony_plik)
            else:
                return None
                
        elif rozszerzenie in ['.gpkg', '.shp']:
            return _bezpieczny_odczyt_wektora(temp_file_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def wczytaj_wszystkie_warstwy_bdot(uploaded_file):
    if uploaded_file is None:
        return None
        
    nazwa_pliku = uploaded_file.name
    temp_dir = tempfile.mkdtemp()
    
    wyniki = {'budynki': None, 'rekreacja': [], 'wody': None, 'jezdnie': None, 'tory': None}
    
    try:
        temp_file_path = os.path.join(temp_dir, nazwa_pliku)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        if nazwa_pliku.lower().endswith('.zip'):
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.shp', '.gpkg')):
                        file_lower = file.lower()
                        sciezka = os.path.join(root, file)
                        
                        if 'bubd' in file_lower:
                            wyniki['budynki'] = _bezpieczny_odczyt_wektora(sciezka)
                        elif any(x in file_lower for x in ['ptzb', 'kusk', 'ptut']):
                            gdf = _bezpieczny_odczyt_wektora(sciezka)
                            if gdf is not None:
                                wyniki['rekreacja'].append(gdf)
                        elif 'ptwp' in file_lower:
                            wyniki['wody'] = _bezpieczny_odczyt_wektora(sciezka)
                        elif 'skjz' in file_lower:
                            wyniki['jezdnie'] = _bezpieczny_odczyt_wektora(sciezka)
                        elif 'sktr' in file_lower:
                            wyniki['tory'] = _bezpieczny_odczyt_wektora(sciezka)
                            
            if wyniki['rekreacja']:
                wyniki['rekreacja'] = gpd.GeoDataFrame(pd.concat(wyniki['rekreacja'], ignore_index=True))
            else:
                wyniki['rekreacja'] = None
                
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return wyniki