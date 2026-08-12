import streamlit as st
import pandas as pd
from datetime import datetime
import json
import pytz
from github import Github

# Sayfa Yapılandırması
st.set_page_config(page_title="Dosya Takip Sistemi", layout="centered")

st.title("📁 Dosya İşlem Kayıt Sistemi")

# --- GITHUB BAĞLANTISI VE VERİ OKUMA ---
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
    except Exception:
        return [], None

def verileri_kaydet(yeni_kayitlar, sha, mesaj):
    yeni_json_icerik = json.dumps(yeni_kayitlar, ensure_ascii=False, indent=2)
    if sha:
        repo.update_file(
            path=FILE_PATH,
            message=mesaj,
            content=yeni_json_icerik,
            sha=sha
        )
    else:
        repo.create_file(
            path=FILE_PATH,
            message=mesaj,
            content=yeni_json_icerik
        )

kayitlar, file_sha = verileri_getir()

# --- KAYIT FORMU ---
st.subheader("Yeni İşlem Ekle")

with st.form("kayit_formu", clear_on_submit=True):
    dosya_no = st.text_input("Dosya No")
    islem = st.text_area("Yapılan İşlem")
    submit = st.form_submit_button("Kaydet")

    if submit:
        if dosya_no.strip() != "" and islem.strip() != "":
            turkey_tz = pytz.timezone("Europe/Istanbul")
            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            yeni_kayit = {
                "Tarih": simdi,
                "Dosya No": dosya_no,
                "Yapılan İşlem": islem
            }
            
            kayitlar.append(yeni_kayit)
            verileri_kaydet(kayitlar, file_sha, f"Yeni kayıt eklendi: {dosya_no}")
            
            st.success(f"'{dosya_no}' numaralı dosya işlemi başarıyla kaydedildi!")
            st.rerun()
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# --- İZLEME VE SILME EKRANI ---
st.divider()
st.subheader("📋 Geçmiş Kayıtlar")

arama = st.text_input("Dosya No ile Arama Yap", "")

if kayitlar:
    # Kayıtları tarihe göre ters sıralama (En yeni en üstte)
    sirali_kayitlar = sorted(kayitlar, key=lambda x: x.get("Tarih", ""), reverse=True)
    
    # Arama filtresi
    if arama:
        gosterilecek_kayitlar = [k for k in sirali_kayitlar if arama.lower() in str(k.get("Dosya No", "")).lower()]
    else:
        gosterilecek_kayitlar = sirali_kayitlar

    if gosterilecek_kayitlar:
        for idx, kayit in enumerate(gosterilecek_kayitlar):
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.markdown(f"**Dosya No:** `{kayit.get('Dosya No')}` | **Tarih:** {kayit.get('Tarih')}")
                    st.write(f"**İşlem:** {kayit.get('Yapılan İşlem')}")
                
                with col2:
                    # Her kayıt için benzersiz buton anahtarı
                    if st.button("🗑️ Sil", key=f"delete_{kayit.get('Tarih')}_{idx}"):
                        # Orijinal listeden ilgili kaydı sil
                        kayitlar.remove(kayit)
                        verileri_kaydet(kayitlar, file_sha, f"Kayıt silindi: {kayit.get('Dosya No')}")
                        st.success("Kayıt silindi!")
                        st.rerun()
                st.divider()
    else:
        st.info("Aramanıza uygun kayıt bulunamadı.")
else:
    st.info("Henüz kayıt bulunmuyor.")
