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

# Session State kontrolleri (Düzenleme modu için)
if "editing_target" not in st.session_state:
    st.session_state.editing_target = None

# --- KAYIT / İŞLEM EKLEME FORMU ---
if st.session_state.editing_target:
    st.subheader("✏️ İşlem Adımını Düzenle")
    default_dosya = st.session_state.editing_target["dosya_no"]
    default_islem = st.session_state.editing_target["islem_text"]
else:
    st.subheader("➕ Yeni İşlem / Dosya Ekle")
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
            clean_dosya = dosya_no.strip()

            if st.session_state.editing_target:
                # DÜZENLEME MODU: Mevcut adımı güncelle
                t_dosya = st.session_state.editing_target["dosya_no"]
                t_idx = st.session_state.editing_target["islem_idx"]
                
                for dosya in kayitlar:
                    if str(dosya.get("Dosya No")) == str(t_dosya):
                        dosya["Islemler"][t_idx]["Aciklama"] = islem
                        dosya["Islemler"][t_idx]["Tarih"] = f"{simdi} (Düzenlendi)"
                        break
                
                verileri_kaydet(kayitlar, file_sha, f"İşlem güncellendi: {clean_dosya}")
                st.session_state.editing_target = None
                st.success("İşlem adımı başarıyla güncellendi!")
            else:
                # YENİ EKLEME MODU: Dosya var mı kontrol et
                mevcut_dosya = None
                for d in kayitlar:
                    if str(d.get("Dosya No")) == clean_dosya:
                        mevcut_dosya = d
                        break
                
                if mevcut_dosya:
                    # Dosya zaten var, altına yeni işlem adımı ekle
                    islem_no = len(mevcut_dosya["Islemler"]) + 1
                    mevcut_dosya["Islemler"].append({
                        "Adim": islem_no,
                        "Aciklama": islem,
                        "Tarih": simdi
                    })
                    verileri_kaydet(kayitlar, file_sha, f"{clean_dosya} dosyasına {islem_no}. işlem eklendi")
                    st.success(f"'{clean_dosya}' numaralı dosyaya {islem_no}. işlem adımı eklendi!")
                else:
                    # Yeni dosya kaydı ve ilk işlem
                    yeni_dosya_kaydi = {
                        "Dosya No": clean_dosya,
                        "OlusturmaTarihi": simdi,
                        "Islemler": [
                            {
                                "Adim": 1,
                                "Aciklama": islem,
                                "Tarih": simdi
                            }
                        ]
                    }
                    kayitlar.append(yeni_dosya_kaydi)
                    verileri_kaydet(kayitlar, file_sha, f"Yeni dosya eklendi: {clean_dosya}")
                    st.success(f"'{clean_dosya}' numaralı dosya ve 1. işlemi oluşturuldu!")
            
            st.rerun()
        else:
            st.warning("Lütfen tüm alanları doldurun.")

# --- İZLEME VE GEÇMİŞ EKRANI ---
st.divider()
st.subheader("📋 Kayıtlı Dosyalar ve İşlem Geçmişi")

arama = st.text_input("Dosya No ile Arama Yap", "")

if kayitlar:
    # Dosyaları en son işlem gören üstte olacak şekilde sırala
    sirali_dosyalar = sorted(kayitlar, key=lambda x: x.get("OlusturmaTarihi", ""), reverse=True)
    
    if arama:
        gosterilecek_dosyalar = [d for d in sirali_dosyalar if arama.lower() in str(d.get("Dosya No", "")).lower()]
    else:
        gosterilecek_dosyalar = sirali_dosyalar

    if gosterilecek_dosyalar:
        for d_idx, dosya in enumerate(gosterilecek_dosyalar):
            d_no = dosya.get("Dosya No")
            
            with st.expander(f"📁 **Dosya No: {d_no}**", expanded=True):
                islemler = dosya.get("Islemler", [])
                
                for i_idx, islem in enumerate(islemler):
                    col_info, col_edit, col_del = st.columns([5, 1, 1])
                    
                    with col_info:
                        st.markdown(f"**{i_idx + 1}. İşlem:** {islem.get('Aciklama')}")
                        st.caption(f"🕒 *Tarih:* {islem.get('Tarih')}")
                    
                    with col_edit:
                        if st.button("✏️", key=f"edit_{d_no}_{i_idx}"):
                            st.session_state.editing_target = {
                                "dosya_no": d_no,
                                "islem_idx": i_idx,
                                "islem_text": islem.get('Aciklama')
                            }
                            st.rerun()
                            
                    with col_del:
                        if st.button("🗑️", key=f"del_{d_no}_{i_idx}"):
                            islemler.pop(i_idx)
                            # Eğer dosyadaki tüm işlemler silinirse dosyayı tamamen kaldır
                            if len(islemler) == 0:
                                kayitlar.remove(dosya)
                            else:
                                # Adım numaralarını yeniden hizala
                                for n, item in enumerate(islemler):
                                    item["Adim"] = n + 1
                                    
                            verileri_kaydet(kayitlar, file_sha, f"{d_no} dosyasından işlem silindi")
                            st.session_state.editing_target = None
                            st.success("İşlem silindi!")
                            st.rerun()
                    
                    if i_idx < len(islemler) - 1:
                        st.divider()
            st.write("") # Boşluk
    else:
        st.info("Aramanıza uygun dosya bulunamadı.")
else:
    st.info("Henüz kayıtlı dosya bulunmuyor.")
