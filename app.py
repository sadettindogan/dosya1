import streamlit as st
import json
import os
import shutil
import base64
from datetime import datetime
import pandas as pd
from io import BytesIO

# ==============================================================================
# SAYFA AYARLARI VE CSS DÜZENLEMELERİ
# ==============================================================================
st.set_page_config(page_title="Gözetim Takip Portalı", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    .card {
        background-color: #ffffff;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .badge-bagli { background-color: #dbeafe; color: #1e40af; }
    .badge-red { background-color: #fee2e2; color: #991b1b; }
    .badge-tescilde { background-color: #fef3c7; color: #92400e; }
    .badge-kapatma { background-color: #d1fae5; color: #065f46; }
    .badge-yazi { background-color: #e0e7ff; color: #3730a3; }
    .badge-incelenmedi { background-color: #f3e8ff; color: #6b21a8; }
    .badge-incelemede { background-color: #ffedd5; color: #9a3412; }
    .badge-mail { background-color: #ccfbf1; color: #115e59; }

    /* Sağ panel sıkılaştırma */
    .stForm > div {
        padding-top: 0.5rem;
    }
    
    /* Toast/Bildirim stilleri */
    .stToast {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    /* Durum Kaydet Butonu için Özel Konumlandırma */
    .save-status-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# VERİ YÖNETİMİ VE DOSYA İŞLEMLERİ
# ==============================================================================
DATA_FILE = "data.json"
BACKUP_DIR = "backups"

def verileri_yukle():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "kayitlar": [],
            "onemli_notlar": [],
            "hatirlatmalar": [],
            "bolum_sirasi": ["Önemli Notlar", "Hatırlatmalar", "İncelemede Olanlar", "İncelenmedi Olanlar", "Diğer Dosyalar"]
        }
        verileri_kaydet(default_data["kayitlar"], default_data["onemli_notlar"], default_data["hatirlatmalar"], default_data["bolum_sirasi"], "İlk Kurulum")
        return default_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "bolum_sirasi" not in data:
                data["bolum_sirasi"] = ["Önemli Notlar", "Hatırlatmalar", "İncelemede Olanlar", "İncelenmedi Olanlar", "Diğer Dosyalar"]
            return data
    except Exception as e:
        st.error(f"Veri yüklenirken hata oluştu: {e}")
        return {
            "kayitlar": [],
            "onemli_notlar": [],
            "hatirlatmalar": [],
            "bolum_sirasi": ["Önemli Notlar", "Hatırlatmalar", "İncelemede Olanlar", "İncelenmedi Olanlar", "Diğer Dosyalar"]
        }

def otomatik_yedek_al(islem_adi="otomatik"):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    yedek_dosya_adi = f"data_backup_{zaman_damgasi}_{islem_adi}.json"
    yedek_yolu = os.path.join(BACKUP_DIR, yedek_dosya_adi)
    
    if os.path.exists(DATA_FILE):
        shutil.copy(DATA_FILE, yedek_yolu)
        
    # En eski yedekleri temizle (Son 10 yedek kalsın)
    yedekler = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith("data_backup_")])
    if len(yedekler) > 10:
        for silinecek in yedekler[:-10]:
            try:
                os.remove(silinecek)
            except:
                pass

def verileri_kaydet(kayitlar, onemli_notlar, hatirlatmalar, bolum_sirasi, islem_adi="güncelleme"):
    data = {
        "kayitlar": kayitlar,
        "onemli_notlar": onemli_notlar,
        "hatirlatmalar": hatirlatmalar,
        "bolum_sirasi": bolum_sirasi,
        "son_guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Önce yedek al
    otomatik_yedek_al(islem_adi.replace(" ", "_"))
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Verileri Yükle
veri = verileri_yukle()
kayitlar = veri.get("kayitlar", [])
mevcut_onemli_notlar = veri.get("onemli_notlar", [])
mevcut_hatirlatmalar = veri.get("hatirlatmalar", [])
mevcut_bolum_sirasi = veri.get("bolum_sirasi", ["Önemli Notlar", "Hatırlatmalar", "İncelemede Olanlar", "İncelenmedi Olanlar", "Diğer Dosyalar"])

# Tarih formatlama için şimdiki zaman
simdi_dt = datetime.now()

# ==============================================================================
# SİDEBAR (YAN PANEL)
# ==============================================================================
with st.sidebar:
    st.title("⚙️ Yönetim Paneli")
    st.markdown("---")

    # ARAMA BÖLÜMÜ
    st.subheader("🔍 Dosya Arama")
    arama_metni = st.text_input("Dosya No veya Firma Adı", placeholder="Aramak için yazın...").strip().lower()

    # DURUM FİLTRELERİ
    st.markdown("---")
    st.subheader("🚩 Durum Filtreleri")
    
    filter_bagli = st.checkbox("🔗 Bağlı Dosyalar")
    filter_red = st.checkbox("🚫 Kapatma Red")
    filter_tescilde = st.checkbox("⏳ Tescilde Bekleyen")
    filter_kapatma = st.checkbox("🏁 Kapatma Aşamasında")
    filter_yazi = st.checkbox("✉️ Yazı Cevabı Bekleyen")
    filter_incelenmedi = st.checkbox("🔍 İncelenmedi")
    filter_incelemede = st.checkbox("🧐 İncelemede")
    filter_mail = st.checkbox("📧 Mail Atıldı")

    # YEDEKLEME VE VERİ AKTARIMI
    st.markdown("---")
    st.subheader("💾 Veri Yönetimi")
    
    # JSON İndir
    json_data = json.dumps(veri, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 Veri Yedeği İndir (JSON)",
        data=json_data,
        file_name=f"gozetim_takip_yedek_{simdi_dt.strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

    # Excel İndir
    if kayitlar:
        df_export = pd.DataFrame(kayitlar)
        # İşlemler listesini metne dönüştür
        if "Islemler" in df_export.columns:
            df_export["Islemler_Metin"] = df_export["Islemler"].apply(lambda x: "\n".join([f"{i.get('Tarih','')}: {i.get('Not','')}" for i in x]) if isinstance(x, list) else "")
            df_export.drop(columns=["Islemler"], inplace=True)
            
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Dosyalar')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📊 Excel Olarak İndir",
            data=excel_data,
            file_name=f"gozetim_dosyalari_{simdi_dt.strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # Veri Yükle
    uploaded_file = st.file_uploader("📂 Yedeği Geri Yükle (JSON)", type=["json"])
    if uploaded_file is not None:
        try:
            imported_data = json.load(uploaded_file)
            if "kayitlar" in imported_data:
                verileri_kaydet(
                    imported_data.get("kayitlar", []),
                    imported_data.get("onemli_notlar", []),
                    imported_data.get("hatirlatmalar", []),
                    imported_data.get("bolum_sirasi", mevcut_bolum_sirasi),
                    "Yedek_Yukleme"
                )
                st.success("Veriler başarıyla yüklendi! Sayfa yenileniyor...")
                st.rerun()
            else:
                st.error("Geçersiz yedek dosyası formatı.")
        except Exception as e:
            st.error(f"Yükleme hatası: {e}")

# ==============================================================================
# ANA SAYFA VE DÜZEN
# ==============================================================================
st.markdown("<div class='main-header'>📦 Gözetim ve Takip Portalı</div>", unsafe_allow_html=True)

# Filtreleme Mantığı
gosterilecek_dosyalar = []
for d in kayitlar:
    # Arama Metni Kontrolü
    metin_uygun = True
    if arama_metni:
        d_no = str(d.get("Dosya No", "")).lower()
        d_firma = str(d.get("Firma", "")).lower()
        d_aciklama = str(d.get("Aciklama", "")).lower()
        metin_uygun = arama_metni in d_no or arama_metni in d_firma or arama_metni in d_aciklama

    # Checkbox Filtreleri Kontrolü
    filtre_uygun = True
    if filter_bagli and not d.get("BagliDosya", False): filtre_uygun = False
    if filter_red and not d.get("KapatmaRed", False): filtre_uygun = False
    if filter_tescilde and not d.get("TescildeBekleyen", False): filtre_uygun = False
    if filter_kapatma and not d.get("KapatmaAsamasinda", False): filtre_uygun = False
    if filter_yazi and not d.get("YaziCevabiBekleyen", False): filtre_uygun = False
    if filter_incelenmedi and not d.get("Incelenmedi", False): filtre_uygun = False
    if filter_incelemede and not d.get("Incelemede", False): filtre_uygun = False
    if filter_mail and not d.get("MailAtildi", False): filtre_uygun = False

    if metin_uygun and filtre_uygun:
        gosterilecek_dosyalar.append(d)

# Layout: Sol Taraf (Dosya Listesi), Sağ Taraf (Yeni Dosya Ekleme Formu)
col_left, col_right = st.columns([8, 4])

# ==============================================================================
# SOL TARAF: DOSYA LİSTESİ VE DÜZENLEME
# ==============================================================================
with col_left:
    st.subheader(f"📋 Dosya Listesi ({len(gosterilecek_dosyalar)} Dosya)")
    
    if kayitlar:
        if gosterilecek_dosyalar:
            for d_idx, dosya in enumerate(gosterilecek_dosyalar):
                d_no = dosya.get("Dosya No", "")
                firma = dosya.get("Firma", "")
                ana_aciklama = dosya.get("Aciklama", "")
                islemler = dosya.get("Islemler", [])
                
                # Durumlar
                bagli_durumu = dosya.get("BagliDosya", False)
                kapatma_red_durumu = dosya.get("KapatmaRed", False)
                tescilde_durumu = dosya.get("TescildeBekleyen", False)
                kapatma_asamasinda_durumu = dosya.get("KapatmaAsamasinda", False)
                yazi_cevabi_durumu = dosya.get("YaziCevabiBekleyen", False)
                incelenmedi_durumu = dosya.get("Incelenmedi", False)
                incelemede_durumu = dosya.get("Incelemede", False)
                mail_atildi_durumu = dosya.get("MailAtildi", False)
                mail_tarihi = dosya.get("MailTarihi", "")

                # İkon Rozetleri
                simgeler = ""
                if bagli_durumu: simgeler += "🔗 "
                if kapatma_red_durumu: simgeler += "🚫 "
                if tescilde_durumu: simgeler += "⏳ "
                if kapatma_asamasinda_durumu: simgeler += "🏁 "
                if yazi_cevabi_durumu: simgeler += "✉️ "
                if incelenmedi_durumu: simgeler += "🔍 "
                if incelemede_durumu: simgeler += "🧐 "
                if mail_atildi_durumu: simgeler += "📧 "

                mail_baslik_eki = f" (📧 {mail_tarihi})" if (mail_atildi_durumu and mail_tarihi) else ""

                # Kart Mantığı
                with st.container():
                    col_del, col_exp = st.columns([1, 11])
                    
                    with col_del:
                        confirm_del_key = f"confirm_del_{d_no}_{d_idx}"
                        if confirm_del_key not in st.session_state:
                            st.session_state[confirm_del_key] = False
                        
                        if not st.session_state[confirm_del_key]:
                            if st.button("🗑️", key=f"btn_del_init_{d_no}_{d_idx}", help="Dosyayı Sil"):
                                st.session_state[confirm_del_key] = True
                                st.rerun()
                        else:
                            c_s_evet, c_s_iptal = st.columns(2)
                            with c_s_evet:
                                if st.button("✔️", key=f"confirm_del_yes_{d_no}_{d_idx}", help="Silmeyi Onayla"):
                                    kayitlar = [d for d in kayitlar if d.get("Dosya No") != d_no]
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} silindi")
                                    st.session_state[confirm_del_key] = False
                                    st.toast(f"🗑️ {d_no} silindi.")
                                    st.rerun()
                            with c_s_iptal:
                                if st.button("❌", key=f"cancel_del_{d_no}_{d_idx}", help="İptal"):
                                    st.session_state[confirm_del_key] = False
                                    st.rerun()

                    with col_exp:
                        exp_header = f"📂 **Dosya No:** {d_no}\n\n🏢 **Firma:** {firma} {simgeler}({len(islemler)} İşlem){mail_baslik_eki}"
                        exp_container = st.expander(exp_header, expanded=False)

                        with exp_container:
                            # 1. BÖLÜM: DOSYA DURUMU
                            st.write("##### 1. Dosya Durumu")
                            st.markdown(f"**Açıklama:** {ana_aciklama if ana_aciklama else '_Açıklama yok._'}")

                            st.markdown("---")

                            # 2. BÖLÜM: DOSYA DURUM DETAYI
                            st.write("##### 2. Dosya Durum Detayı")

                            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
                            with c_st1:
                                c_bagli = st.checkbox("🔗 Bağlı Dosya", value=bagli_durumu, key=f"chk_bagli_{d_no}_{d_idx}")
                                c_red = st.checkbox("🚫 Kapatma Red", value=kapatma_red_durumu, key=f"chk_red_{d_no}_{d_idx}")
                            with c_st2:
                                c_tescilde = st.checkbox("⏳ Tescilde Bekleyen", value=tescilde_durumu, key=f"chk_tescilde_{d_no}_{d_idx}")
                                c_kapatma = st.checkbox("🏁 Kapatma Aşamasında", value=kapatma_asamasinda_durumu, key=f"chk_kapatma_{d_no}_{d_idx}")
                            with c_st3:
                                c_yazi = st.checkbox("✉️ Yazı Cevabı Bekleyen", value=yazi_cevabi_durumu, key=f"chk_yazi_{d_no}_{d_idx}")
                                c_incelenmedi = st.checkbox("🔍 İncelenmedi", value=incelenmedi_durumu, key=f"chk_incelenmedi_{d_no}_{d_idx}")
                            with c_st4:
                                c_incelemede = st.checkbox("🧐 İncelemede", value=incelemede_durumu, key=f"chk_incelemede_{d_no}_{d_idx}")
                                c_mail = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"chk_mail_{d_no}_{d_idx}")

                            # Durumu Kaydet Butonu
                            st.markdown("<div class='save-status-container'>", unsafe_allow_html=True)
                            if st.button("💾 Durumları Kaydet", key=f"btn_save_status_{d_no}_{d_idx}"):
                                dosya["BagliDosya"] = c_bagli
                                dosya["KapatmaRed"] = c_red
                                dosya["TescildeBekleyen"] = c_tescilde
                                dosya["KapatmaAsamasinda"] = c_kapatma
                                dosya["YaziCevabiBekleyen"] = c_yazi
                                dosya["Incelenmedi"] = c_incelenmedi
                                dosya["Incelemede"] = c_incelemede
                                dosya["MailAtildi"] = c_mail
                                
                                if c_mail and not mail_atildi_durumu:
                                    dosya["MailTarihi"] = simdi_dt.strftime("%d.%m.%Y")
                                elif not c_mail:
                                    dosya["MailTarihi"] = ""

                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} durumları güncellendi")
                                st.toast("✅ Durumlar güncellendi!")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                            st.markdown("---")
                            
                            # 3. BÖLÜM: DOSYADA BUGÜNE KADAR YAPILAN İŞLEMLER
                            st.write("##### 3. Dosyada Bugüne Kadar Yapılan İşlemler")
                            
                            # Geçmiş İşlemler Listesi
                            if islemler:
                                for isl in reversed(islemler):
                                    st.caption(f"🗓️ **{isl.get('Tarih', '')}** — {isl.get('Not', '')}")
                            else:
                                st.caption("*Henüz kaydedilmiş bir işlem yok.*")

                            # Yeni İşlem Ekle Formu (3. Bölümün İçinde)
                            st.markdown("###### ➕ Yeni İşlem Ekle")
                            with st.form(key=f"form_islem_ekle_{d_no}_{d_idx}", clear_on_submit=True):
                                yeni_islem_notu = st.text_input("İşlem Notu", placeholder=f"{d_no} nolu dosyaya yapılan işlemi giriniz...", label_visibility="collapsed")
                                submit_islem = st.form_submit_button("💾 İşlemi Kaydet")
                                if submit_islem:
                                    if yeni_islem_notu.strip():
                                        yeni_islem = {
                                            "Tarih": simdi_dt.strftime("%d.%m.%Y %H:%M"),
                                            "Not": yeni_islem_notu.strip()
                                        }
                                        dosya.setdefault("Islemler", []).append(yeni_islem)
                                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyasına yeni işlem eklendi")
                                        st.toast("✅ İşlem kaydedildi!")
                                        st.rerun()
                                    else:
                                        st.warning("İşlem notu boş olamaz.")
        else:
            st.info("Arama kriterlerine uygun dosya bulunamadı.")
    else:
        st.info("Henüz kayıtlı dosya yok.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA EKLEME FORMU
# ==============================================================================
with col_right:
    st.subheader("➕ Yeni Dosya Ekle")
    with st.form(key="form_yeni_dosya", clear_on_submit=True):
        yeni_dno = st.text_input("Dosya No *", placeholder="Örn: 2025 D1 5400")
        yeni_firma = st.text_input("Firma Adı *", placeholder="Firma unvanı...")
        yeni_aciklama = st.text_area("Açıklama", placeholder="Dosya hakkında ek notlar...")
        
        submit_dosya = st.form_submit_button("📂 Dosyayı Kaydet", use_container_width=True)
        
        if submit_dosya:
            if yeni_dno.strip() and yeni_firma.strip():
                # Mükerrer Kontrolü
                zaten_var = any(d.get("Dosya No", "").strip().lower() == yeni_dno.strip().lower() for d in kayitlar)
                if zaten_var:
                    st.error("Bu dosya numarası zaten kayıtlı!")
                else:
                    yeni_kayit = {
                        "Dosya No": yeni_dno.strip(),
                        "Firma": yeni_firma.strip(),
                        "Aciklama": yeni_aciklama.strip(),
                        "OlusturmaTarihi": simdi_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "Islemler": [],
                        "BagliDosya": False,
                        "KapatmaRed": False,
                        "TescildeBekleyen": False,
                        "KapatmaAsamasinda": False,
                        "YaziCevabiBekleyen": False,
                        "Incelenmedi": False,
                        "Incelemede": False,
                        "MailAtildi": False,
                        "MailTarihi": "",
                        "SiraNo": len(kayitlar) + 1,
                        "IncelenmediSiraNo": 9999,
                        "IncelemedeSiraNo": 9999
                    }
                    kayitlar.append(yeni_kayit)
                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Yeni dosya eklendi: {yeni_dno}")
                    st.success(f"✅ '{yeni_dno}' başarıyla eklendi!")
                    st.rerun()
            else:
                st.warning("Lütfen Dosya No ve Firma alanlarını doldurunuz.")
