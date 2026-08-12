import streamlit as st
import pandas as pd
from datetime import datetime
import json
import pytz
import io
from github import Github

# Sayfa Yapılandırması (Geniş Ekran)
st.set_page_config(
    page_title="Dosya Takibi", 
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📁 Dosya Takibi")
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

# EKRAN YAPILANDIRMASI: Sol Taraf %65, Sağ Taraf %35
col_left, col_right = st.columns([65, 35], gap="large")

# ==============================================================================
# SOL TARAF: GENİŞ DOSYA LİSTESİ VE GEÇMİŞ İŞLEMLER
# ==============================================================================
with col_left:
    st.subheader("📋 Kayıtlı Dosyalar ve İşlem Akışı")
    
    search_col, _ = st.columns([1, 2])
    with search_col:
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
                
                with st.expander(f"📂 DOSYA NO: **{d_no}** | (Toplam {len(islemler)} İşlem Adımı)", expanded=False):
                    
                    st.markdown(f"**➕ `{d_no}` Nolu Dosyaya Yeni İşlem Ekle**")
                    
                    with st.form(key=f"add_islem_form_main_{d_no}_{d_idx}", clear_on_submit=True):
                        col_inp, col_btn = st.columns([3, 1], vertical_alignment="center")
                        
                        with col_inp:
                            yeni_islem_text = st.text_input("İşlem Açıklaması", key=f"inp_{d_no}_{d_idx}", placeholder="Yapılan işlemi yazınız...", label_visibility="collapsed")
                        
                        with col_btn:
                            submit_islem = st.form_submit_button("➕ İşlem Ekle", use_container_width=True)
                            
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
                                st.warning("Açıklama boş olamaz.")

                    st.markdown("---")
                    st.markdown("##### 🕒 Dosyada bugüne kadar yapılan işlemler")
                    
                    for i_idx, item in enumerate(islemler):
                        c_text, c_date, c_del = st.columns([5, 3, 1], vertical_alignment="center")
                        
                        with c_text:
                            st.markdown(f"**{i_idx + 1}. Adım:** {item.get('Aciklama')}")
                        
                        with c_date:
                            st.caption(f"🗓️ {item.get('Tarih')}")
                        
                        with c_del:
                            if st.button("🗑️ Sil", key=f"del_main_{d_no}_{i_idx}", help="Bu işlemi sil"):
                                islemler.pop(i_idx)
                                
                                if len(islemler) == 0:
                                    kayitlar.remove(dosya)
                                    
                                verileri_kaydet(kayitlar, f"{d_no} dosyasından işlem silindi")
                                st.success("Silindi!")
                                st.rerun()
                st.write("") 
        else:
            st.info("Arama kriterinize uygun dosya bulunamadı.")
    else:
        st.info("Sistemde henüz kayıtlı dosya bulunmuyor.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA VEYA TOPLU EXCEL VERİ GİRİŞİ PANELİ
# ==============================================================================
with col_right:
    st.subheader("📌 Veri Girişi & Yeni Dosya")
    
    tab_tekli, tab_excel = st.tabs(["✏️ Tekli Dosya Ekle", "📋 Excel'den Toplu Yapıştır"])
    
    # 1. TEKLİ DOSYA EKLEME SEKMESİ
    with tab_tekli:
        with st.form("yeni_dosya_formu_sag", clear_on_submit=True):
            col_dno, col_btn_tek = st.columns([2, 1], vertical_alignment="bottom")
            with col_dno:
                dosya_no = st.text_input("Dosya No", placeholder="Örn: 2026-101")
            with col_btn_tek:
                submit_yeni = st.form_submit_button("📂 Dosya Oluştur", use_container_width=True)
                
            islem = st.text_area("İlk İşlem Açıklaması", placeholder="Dosya için başlatılan ilk işlemi girin...", height=80)

            if submit_yeni:
                if dosya_no.strip() != "" and islem.strip() != "":
                    clean_dosya = dosya_no.strip()
                    turkey_tz = pytz.timezone("Europe/Istanbul")
                    simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")

                    mevcut = next((d for d in kayitlar if str(d.get("Dosya No")) == clean_dosya), None)
                    
                    if mevcut:
                        islem_no = len(mevcut["Islemler"]) + 1
                        mevcut["Islemler"].append({
                            "Aciklama": islem.strip(),
                            "Tarih": simdi
                        })
                        verileri_kaydet(kayitlar, f"{clean_dosya} dosyasına {islem_no}. işlem eklendi")
                        st.success(f"'{clean_dosya}' dosyasına yeni işlem eklendi!")
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
                    st.warning("Lütfen hem Dosya No hem de işlem açıklamasını girin.")

    # 2. EXCEL'DEN TOPLU VERİ YAPIŞTIRMA SEKMESİ
    with tab_excel:
        st.caption("Excel'de seçtiğiniz **2 Sütunu (1.Sütun: Dosya No | 2.Sütun: Açıklama)** kopyalayıp aşağıdaki kutuya yapıştırın:")
        
        with st.form("excel_paste_form", clear_on_submit=True):
            pasted_data = st.text_area("Excel Verisini Buraya Yapıştırın", placeholder="1001\tAçıklama 1\n1002\tAçıklama 2", height=120)
            submit_excel = st.form_submit_button("⚡ Toplu Verileri Kaydet", use_container_width=True)
            
            if submit_excel:
                if pasted_data.strip() != "":
                    turkey_tz = pytz.timezone("Europe/Istanbul")
                    eklenen_sayi = 0
                    
                    # Satır satır okuma
                    lines = pasted_data.strip().split("\n")
                    for line in lines:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            c_dno = parts[0].strip()
                            c_islem = parts[1].strip()
                            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                            
                            if c_dno and c_islem:
                                mevcut = next((d for d in kayitlar if str(d.get("Dosya No")) == c_dno), None)
                                if mevcut:
                                    mevcut["Islemler"].append({
                                        "Aciklama": c_islem,
                                        "Tarih": simdi
                                    })
                                else:
                                    kayitlar.append({
                                        "Dosya No": c_dno,
                                        "OlusturmaTarihi": simdi,
                                        "Islemler": [{
                                            "Aciklama": c_islem,
                                            "Tarih": simdi
                                        }]
                                    })
                                eklenen_sayi += 1
                                
                    if eklenen_sayi > 0:
                        verileri_kaydet(kayitlar, f"Excel'den {eklenen_sayi} adet kayıt eklendi")
                        st.success(f"Toplam {eklenen_sayi} adet dosya/işlem kaydı işlendi!")
                        st.rerun()
                    else:
                        st.warning("Geçerli formatta veri bulunamadı. 2 sütun kopyaladığınızdan emin olun.")
                else:
                    st.warning("Yapıştırılan alan boş olamaz.")

    st.divider()
    st.markdown("##### 💡 Kullanım İpuçları")
    st.caption("• Tekli girişte Dosya No daha önceden varsa otomatik yeni işlem adımı olarak altına eklenir.")
    st.caption("• Excel yapıştırma özelliğinde başlık satırı dahil etmeden kopyalama yapabilirsiniz.")
