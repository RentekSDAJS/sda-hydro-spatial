import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from scipy.stats import norm, gumbel_r

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="SDA HYDRO-SPATIAL")

# --- FUNGSI HITUNG (MATEMATIKA HIDROLOGI) ---
def hitung_hidrologi(data):
    df = pd.DataFrame(data, columns=['hujan'])
    m, s = df['hujan'].mean(), df['hujan'].std()
    periods = [2, 5, 10, 25, 50, 100]
    
    # Normal & Gumbel
    res_n = [m + (norm.ppf(1 - 1/t) * s) for t in periods]
    res_g = [m + ((gumbel_r.ppf(1 - 1/t) - 0.5772) / 1.2825 * s) for t in periods]
    
    # Log-Pearson III
    log_d = np.log10(df['hujan'])
    lm, ls, lcs = log_d.mean(), log_d.std(), log_d.skew()
    res_lp3 = []
    for t in periods:
        z = norm.ppf(1 - 1/t)
        k = (2/lcs) * (((z - lcs/6) * (lcs/6) + 1)**3 - 1) if lcs != 0 else z
        res_lp3.append(10**(lm + k * ls))
        
    return pd.DataFrame({
        "T (Tahun)": periods,
        "Normal (mm)": res_n,
        "Gumbel (mm)": res_g,
        "Log-Pearson III (mm)": res_lp3
    })

# --- UI STREAMLIT ---
st.title("🌊 SDA HYDRO-SPATIAL ULTIMATE")

col_peta, col_data = st.columns([1.5, 1])

with col_peta:
    st.subheader("📍 Peta Digital & SHP")
    # Base Map
    m = folium.Map(location=[-6.20, 106.84], zoom_start=13)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                     attr='Esri', name='Satelit').add_to(m)
    
    # Fitur Gambar Catchment
    Draw(export=True).add_to(m)
    
    # Upload SHP (.zip)
    up = st.file_uploader("Upload SHP (.zip)", type=['zip'])
    if up:
        gdf = gpd.read_file(up)
        folium.GeoJson(gdf, name="Layer SHP").add_to(m)
        st.success("SHP Terpasang!")

    st_folium(m, width="100%", height=500)

with col_data:
    st.subheader("📊 Analisis Curah Hujan")
    input_hujan = st.text_area("Input Hujan (koma):", "120, 150, 110, 135, 140")
    arr_hujan = [float(x.strip()) for x in input_hujan.split(",")]
    
    if st.button("Jalankan Analisis"):
        hasil = hitung_hidrologi(arr_hujan)
        st.dataframe(hasil.style.format(precision=2))
        st.line_chart(hasil.set_index('T (Tahun)'))
