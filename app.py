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

# Düzenleme modunu kontrol etmek için Session State kullanımı
if "editing_target" not in st.session_state:
    st.session_state.editing_target = None

# --- KAYIT / DÜZENLEME FORMU ---
if st.session_state.editing_target:
    st.subheader("✏️ Kaydı Düzenle")
    default_dosya = st.session_state.editing_target.get("Dosya No", "")
    default_islem = st.session_state.editing_target.get("Yapılan İşlem", "")
else:
    st.subheader("➕ Yeni İşlem Ekle")
    default_dosya = ""
    default_islem = ""

with st.form("kayit_formu", clear_on_submit=True):
    dosya_no = st.text_input("Dosya No", value=default_dosya)
    islem = st.text_area("Yapılan İşlem", value=default_islem)
    
    col_submit1, col_submit2 = st.columns([1, 1])
    with col_submit1:
        submit = st.form_submit_button("Güncelle" if st.session_state.editing_target else "Kaydet")
    with col_submit2:
        if st.session_state.editing_target:
            cancel = st.form_submit_button("İptal Et")
            if cancel:
                st.session_state.editing_target = None
                st.rerun()

    if submit:
        if dosya_no.strip() != "" and islem.strip() != "":
            turkey_tz = pytz.timezone("Europe/Istanbul")
            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            # Eğer DÜZENLEME modundaysak eski kaydı güncelle
            if st.session_state.editing_target:
                target_tarih = st.session_state.editing_target.get("Tarih")
                for k in kayitlar:
                    if k.get("Tarih") == target_tarih:
                        k["Dosya No"] = dosya_no
                        k["Yapılan İşlem"] = islem
                        # Opsiyonel: Güncelleme tarihini eklemek isterseniz: k["Tarih"] = simdi
                        break
                verileri_kaydet(kayitlar, file_sha, f"Kayıt güncellendi: {dosya_no}")
                st.session_state.editing_target = None
                st.success("Kayıt başarıyla güncellendi!")
            else:
                # Yeni Kayıt Ekleme
                yeni_kayit = {
                    "Tarih": simdi,
                    "Dosya No": dosya_no,
                    "Yapılan İşlem": islem
                }
                kayitlar.append(yeni_kayit)
                verileri_kaydet(kayitlar, file_sha, f"Yeni kayıt eklendi: {dosya_no}")
                st.success(f"'{dosya_no}' numaralı dosya işlemi eklendi!")
            
            st.rerun()
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# --- İZLEME, DÜZENLEME VE SİLME EKRANI ---
st.divider()
st.subheader("📋 Geçmiş Kayıtlar")

arama = st.text_input("Dosya No ile Arama Yap", "")

if kayitlar:
    sirali_kayitlar = sorted(kayitlar, key=lambda x: x.get("Tarih", ""), reverse=True)
    
    if arama:
        gosterilecek_kayitlar = [k for k in sirali_kayitlar if arama.lower() in str(k.get("Dosya No", "")).lower()]
    else:
        gosterilecek_kayitlar = sirali_kayitlar

    if gosterilecek_kayitlar:
        for idx, kayit in enumerate(gosterilecek_kayitlar):
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.markdown(f"**Dosya No:** `{kayit.get('Dosya No')}` | **Tarih:** {kayit.get('Tarih')}")
                    st.write(f"**İşlem:** {kayit.get('Yapılan İşlem')}")
                
                with col2:
                    if st.button("✏️ Düzenle", key=f"edit_{kayit.get('Tarih')}_{idx}"):
                        st.session_state.editing_target = kayit
                        st.rerun()

                with col3:
                    if st.button("🗑️ Sil", key=f"delete_{kayit.get('Tarih')}_{idx}"):
                        kayitlar.remove(kayit)
                        verileri_kaydet(kayitlar, file_sha, f"Kayıt silindi: {kayit.get('Dosya No')}")
                        if st.session_state.editing_target == kayit:
                            st.session_state.editing_target = None
                        st.success("Kayıt silindi!")
                        st.rerun()
                st.divider()
    else:
        st.info("Aramanıza uygun kayıt bulunamadı.")
else:
    st.info("Henüz kayıt bulunmuyor.")
