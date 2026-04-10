import os
import rasterio
from rasterio.merge import merge
import numpy as np
import tempfile
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import streamlit as st

def load_elevation_data(file_path):
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

def wczytaj_raster_z_uploadu(uploaded_files):
    """
    Automatycznie łączy (mozaikuje) wiele kafelków NMT.
    Działa ZARÓWNO z paczkami ZIP, jak i luzem rzuconymi plikami .asc / .tif
    """
    if not uploaded_files:
        return None, None, None
        
    # Upewniamy się, że to lista plików
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    temp_dir = tempfile.mkdtemp()
    raster_paths = []
    
    try:
        # 1. Zapisujemy wgrane pliki (.asc lub .zip) do folderu tymczasowego
        for uploaded_file in uploaded_files:
            nazwa_pliku = uploaded_file.name
            temp_file_path = os.path.join(temp_dir, nazwa_pliku)
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Jeśli to ZIP, rozpakowujemy i wywalamy paczkę. Jeśli to .asc - zostaje.
            if nazwa_pliku.lower().endswith('.zip'):
                extract_dir = os.path.join(temp_dir, nazwa_pliku + "_unzipped")
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                os.remove(temp_file_path) 
        
        # 2. Przeczesujemy foldery w poszukiwaniu .asc lub .tif
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(('.tif', '.tiff', '.asc')):
                    raster_paths.append(os.path.join(root, file))
                    
        if not raster_paths:
            st.error("❌ W wgranych plikach/paczkach nie znaleziono żadnego modelu wysokości (.tif lub .asc)!")
            return None, None, None

        # 3. Zszywamy pliki w jeden wielki obszar
        src_files_to_mosaic = []
        for fp in raster_paths:
            src_files_to_mosaic.append(rasterio.open(fp))

        # ŁATKA: Wymuszamy, aby dziury między mapami były "brakiem danych", a nie wys. 0m
        nodata = src_files_to_mosaic[0].nodata
        merge_nodata = nodata if nodata is not None else -9999.0

        mosaic, out_trans = merge(src_files_to_mosaic, nodata=merge_nodata)
        out_crs = src_files_to_mosaic[0].crs

        for src in src_files_to_mosaic:
            src.close()
            
        macierz_wysokosci = mosaic[0].astype(np.float32)
        
        # 4. Docinanie czarnych krawędzi Geoportalu
        macierz_wysokosci[macierz_wysokosci == merge_nodata] = np.nan
        macierz_wysokosci[macierz_wysokosci < -100] = np.nan 

        return macierz_wysokosci, out_trans, out_crs
        
    except Exception as e:
        st.error(f"❌ Błąd podczas łączenia kafelków NMT: {e}")
        return None, None, None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def _bezpieczny_odczyt_wektora(sciezka):
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