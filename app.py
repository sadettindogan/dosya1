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
        
        # Eski liste formatındaki kayıtları otomatik yeni dosya formatına dönüştürme
        yeni_format_data = []
        if isinstance(data, list):
            for item in data:
                # Eğer veri eski basitleştirilmiş yapıdaysa
                if "Islemler" not in item and "Dosya No" in item:
                    d_no = str(item.get("Dosya No"))
                    tarih = item.get("Tarih", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    islem_text = item.get("Yapılan İşlem", "Kayıt detay yok")
                    
                    # Var olan dosyaya mı eklenecek kontrolü
                    mevcut = next((x for x in yeni_format_data if x["Dosya No"] == d_no), None)
                    if mevcut:
                        mevcut["Islemler"].append({"Aciklama": islem_text, "Tarih": tarih})
                    else:
                        yeni_format_data.append({
                            "Dosya No": d_no,
                            "OlusturmaTarihi": tarih,
                            "Islemler": [{"Aciklama": islem_text, "Tarih": tarih}]
                        })
                else:
                    yeni_format_data.append(item)
            return yeni_format_data
        return []
    except Exception:
        return []

def verileri_kaydet(yeni_kayitlar, mesaj):
    yeni_json_icerik = json.dumps(yeni_kayitlar, ensure_ascii=False, indent=2)
    try:
        file_content = repo.get_contents(FILE_PATH)
        repo.update_file(
            path=FILE_PATH,
            message=mesaj,
            content=yeni_json_icerik,
            sha=file_content.sha
        )
    except Exception:
        repo.create_file(
            path=FILE_PATH,
            message=mesaj,
            content=yeni_json_icerik
        )

kayitlar = verileri_getir()

# --- YENİ DOSYA OLUŞTURMA FORMU ---
st.subheader("➕ Yeni Dosya Oluştur")

with st.form("yeni_dosya_formu", clear_on_submit=True):
    dosya_no = st.text_input("Dosya No")
    islem = st.text_area("İlk İşlem / Açıklama")
    submit_yeni = st.form_submit_button("Dosyayı ve İlk İşlemi Kaydet")

    if submit_yeni:
        if dosya_no.strip() != "" and islem.strip() != "":
            clean_dosya = dosya_no.strip()
            turkey_tz = pytz.timezone("Europe/Istanbul")
            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")

            # Dosya zaten var mı kontrolü
            mevcut = any(str(d.get("Dosya No")) == clean_dosya for d in kayitlar)
            
            if mevcut:
                st.warning(f"'{clean_dosya}' numaralı dosya zaten mevcut. Aşağıdaki listeden dosya kartını açarak yeni işlem ekleyebilirsiniz.")
            else:
                yeni_dosya = {
                    "Dosya No": clean_dosya,
                    "OlusturmaTarihi": simdi,
                    "Islemler": [
                        {
                            "Aciklama": islem,
                            "Tarih": simdi
                        }
                    ]
                }
                kayitlar.append(yeni_dosya)
                verileri_kaydet(kayitlar, f"Yeni dosya eklendi: {clean_dosya}")
                st.success(f"'{clean_dosya}' numaralı dosya ve ilk işlemi oluşturuldu!")
                st.rerun()
        else:
            st.warning("Lütfen Dosya No ve İşlem alanlarını doldurun.")

# --- İZLEME VE İŞLEM EKLEME/SİLME EKRANI ---
st.divider()
st.subheader("📋 Kayıtlı Dosyalar")

arama = st.text_input("Dosya No ile Arama Yap", "")

if kayitlar:
    sirali_dosyalar = sorted(kayitlar, key=lambda x: x.get("OlusturmaTarihi", ""), reverse=True)
    
    if arama:
        gosterilecek_dosyalar = [d for d in sirali_dosyalar if arama.lower() in str(d.get("Dosya No", "")).lower()]
    else:
        gosterilecek_dosyalar = sirali_dosyalar

    if gosterilecek_dosyalar:
        for d_idx, dosya in enumerate(gosterilecek_dosyalar):
            d_no = dosya.get("Dosya No")
            islemler = dosya.get("Islemler", [])
            
            with st.expander(f"📁 **Dosya No: {d_no}** (Toplam {len(islemler)} İşlem)", expanded=False):
                
                # Dosya içi işlem ekleme formu
                with st.form(key=f"add_islem_form_{d_no}_{d_idx}", clear_on_submit=True):
                    yeni_islem_text = st.text_input("Bu dosyaya yeni kayıt ekle")
                    submit_islem = st.form_submit_button("➕ Kayıt Ekle")
                    
                    if submit_islem:
                        if yeni_islem_text.strip() != "":
                            turkey_tz = pytz.timezone("Europe/Istanbul")
                            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                            
                            islemler.append({
                                "Aciklama": yeni_islem_text.strip(),
                                "Tarih": simdi
                            })
                            
                            verileri_kaydet(kayitlar, f"{d_no} dosyasına yeni işlem eklendi")
                            st.success("Yeni işlem başarıyla eklendi!")
                            st.rerun()
                        else:
                            st.warning("Lütfen işlem açıklamasını girin.")

                st.markdown("---")
                st.markdown("**Yapılan Geçmiş Kayıtlar:**")
                
                for i_idx, item in enumerate(islemler):
                    col_info, col_del = st.columns([6, 1])
                    
                    with col_info:
                        st.markdown(f"**{i_idx + 1}. Kayıt:** {item.get('Aciklama')}")
                        st.caption(f"🕒 *Tarih/Saat:* {item.get('Tarih')}")
                    
                    with col_del:
                        if st.button("🗑️ Sil", key=f"del_{d_no}_{i_idx}"):
                            islemler.pop(i_idx)
                            
                            if len(islemler) == 0:
                                kayitlar.remove(dosya)
                                
                            verileri_kaydet(kayitlar, f"{d_no} dosyasından işlem silindi")
                            st.success("Kayıt silindi!")
                            st.rerun()
                    
                    if i_idx < len(islemler) - 1:
                        st.divider()
            st.write("") 
    else:
        st.info("Aramanıza uygun dosya bulunamadı.")
else:
    st.info("Henüz kayıtlı dosya bulunmuyor.")
