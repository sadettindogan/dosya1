import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dosya Takip Sistemi", layout="centered")

st.title("📁 Dosya İşlem Kayıt Sistemi")

# Google Sheets Bağlantısı
conn = st.connection("gsheets", type=GSheetsConnection)

# Mevcut veriyi çekme
try:
    df = conn.read(ttl=0)
except Exception:
    df = pd.DataFrame(columns=["Tarih", "Dosya No", "Yapılan İşlem"])

# --- KAYIT FORMU ---
st.subheader("Yeni İşlem Ekle")

with st.form("kayit_formu", clear_on_submit=True):
    dosya_no = st.text_input("Dosya No")
    islem = st.text_area("Yapılan İşlem")
    submit = st.form_submit_button("Kaydet")

    if submit:
        if dosya_no.strip() != "" and islem.strip() != "":
            # Otomatik Tarih ve Saat alma
            simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Yeni veriyi hazırlama
            yeni_veri = pd.DataFrame([{
                "Tarih": simdi,
                "Dosya No": dosya_no,
                "Yapılan İşlem": islem
            }])
            
            # Var olan tabloyla birleştirip Google Sheets'e yazma
            updated_df = pd.concat([df, yeni_veri], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success(f"'{dosya_no}' numaralı dosya işlemi başarıyla kaydedildi!")
            st.rerun()
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# --- İZLEME VE GEÇMİŞ EKRANI ---
st.divider()
st.subheader("📋 Geçmiş Kayıtlar")

# Arama / Filtreleme
arama = st.text_input("Dosya No ile Arama Yap", "")

if not df.empty:
    if arama:
        filtreli_df = df[df["Dosya No"].astype(str).str.contains(arama, case=False, na=False)]
        st.dataframe(filtreli_df, use_container_width=True)
    else:
        st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True)
else:
    st.info("Henüz kayıt bulunmuyor.")