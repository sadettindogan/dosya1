import streamlit as st
import pandas as pd
import json
import os

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Dosya Takip ve Açıklama Yönetimi",
    page_icon="📂",
    layout="wide"
)

VERI_DOSYASI = "data.json"

# --- YARDIMCI FONKSİYONLAR (VERİ OKUMA / KAYIT) ---
def verileri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                return (
                    data.get("kayitlar", []),
                    data.get("onemli_notlar", []),
                    data.get("hatirlatmalar", []),
                    data.get("bolum_sirasi", [])
                )
        except Exception:
            return [], [], [], []
    return [], [], [], []

def verileri_kaydet(kayitlar, onemli_notlar, hatirlatmalar, bolum_sirasi, log_mesaji=""):
    data = {
        "kayitlar": kayitlar,
        "onemli_notlar": onemli_notlar,
        "hatirlatmalar": hatirlatmalar,
        "bolum_sirasi": bolum_sirasi
    }
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Verileri oturuma yükle
kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi = verileri_yukle()

st.title("📂 Dosya Yönetim ve Takip Sistemi")

# --- EXCEL İLE TOPLU AÇIKLAMA GÜNCELLEME SİSTEMİ ---
st.subheader("📑 Excel İle Toplu Açıklama Güncelle")
st.caption("Başlıksız Excel yükleyebilirsiniz (A: Yıl, B: Kod, C: Sıra No, D: Açıklama şeklinde otomatik birleştirilir).")

uploaded_file = st.file_uploader("Excel Dosyası Seçin", type=["xlsx", "xls"], key="excel_updater_input")

if uploaded_file is not None:
    try:
        # Başlıksız oku (header=None)
        df_raw = pd.read_excel(uploaded_file, header=None)
        
        df_upload = pd.DataFrame()
        
        # A, B ve C sütunlarını birleştirerek 'Dosya No' oluştur
        if len(df_raw.columns) >= 3:
            c0 = df_raw[0].fillna('').astype(str).str.strip()
            c1 = df_raw[1].fillna('').astype(str).str.strip()
            c2 = df_raw[2].fillna('').astype(str).str.strip()
            
            # Aralarındaki fazladan boşlukları temizleyerek tek boşlukla birleştir
            df_upload['Dosya No'] = (c0 + " " + c1 + " " + c2).str.replace(r'\s+', ' ', regex=True).str.strip()
        else:
            df_upload['Dosya No'] = df_raw[0].fillna('').astype(str).str.strip()

        # D sütununu Açıklama olarak al
        if len(df_raw.columns) >= 4:
            df_upload['Açıklama'] = df_raw[3].fillna('').astype(str).str.strip()
        elif len(df_raw.columns) >= 2:
            df_upload['Açıklama'] = df_raw[1].fillna('').astype(str).str.strip()
        else:
            df_upload['Açıklama'] = ""

        dosya_no_col = 'Dosya No'
        aciklama_col = 'Açıklama'

        st.success(f"✅ Excel okundu: **{len(df_upload)}** satır veri birleştirildi.")
        
        # Önizleme tablosu
        st.dataframe(df_upload[['Dosya No', 'Açıklama']].head(5), use_container_width=True)

        if st.button("🚀 Excel'deki Verilerle Açıklamaları Güncelle", type="primary", use_container_width=True):
            guncellenen_sayi = 0
            bulunamayanlar = []

            for _, row in df_upload.iterrows():
                target_no = str(row[dosya_no_col]).strip()
                yeni_aciklama = str(row[aciklama_col]).strip() if pd.notna(row[aciklama_col]) else ""

                if target_no:
                    match = next((d for d in kayitlar if str(d.get("Dosya No", "")).strip().lower() == target_no.lower()), None)
                    if match:
                        match["Aciklama"] = yeni_aciklama
                        guncellenen_sayi += 1
                    else:
                        bulunamayanlar.append(target_no)

            if guncellenen_sayi > 0:
                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{guncellenen_sayi} dosya açıklaması Excel ile güncellendi")
                st.toast(f"✅ {guncellenen_sayi} adet dosya açıklaması güncellendi!")
                
            if bulunamayanlar:
                st.warning(f"⚠️ Sistemde eşleşmeyen/bulunamayan dosyalar ({len(bulunamayanlar)} adet): {', '.join(bulunamayanlar)}")
            
            if guncellenen_sayi > 0:
                st.rerun()

    except Exception as e:
        st.error(f"Excel dosyası işlenirken bir hata oluştu: {e}")

st.divider()

# --- MEVCUT KAYITLARI LİSTELEME VE GÖSTERME ---
st.subheader("📋 Kayıtlı Dosyalar")
if kayitlar:
    df_kayitlar = pd.DataFrame(kayitlar)
    st.dataframe(df_kayitlar, use_container_width=True)
else:
    st.info("Henüz kayıtlı bir dosya bulunmamaktadır.")
