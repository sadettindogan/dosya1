import streamlit as st
import pandas as pd
from datetime import datetime
import json
from github import Github

st.set_page_config(page_title="Dosya Takip Sistemi", layout="centered")

st.title("📁 Dosya İşlem Kayıt Sistemi")

# --- GITHUB BAGLANTISI VE VERİ OKUMA ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = st.secrets["FILE_PATH"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def verileri_getir():
    try:
        file_content = repo.get_contents(FILE_PATH)
        data = json.loads(file_content.decoded_content.decode('utf-8'))
        return data, file_content.sha
    except Exception as e:
        return [], None

kayitlar, file_sha = verileri_getir()

# DataFrame oluşturma
if kayitlar:
    df = pd.DataFrame(kayitlar)
else:
    df = pd.DataFrame(columns=["Tarih", "Dosya No", "Yapılan İşlem"])

# --- KAYIT FORMU ---
st.subheader("Yeni İşlem Ekle")

with st.form("kayit_formu", clear_on_submit=True):
    dosya_no = st.text_input("Dosya No")
    islem = st.text_area("Yapılan İşlem")
    submit = st.form_submit_button("Kaydet")

    if submit:
        if dosya_no.strip() != "" and islem.strip() != "":
            # Otomatik Tarih alma
import pytz

# Türkiye saat dilimini tanımlama (UTC+3)
turkey_tz = pytz.timezone("Europe/Istanbul")
simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            yeni_kayit = {
                "Tarih": simdi,
                "Dosya No": dosya_no,
                "Yapılan İşlem": islem
            }
            
            kayitlar.append(yeni_kayit)
            yeni_json_icerik = json.dumps(kayitlar, ensure_ascii=False, indent=2)
            
            # GitHub üzerindeki dosyayı güncelleme (Commit)
            if file_sha:
                repo.update_file(
                    path=FILE_PATH,
                    message=f"Yeni kayıt eklendi: {dosya_no}",
                    content=yeni_json_icerik,
                    sha=file_sha
                )
            else:
                repo.create_file(
                    path=FILE_PATH,
                    message=f"Veri dosyası oluşturuldu ve kayıt eklendi: {dosya_no}",
                    content=yeni_json_icerik
                )
            
            st.success(f"'{dosya_no}' numaralı dosya işlemi başarıyla GitHub'a kaydedildi!")
            st.rerun()
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# --- İZLEME VE GEÇMİŞ EKRANI ---
st.divider()
st.subheader("📋 Geçmiş Kayıtlar")

arama = st.text_input("Dosya No ile Arama Yap", "")

if not df.empty:
    if arama:
        filtreli_df = df[df["Dosya No"].astype(str).str.contains(arama, case=False, na=False)]
        st.dataframe(filtreli_df, use_container_width=True)
    else:
        st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True)
else:
    st.info("Henüz kayıt bulunmuyor.")
