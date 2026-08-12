import streamlit as st
import pandas as pd
from datetime import datetime
import json
import pytz
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
                            "Firma": item.get("Firma", "-"),
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
        arama = st.text_input("🔍 Dosya No veya Firma ile Ara", "", placeholder="Örn: 1001 veya Firma Adı")

    if kayitlar:
        sirali_dosyalar = sorted(kayitlar, key=lambda x: x.get("OlusturmaTarihi", ""), reverse=True)
        
        if arama:
            gosterilecek_dosyalar = [
                d for d in sirali_dosyalar 
                if arama.lower() in str(d.get("Dosya No", "")).lower() or arama.lower() in str(d.get("Firma", "")).lower()
            ]
        else:
            gosterilecek_dosyalar = sirali_dosyalar

        if gosterilecek_dosyalar:
            for d_idx, dosya in enumerate(gosterilecek_dosyalar):
                d_no = dosya.get("Dosya No")
                firma = dosya.get("Firma", "-")
                islemler = dosya.get("Islemler", [])
                
                with st.expander(f"📂 **Dosya No:** {d_no} | 🏢 **Firma:** {firma} ({len(islemler)} İşlem)", expanded=False):
                    
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
            dosya_no = st.text_input("Dosya No / Adı (1.-3. Sütun Bilişimi)", placeholder="Örn: 2026 IST 101")
            firma = st.text_input("Firma Adı (4. Sütun)", placeholder="Örn: ABC Dış Ticaret A.Ş.")
            islem = st.text_area("İlk İşlem Açıklaması (5. Sütun)", placeholder="Dosya için başlatılan ilk işlemi girin...", height=80)
            submit_yeni = st.form_submit_button("📂 Dosya Oluştur", use_container_width=True)

            if submit_yeni:
                if dosya_no.strip() != "" and islem.strip() != "":
                    clean_dosya = dosya_no.strip()
                    clean_firma = firma.strip() if firma.strip() != "" else "-"
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
                            "Firma": clean_firma,
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
                    st.warning("Lütfen Dosya No ve Açıklama alanlarını doldurun.")

    # 2. EXCEL'DEN TOPLU VERİ YAPIŞTIRMA SEKMESİ (5 SÜTUNLU YAPININ İŞLENMESİ)
    with tab_excel:
        st.caption("Excel'de seçtiğiniz **5 Sütunu** kopyalayıp aşağıdaki kutuya yapıştırın:")
        st.caption("📌 **Sütun Düzeyi:** `1.Parça` | `2.Parça` | `3.Parça` | `Firma Adı` | `Açıklama`")
        
        with st.form("excel_paste_form", clear_on_submit=True):
            pasted_data = st.text_area("Excel Verisini Buraya Yapıştırın", placeholder="2026\tIST\t101\tABC Lojistik\tAçıklama metni", height=120)
            submit_excel = st.form_submit_button("⚡ Toplu Verileri Kaydet", use_container_width=True)
            
            if submit_excel:
                if pasted_data.strip() != "":
                    turkey_tz = pytz.timezone("Europe/Istanbul")
                    eklenen_sayi = 0
                    
                    lines = pasted_data.strip().split("\n")
                    for line in lines:
                        parts = line.split("\t")
                        # 5 Sütunluk yapının ayrıştırılması
                        if len(parts) >= 5:
                            sutun1 = parts[0].strip()
                            sutun2 = parts[1].strip()
                            sutun3 = parts[2].strip()
                            c_firma = parts[3].strip()
                            c_islem = parts[4].strip()
                            
                            # İlk 3 sütunu arada boşluk olacak şekilde birleştirme
                            c_dno = " ".join(filter(None, [sutun1, sutun2, sutun3]))
                            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                            
                            if c_dno and c_islem:
                                mevcut = next((d for d in kayitlar if str(d.get("Dosya No")) == c_dno), None)
                                if mevcut:
                                    mevcut["Islemler"].append({
                                        "Aciklama": c_islem,
                                        "Tarih": simdi
                                    })
                                    # Firma boşsa güncelle
                                    if c_firma and mevcut.get("Firma") in ["-", ""]:
                                        mevcut["Firma"] = c_firma
                                else:
                                    kayitlar.append({
                                        "Dosya No": c_dno,
                                        "Firma": c_firma if c_firma else "-",
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
                        st.warning("Geçerli formatta veri bulunamadı. Lütfen en az 5 sütun seçip kopyaladığınızdan emin olun.")
                else:
                    st.warning("Yapıştırılan alan boş olamaz.")

    st.divider()
    st.markdown("##### 💡 Kullanım İpuçları")
    st.caption("• Excel yapıştırmada ilk 3 sütun otomatikleştirilerek tek bir dosya adına dönüştürülür.")
    st.caption("• Aynı dosya numarasıyla denk gelen satırlarda yeni işlem adımı otomatik alt alta dizilir.")
