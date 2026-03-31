import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from scipy.stats import norm, gumbel_r

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide", page_title="SDA Hydro-Spatial")

st.title("🌊 SDA HYDRO-SPATIAL PRO")
st.write("Aplikasi Analisis Hidrologi & GIS Interaktif")

# --- FUNGSI HITUNG HIDROLOGI ---
def hitung_hidrologi(data):
    df = pd.DataFrame(data, columns=['hujan'])
    m = df['hujan'].mean()
    s = df['hujan'].std()
    
    periods = [2, 5, 10, 25, 50, 100]
    
    # Perhitungan Normal
    res_n = [m + (norm.ppf(1 - 1/t) * s) for t in periods]
    
    # Perhitungan Gumbel
    res_g = [m + ((gumbel_r.ppf(1 - 1/t) - 0.5772) / 1.2825 * s) for t in periods]
    
    # Perhitungan Log-Pearson III
    log_d = np.log10(df['hujan'])
    lm, ls, lcs = log_d.mean(), log_d.std(), log_d.skew()
    res_lp3 = []
    for t in periods:
        z = norm.ppf(1 - 1/t)
        # Pendekatan faktor K untuk LP3
        if lcs != 0:
            k = (2/lcs) * (((z - lcs/6) * (lcs/6) + 1)**3 - 1)
        else:
            k = z
        res_lp3.append(10**(lm + k * ls))
        
    return pd.DataFrame({
        "T (Tahun)": periods,
        "Normal (mm)": res_n,
        "Gumbel (mm)": res_g,
        "Log-Pearson III (mm)": res_lp3
    })

# --- LAYOUT KOLOM ---
col_map, col_data = st.columns([1.5, 1])

with col_map:
    st.subheader("📍 Peta & Digitasi DAS")
    # Buat Peta Dasar
    m = folium.Map(location=[-6.20, 106.84], zoom_start=12)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                     attr='Esri', name='Satelit').add_to(m)
    
    # Tambahkan fitur menggambar
    Draw(export=True).add_to(m)
    
    # Tampilkan ke Streamlit
    st_folium(m, width="100%", height=500)
    
    st.info("💡 Gunakan toolbar di kiri peta untuk menggambar area DAS secara manual.")

with col_data:
    st.subheader("📊 Input Data Hujan")
    input_hujan = st.text_area("Masukkan Data Hujan Tahunan (pisahkan dengan koma):", 
                               "120, 155, 140, 115, 160, 145, 130")
    
    if st.button("🚀 Jalankan Analisis"):
        try:
            data_list = [float(x.strip()) for x in input_hujan.split(",")]
            hasil_df = hitung_hidrologi(data_list)
            
            st.success("Analisis Berhasil!")
            st.dataframe(hasil_df.style.format(precision=2), use_container_width=True)
            
            # Grafik
            st.line_chart(hasil_df.set_index("T (Tahun)"))
            
        except Exception as e:
            st.error(f"Terjadi kesalahan input: {e}")

# --- FOOTER ---
st.divider()
st.caption("Developed with Streamlit & GeoPandas | 2026")
