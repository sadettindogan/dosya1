import streamlit as st
import pandas as pd
from datetime import datetime
import json
import pytz
from github import Github

# Sayfa Yapılandırması (Geniş Ekran)
st.set_page_config(
    page_title="Dosya Takip Portalı", 
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📁 Dosya İşlem ve Takip Portalı")
st.markdown("---")

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
        
        yeni_format_data = []
        if isinstance(data, list):
            for item in data:
                if "Islemler" not in item and "Dosya No" in item:
                    d_no = str(item.get("Dosya No"))
                    tarih = item.get("Tarih", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    islem_text = item.get("Yapılan İşlem", "Kayıt detay yok")
                    
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

# EKRAN YAPILANDIRMASI: Sol Taraf %68 (Büyük Takip Alanı), Sağ Taraf %32 (Hızlı İşlem Paneli)
col_left, col_right = st.columns([68, 32], gap="large")

# ==============================================================================
# SOL TARAF: GENİŞ DOSYA LİSTESİ VE GEÇMİŞ İŞLEMLER
# ==============================================================================
with col_left:
    st.subheader("📋 Kayıtlı Dosyalar ve İşlem Akışı")
    
    arama = st.text_input("🔍 Dosya No ile Filtrele / Ara", "", placeholder="Örn: 1001")

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
                
                # Kurumsal Kart Görünümü (Genel Bilgiler Header)
                with st.expander(f"📂 DOSYA NO: **{d_no}** | (Toplam {len(islemler)} İşlem Adımı)", expanded=False):
                    
                    # Dosya içine doğrudan yeni işlem ekleme alanı
                    with st.form(key=f"add_islem_form_main_{d_no}_{d_idx}", clear_on_submit=True):
                        st.markdown(f"**➕ `{d_no}` Nolu Dosyaya Yeni İşlem Ekle**")
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            yeni_islem_text = st.text_input("İşlem Açıklaması", key=f"inp_{d_no}_{d_idx}", label_visibility="collapsed", placeholder="Yapılan işlemi yazınız...")
                        with c2:
                            submit_islem = st.form_submit_button("Kaydet", use_container_width=True)
                        
                        if submit_islem:
                            if yeni_islem_text.strip() != "":
                                turkey_tz = pytz.timezone("Europe/Istanbul")
                                simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                                
                                islemler.append({
                                    "Aciklama": yeni_islem_text.strip(),
                                    "Tarih": simdi
                                })
                                
                                verileri_kaydet(kayitlar, f"{d_no} dosyasına yeni işlem eklendi")
                                st.success("İşlem başarıyla eklendi!")
                                st.rerun()
                            else:
                                st.warning("İşlem açıklaması boş olamaz.")

                    st.markdown("---")
                    st.markdown("##### 🕒 Geçmiş İşlem Zaman Çizelgesi")
                    
                    # Geçmiş İşlemler
                    for i_idx, item in enumerate(islemler):
                        c_info, c_del = st.columns([9, 1])
                        
                        with c_info:
                            st.markdown(f"**{i_idx + 1}. Adım:** {item.get('Aciklama')}")
                            st.caption(f"🗓️ *Tarih / Saat:* {item.get('Tarih')}")
                        
                        with c_del:
                            if st.button("🗑️ Sil", key=f"del_main_{d_no}_{i_idx}", help="Bu işlemi sil"):
                                islemler.pop(i_idx)
                                
                                if len(islemler) == 0:
                                    kayitlar.remove(dosya)
                                    
                                verileri_kaydet(kayitlar, f"{d_no} dosyasından işlem silindi")
                                st.success("Silindi!")
                                st.rerun()
                        
                        if i_idx < len(islemler) - 1:
                            st.divider()
                st.write("") # Küçük boşluk
        else:
            st.info("Arama kriterinize uygun dosya bulunamadı.")
    else:
        st.info("Sistemde henüz kayıtlı dosya bulunmuyor. Sağ taraftaki panelden yeni dosya oluşturabilirsiniz.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA OLUŞTURMA VE BİLGİ PANELİ
# ==============================================================================
with col_right:
    st.subheader("📌 Yeni Dosya Tanımla")
    
    with st.form("yeni_dosya_formu_sag", clear_on_submit=True):
        dosya_no = st.text_input("Dosya No", placeholder="Örn: 2026-101")
        islem = st.text_area("İlk İşlem Açıklaması", placeholder="Dosya için başlatılan ilk işlemi girin...")
        submit_yeni = st.form_submit_button("📂 Yeni Dosya Oluştur", use_container_width=True)

        if submit_yeni:
            if dosya_no.strip() != "" and islem.strip() != "":
                clean_dosya = dosya_no.strip()
                turkey_tz = pytz.timezone("Europe/Istanbul")
                simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")

                mevcut = any(str(d.get("Dosya No")) == clean_dosya for d in kayitlar)
                
                if mevcut:
                    st.warning(f"⚠️ '{clean_dosya}' nolu dosya zaten var. Sol taraftaki arama çubuğunu kullanarak dosyayı bulabilir ve yeni işlem ekleyebilirsiniz.")
                else:
                    yeni_dosya = {
                        "Dosya No": clean_dosya,
                        "OlusturmaTarihi": simdi,
                        "Islemler": [
                            {
                                "Aciklama": islem.strip(),
                                "Tarih": simdi
                            }
                        ]
                    }
                    kayitlar.append(yeni_dosya)
                    verileri_kaydet(kayitlar, f"Yeni dosya eklendi: {clean_dosya}")
                    st.success(f"'{clean_dosya}' nolu dosya başarıyla oluşturuldu!")
                    st.rerun()
            else:
                st.warning("Lütfen hem Dosya No hem de ilk işlem alanını doldurun.")

    st.divider()
    st.markdown("##### 💡 Kullanım İpuçları")
    st.caption("• Mükerrer kayıt engellemek için sistem dosya numaralarını otomatik kontrol eder.")
    st.caption("• Dosya üzerindeki herhangi bir işlem adımını sildiğinizde değişiklik anında GitHub veritabanına yansır.")
