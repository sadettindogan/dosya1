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

# Kesin CSS Düzeltmeleri
st.markdown("""
<style>
    div[data-testid="stExpander"] div[role="region"] {
        padding-top: 0.1rem !important;
        padding-bottom: 0.2rem !important;
    }
    .element-container {
        margin-bottom: -0.4rem !important;
    }
    hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    div[data-testid="stAlert"] {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        margin-bottom: 0.2rem !important;
        min-height: auto !important;
    }

    /* Dijital Saat Stili */
    .digital-clock {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85rem;
        font-weight: bold;
        color: #008080;
        background-color: #f0f4f8;
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 2px;
        border: 1px solid #cbd5e1;
    }

    /* Zamanı Gelen Hatırlatma - Sabit Kırmızı Kutu Stili */
    .red-reminder-box {
        background-color: #fee2e2;
        border: 1.5px solid #ef4444;
        color: #991b1b;
        padding: 6px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }

    /* Ana Başlık Altındaki Kırmızı Uyarı Yazısı */
    .header-red-alert {
        background-color: #dc2626;
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 6px;
        display: inline-block;
        margin-top: 5px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(220, 38, 38, 0.3);
    }

    /* SADECE YÖN KAYDIRMA BUTONLARI İÇİN MİNİMAL MAVİ STİL */
    button[help*="Taş"], button[help*="Kaydır"] {
        opacity: 0.2 !important;
        color: #2563eb !important;
        border: none !important;
        background: transparent !important;
        padding: 0px !important;
        font-size: 0.75rem !important;
        width: 22px !important;
        height: 22px !important;
        min-width: 22px !important;
        min-height: 22px !important;
        border-radius: 50% !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out !important;
    }
    button[help*="Taş"]:hover, button[help*="Kaydır"]:hover {
        opacity: 1.0 !important;
        color: #1d4ed8 !important;
        background-color: #eff6ff !important;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.25) !important;
        transform: scale(1.15) !important;
    }

    /* DURUMU KAYDET BUTONU - DÜZGÜN BİÇİMLENDİRME */
    .save-status-container button {
        width: auto !important;
        min-width: 140px !important;
        height: 32px !important;
        padding: 2px 16px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        background-color: #2563eb !important;
        border: 1px solid #1d4ed8 !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
        white-space: nowrap !important;
        opacity: 1.0 !important;
        transform: none !important;
    }
    .save-status-container button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        box-shadow: 0 3px 6px rgba(29, 78, 216, 0.3) !important;
        transform: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GITHUB BAĞLANTISI VE VERİ OKUMA ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = st.secrets["FILE_PATH"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

VARSAYILAN_BOLUM_SIRASI = ["kapatma", "incelenmedi", "incelemede", "notlar", "hatirlatma"]

def verileri_getir():
    try:
        file_content = repo.get_contents(FILE_PATH)
        raw_data = json.loads(file_content.decoded_content.decode('utf-8'))
        
        if isinstance(raw_data, dict):
            kayitlar_data = raw_data.get("Dosyalar", [])
            onemli_notlar_raw = raw_data.get("OnemliNotlar", [])
            hatirlatmalar_raw = raw_data.get("Hatirlatmalar", [])
            bolum_sirasi_data = raw_data.get("BolumSirasi", VARSAYILAN_BOLUM_SIRASI)
        else:
            kayitlar_data = raw_data if isinstance(raw_data, list) else []
            onemli_notlar_raw = []
            hatirlatmalar_raw = []
            bolum_sirasi_data = VARSAYILAN_BOLUM_SIRASI

        if isinstance(onemli_notlar_raw, str):
            onemli_notlar_data = [onemli_notlar_raw.strip()] if onemli_notlar_raw.strip() else []
        elif isinstance(onemli_notlar_raw, list):
            onemli_notlar_data = onemli_notlar_raw
        else:
            onemli_notlar_data = []

        hatirlatmalar_data = hatirlatmalar_raw if isinstance(hatirlatmalar_raw, list) else []

        for b in VARSAYILAN_BOLUM_SIRASI:
            if b not in bolum_sirasi_data:
                bolum_sirasi_data.append(b)

        yeni_format_data = []
        for item in kayitlar_data:
            if "Aciklama" not in item: item["Aciklama"] = ""
            if "Islemler" not in item: item["Islemler"] = []
            if "BagliDosya" not in item: item["BagliDosya"] = False
            if "KapatmaRed" not in item: item["KapatmaRed"] = False
            if "TescildeBekleyen" not in item: item["TescildeBekleyen"] = False
            if "KapatmaAsamasinda" not in item: item["KapatmaAsamasinda"] = False
            if "YaziCevabiBekleyen" not in item: item["YaziCevabiBekleyen"] = False
            if "Incelenmedi" not in item: item["Incelenmedi"] = False
            if "Incelemede" not in item: item["Incelemede"] = False
            if "MailAtildi" not in item: item["MailAtildi"] = False
            if "MailTarihi" not in item: item["MailTarihi"] = ""
            if "SiraNo" not in item: item["SiraNo"] = 9999
            if "IncelenmediSiraNo" not in item: item["IncelenmediSiraNo"] = 9999
            if "IncelemedeSiraNo" not in item: item["IncelemedeSiraNo"] = 9999
            # Ön İnceleme Veri Yapısı
            if "OnInceleme" not in item or not isinstance(item["OnInceleme"], dict):
                item["OnInceleme"] = {
                    "Ekspertiz": False, "EkspertizKontrol": False,
                    "OzelSart233": False, "OzelSart233Kontrol": False,
                    "YMM": False, "YMMKontrol": False,
                    "IIGU": False, "IIGUKontrol": False
                }
            yeni_format_data.append(item)
            
        return yeni_format_data, onemli_notlar_data, hatirlatmalar_data, bolum_sirasi_data
    except Exception:
        return [], [], [], VARSAYILAN_BOLUM_SIRASI

def verileri_kaydet(yeni_kayitlar, onemli_notlar, hatirlatmalar, bolum_sirasi, mesaj):
    kaydedilecek_veri = {
        "Dosyalar": yeni_kayitlar,
        "OnemliNotlar": onemli_notlar,
        "Hatirlatmalar": hatirlatmalar,
        "BolumSirasi": bolum_sirasi
    }
    yeni_json_icerik = json.dumps(kaydedilecek_veri, ensure_ascii=False, indent=2)
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

kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi = verileri_getir()

# ZAMAN KONTROLÜ VE AKTİF HATIRLATMA TESPİTİ
turkey_tz = pytz.timezone("Europe/Istanbul")
simdi_dt = datetime.now(turkey_tz)

zamani_gelen_var = False
for h in mevcut_hatirlatmalar:
    h_zaman_str = h.get("Zaman", "")
    h_tamamlandi = h.get("Tamamlandi", False)
    if not h_tamamlandi and h_zaman_str:
        try:
            h_dt = turkey_tz.localize(datetime.strptime(h_zaman_str, "%Y-%m-%d %H:%M:%S"))
            if simdi_dt >= h_dt:
                zamani_gelen_var = True
                break
        except Exception:
            pass

# BAŞLIK
st.title("📁 Dosya Takibi")

# ZAMANI GELEN HATIRLATMA VARSA BAŞLIĞIN ALTINDA KIRMIZI UYARI
if zamani_gelen_var:
    st.markdown("<div class='header-red-alert'>🚨 HATIRLATMA VAR</div>", unsafe_allow_html=True)

st.markdown("---")

# TOPLAM VE DURUM SAYILARI GÖSTERGELERİ
toplam_dosya_sayisi = len(kayitlar)
bagli_dosya_sayisi = sum(1 for d in kayitlar if d.get("BagliDosya", False))
kapatma_red_sayisi = sum(1 for d in kayitlar if d.get("KapatmaRed", False))
tescilde_bekleyen_sayisi = sum(1 for d in kayitlar if d.get("TescildeBekleyen", False))
kapatma_asamasinda_sayisi = sum(1 for d in kayitlar if d.get("KapatmaAsamasinda", False))
yazi_cevabi_bekleyen_sayisi = sum(1 for d in kayitlar if d.get("YaziCevabiBekleyen", False))
incelenmedi_sayisi = sum(1 for d in kayitlar if d.get("Incelenmedi", False))
incelemede_sayisi = sum(1 for d in kayitlar if d.get("Incelemede", False))
mail_atildi_sayisi = sum(1 for d in kayitlar if d.get("MailAtildi", False))

col_m1, col_m2, col_m3, col_m4, col_m5, col_m6, col_m7, col_m8, col_m9 = st.columns(9)
with col_m1: st.metric(label="📊 Toplam", value=f"{toplam_dosya_sayisi}")
with col_m2: st.metric(label="🔗 Bağlı", value=f"{bagli_dosya_sayisi}")
with col_m3: st.metric(label="🚫 Red", value=f"{kapatma_red_sayisi}")
with col_m4: st.metric(label="⏳ Tescilde", value=f"{tescilde_bekleyen_sayisi}")
with col_m5: st.metric(label="🏁 Kapatmada", value=f"{kapatma_asamasinda_sayisi}")
with col_m6: st.metric(label="✉️ Yazı Cevabı", value=f"{yazi_cevabi_bekleyen_sayisi}")
with col_m7: st.metric(label="🔍 İncelenmedi", value=f"{incelenmedi_sayisi}")
with col_m8: st.metric(label="🧐 İncelemede", value=f"{incelemede_sayisi}")
with col_m9: st.metric(label="📧 Mail Atıldı", value=f"{mail_atildi_sayisi}")

st.markdown("---")

# ==============================================================================
# DİNAMİK BÖLÜM SIRALAMA MEKANİZMASI
# ==============================================================================
def bolum_sol_sag_kaydir(bolum_kodu, yon):
    idx = mevcut_bolum_sirasi.index(bolum_kodu)
    if yon == "sol" and idx > 0:
        mevcut_bolum_sirasi[idx], mevcut_bolum_sirasi[idx - 1] = mevcut_bolum_sirasi[idx - 1], mevcut_bolum_sirasi[idx]
    elif yon == "sag" and idx < len(mevcut_bolum_sirasi) - 1:
        mevcut_bolum_sirasi[idx], mevcut_bolum_sirasi[idx + 1] = mevcut_bolum_sirasi[idx + 1], mevcut_bolum_sirasi[idx]
    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{bolum_kodu} bölümü {yon}a kaydırıldı")
    st.rerun()

genislik_haritasi = {
    "kapatma": 1.1,
    "incelenmedi": 1.1,
    "incelemede": 1.1,
    "notlar": 0.9,
    "hatirlatma": 0.9
}
sutun_genislikleri = [genislik_haritasi[b] for b in mevcut_bolum_sirasi]
top_cols = st.columns(sutun_genislikleri)

for col_idx, bolum_kodu in enumerate(mevcut_bolum_sirasi):
    target_col = top_cols[col_idx]
    
    with target_col:
        c_head_txt, c_head_left, c_head_right = st.columns([78, 11, 11], vertical_alignment="center")
        
        with c_head_left:
            if col_idx > 0:
                if st.button("◀", key=f"btn_m_left_{bolum_kodu}", help="Bölümü Sola Kaydır"):
                    bolum_sol_sag_kaydir(bolum_kodu, "sol")
                    
        with c_head_right:
            if col_idx < len(mevcut_bolum_sirasi) - 1:
                if st.button("▶", key=f"btn_m_right_{bolum_kodu}", help="Bölümü Sağa Kaydır"):
                    bolum_sol_sag_kaydir(bolum_kodu, "sag")

        # 1. KAPATMA AŞAMASINDA
        if bolum_kodu == "kapatma":
            with c_head_txt:
                st.subheader("🏁 Kapatmada")
            
            kapatmada_dosyalar = [d for d in kayitlar if d.get("KapatmaAsamasinda", False)]
            kapatmada_dosyalar = sorted(kapatmada_dosyalar, key=lambda x: x.get("SiraNo", 9999))
            
            with st.container(height=280):
                if kapatmada_dosyalar:
                    for k_idx, k_dosya in enumerate(kapatmada_dosyalar):
                        k_dno = k_dosya.get("Dosya No", "")
                        k_firma = k_dosya.get("Firma", "-")
                        
                        c_k_txt, c_k_up, c_k_down = st.columns([78, 11, 11], vertical_alignment="center")
                        with c_k_txt:
                            st.markdown(f"**{k_idx + 1}.** `{k_dno}` | <small>{k_firma}</small>", unsafe_allow_html=True)
                        
                        with c_k_up:
                            if st.button("▲", key=f"btn_kp_up_{k_dno}_{k_idx}", help="Yukarı Taş"):
                                if k_idx > 0:
                                    ust_dosya = kapatmada_dosyalar[k_idx - 1]
                                    curr_sira = k_dosya.get("SiraNo", k_idx)
                                    ust_sira = ust_dosya.get("SiraNo", k_idx - 1)
                                    k_dosya["SiraNo"] = ust_sira if ust_sira != curr_sira else k_idx - 1
                                    ust_dosya["SiraNo"] = curr_sira if ust_sira != curr_sira else k_idx
                                else:
                                    k_dosya["SiraNo"] = -1
                                    
                                for idx, d in enumerate(sorted(kapatmada_dosyalar, key=lambda x: x.get("SiraNo", 9999))):
                                    d["SiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{k_dno} kapatma yukarı")
                                st.rerun()

                        with c_k_down:
                            if st.button("▼", key=f"btn_kp_dn_{k_dno}_{k_idx}", help="Aşağı Taş"):
                                if k_idx < len(kapatmada_dosyalar) - 1:
                                    alt_dosya = kapatmada_dosyalar[k_idx + 1]
                                    curr_sira = k_dosya.get("SiraNo", k_idx)
                                    alt_sira = alt_dosya.get("SiraNo", k_idx + 1)
                                    k_dosya["SiraNo"] = alt_sira if alt_sira != curr_sira else k_idx + 1
                                    alt_dosya["SiraNo"] = curr_sira if alt_sira != curr_sira else k_idx
                                    
                                for idx, d in enumerate(sorted(kapatmada_dosyalar, key=lambda x: x.get("SiraNo", 9999))):
                                    d["SiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{k_dno} kapatma aşağı")
                                st.rerun()
                else:
                    st.caption("*Kapatma aşamasında dosya yok.*")

        # 2. İNCELENMEDİ
        elif bolum_kodu == "incelenmedi":
            with c_head_txt:
                st.subheader("🔍 İncelenmedi")
            
            incelenmedi_dosyalar = [d for d in kayitlar if d.get("Incelenmedi", False)]
            incelenmedi_dosyalar = sorted(incelenmedi_dosyalar, key=lambda x: x.get("IncelenmediSiraNo", 9999))
            
            with st.container(height=280):
                if incelenmedi_dosyalar:
                    for i_idx, i_dosya in enumerate(incelenmedi_dosyalar):
                        i_dno = i_dosya.get("Dosya No", "")
                        i_firma = i_dosya.get("Firma", "-")
                        
                        c_i_txt, c_i_up, c_i_down = st.columns([78, 11, 11], vertical_alignment="center")
                        with c_i_txt:
                            st.markdown(f"**{i_idx + 1}.** `{i_dno}` | <small>{i_firma}</small>", unsafe_allow_html=True)
                        
                        with c_i_up:
                            if st.button("▲", key=f"btn_inc_up_{i_dno}_{i_idx}", help="Yukarı Taş"):
                                if i_idx > 0:
                                    ust_dosya = incelenmedi_dosyalar[i_idx - 1]
                                    curr_sira = i_dosya.get("IncelenmediSiraNo", i_idx)
                                    ust_sira = ust_dosya.get("IncelenmediSiraNo", i_idx - 1)
                                    i_dosya["IncelenmediSiraNo"] = ust_sira if ust_sira != curr_sira else i_idx - 1
                                    ust_dosya["IncelenmediSiraNo"] = curr_sira if ust_sira != curr_sira else i_idx
                                else:
                                    i_dosya["IncelenmediSiraNo"] = -1
                                    
                                for idx, d in enumerate(sorted(incelenmedi_dosyalar, key=lambda x: x.get("IncelenmediSiraNo", 9999))):
                                    d["IncelenmediSiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{i_dno} incelenmedi yukarı")
                                st.rerun()

                        with c_i_down:
                            if st.button("▼", key=f"btn_inc_dn_{i_dno}_{i_idx}", help="Aşağı Taş"):
                                if i_idx < len(incelenmedi_dosyalar) - 1:
                                    alt_dosya = incelenmedi_dosyalar[i_idx + 1]
                                    curr_sira = i_dosya.get("IncelenmediSiraNo", i_idx)
                                    alt_sira = alt_dosya.get("IncelenmediSiraNo", i_idx + 1)
                                    i_dosya["IncelenmediSiraNo"] = alt_sira if alt_sira != curr_sira else i_idx + 1
                                    alt_dosya["IncelenmediSiraNo"] = curr_sira if alt_sira != curr_sira else i_idx
                                    
                                for idx, d in enumerate(sorted(incelenmedi_dosyalar, key=lambda x: x.get("IncelenmediSiraNo", 9999))):
                                    d["IncelenmediSiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{i_dno} incelenmedi aşağı")
                                st.rerun()
                else:
                    st.caption("*İncelenmedi işaretli dosya yok.*")

        # 3. İNCELEMEDE
        elif bolum_kodu == "incelemede":
            with c_head_txt:
                st.subheader("🧐 İncelemede")
            
            incelemede_dosyalar = [d for d in kayitlar if d.get("Incelemede", False)]
            incelemede_dosyalar = sorted(incelemede_dosyalar, key=lambda x: x.get("IncelemedeSiraNo", 9999))
            
            with st.container(height=280):
                if incelemede_dosyalar:
                    for m_idx, m_dosya in enumerate(incelemede_dosyalar):
                        m_dno = m_dosya.get("Dosya No", "")
                        m_firma = m_dosya.get("Firma", "-")
                        
                        c_m_txt, c_m_up, c_m_down = st.columns([78, 11, 11], vertical_alignment="center")
                        with c_m_txt:
                            st.markdown(f"**{m_idx + 1}.** `{m_dno}` | <small>{m_firma}</small>", unsafe_allow_html=True)
                        
                        with c_m_up:
                            if st.button("▲", key=f"btn_incmd_up_{m_dno}_{m_idx}", help="Yukarı Taş"):
                                if m_idx > 0:
                                    ust_dosya = incelemede_dosyalar[m_idx - 1]
                                    curr_sira = m_dosya.get("IncelemedeSiraNo", m_idx)
                                    ust_sira = ust_dosya.get("IncelemedeSiraNo", m_idx - 1)
                                    m_dosya["IncelemedeSiraNo"] = ust_sira if ust_sira != curr_sira else m_idx - 1
                                    ust_dosya["IncelemedeSiraNo"] = curr_sira if ust_sira != curr_sira else m_idx
                                else:
                                    m_dosya["IncelemedeSiraNo"] = -1
                                    
                                for idx, d in enumerate(sorted(incelemede_dosyalar, key=lambda x: x.get("IncelemedeSiraNo", 9999))):
                                    d["IncelemedeSiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{m_dno} incelemede yukarı")
                                st.rerun()

                        with c_m_down:
                            if st.button("▼", key=f"btn_incmd_dn_{m_dno}_{m_idx}", help="Aşağı Taş"):
                                if m_idx < len(incelemede_dosyalar) - 1:
                                    alt_dosya = incelemede_dosyalar[m_idx + 1]
                                    curr_sira = m_dosya.get("IncelemedeSiraNo", m_idx)
                                    alt_sira = alt_dosya.get("IncelemedeSiraNo", m_idx + 1)
                                    m_dosya["IncelemedeSiraNo"] = alt_sira if alt_sira != curr_sira else m_idx + 1
                                    alt_dosya["IncelemedeSiraNo"] = curr_sira if alt_sira != curr_sira else m_idx
                                    
                                for idx, d in enumerate(sorted(incelemede_dosyalar, key=lambda x: x.get("IncelemedeSiraNo", 9999))):
                                    d["IncelemedeSiraNo"] = idx
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{m_dno} incelemede aşağı")
                                st.rerun()
                else:
                    st.caption("*İncelemede işaretli dosya yok.*")

        # 4. ÖNEMLİ NOTLAR
        elif bolum_kodu == "notlar":
            with c_head_txt:
                st.subheader("📌 Önemli Notlar")
            
            with st.form(key="form_yeni_not_ekle", clear_on_submit=True):
                yeni_not_metni = st.text_input("Yeni Not", placeholder="Not yazınız...", label_visibility="collapsed")
                submit_not = st.form_submit_button("➕ Ekle", use_container_width=True)
                    
                if submit_not:
                    if yeni_not_metni.strip() != "":
                        mevcut_onemli_notlar.append(yeni_not_metni.strip())
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Yeni önemli not eklendi")
                        st.toast("✅ Not eklendi!")
                        st.rerun()
                    else:
                        st.warning("Not boş olamaz.")

            with st.container(height=200):
                if mevcut_onemli_notlar:
                    for n_idx, not_item in enumerate(mevcut_onemli_notlar):
                        c_not_text, c_not_del = st.columns([82, 18], vertical_alignment="center")
                        with c_not_text:
                            st.info(f"📌 {not_item}")
                        with c_not_del:
                            if st.button("🗑️", key=f"btn_del_not_{n_idx}", help="Bu notu sil"):
                                mevcut_onemli_notlar.pop(n_idx)
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Önemli not silindi")
                                st.toast("Not silindi!")
                                st.rerun()
                else:
                    st.caption("*Henüz kayıtlı not yok.*")

        # 5. HATIRLATMALAR
        elif bolum_kodu == "hatirlatma":
            saat_str = simdi_dt.strftime("%d.%m.%Y | %H:%M:%S")
            st.markdown(f"<div class='digital-clock'>🕒 {saat_str}</div>", unsafe_allow_html=True)
            with c_head_txt:
                st.subheader("⏰ Hatırlatmalar")

            with st.form(key="form_yeni_hatirlatma_ekle", clear_on_submit=True):
                h_metin = st.text_input("Hatırlatma Metni", placeholder="Hatırlatma...", label_visibility="collapsed")
                col_hd, col_ht = st.columns(2)
                with col_hd:
                    h_tarih = st.date_input("Tarih", value=simdi_dt.date())
                with col_ht:
                    h_saat = st.time_input("Saat", value=simdi_dt.time())
                    
                submit_hatirlatma = st.form_submit_button("➕ Ekle", use_container_width=True)

                if submit_hatirlatma:
                    if h_metin.strip() != "":
                        hedef_zaman_str = datetime.combine(h_tarih, h_saat).strftime("%Y-%m-%d %H:%M:%S")
                        mevcut_hatirlatmalar.append({
                            "Metin": h_metin.strip(),
                            "Zaman": hedef_zaman_str,
                            "Tamamlandi": False
                        })
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Yeni hatırlatma eklendi")
                        st.toast("✅ Hatırlatma eklendi!")
                        st.rerun()
                    else:
                        st.warning("Hatırlatma metni boş olamaz.")

            with st.container(height=180):
                if mevcut_hatirlatmalar:
                    for h_idx, h_item in enumerate(mevcut_hatirlatmalar):
                        h_metin_val = h_item.get("Metin", "")
                        h_zaman_str = h_item.get("Zaman", "")
                        h_tamamlandi = h_item.get("Tamamlandi", False)

                        zaman_geldi = False
                        try:
                            h_zaman_dt = turkey_tz.localize(datetime.strptime(h_zaman_str, "%Y-%m-%d %H:%M:%S"))
                            zaman_geldi = (simdi_dt >= h_zaman_dt) and not h_tamamlandi
                        except Exception:
                            pass

                        c_ht_txt, c_ht_chk, c_ht_del = st.columns([70, 15, 15], vertical_alignment="center")

                        with c_ht_txt:
                            formatted_zaman = h_zaman_str
                            try:
                                formatted_zaman = datetime.strptime(h_zaman_str, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
                            except Exception:
                                pass

                            if zaman_geldi:
                                st.markdown(f"<div class='red-reminder-box'>🔔 {h_metin_val}<br><small>📅 {formatted_zaman}</small></div>", unsafe_allow_html=True)
                            elif h_tamamlandi:
                                st.markdown(f"~~{h_metin_val}~~ <small>({formatted_zaman})</small>")
                            else:
                                st.markdown(f"⏰ **{h_metin_val}**<br><small>📅 {formatted_zaman}</small>", unsafe_allow_html=True)

                        with c_ht_chk:
                            st_chk = st.checkbox("", value=h_tamamlandi, key=f"chk_hatir_{h_idx}")
                            if st_chk != h_tamamlandi:
                                h_item["Tamamlandi"] = st_chk
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma durumu güncellendi")
                                st.rerun()

                        with c_ht_del:
                            if st.button("🗑️", key=f"btn_del_hatir_{h_idx}"):
                                mevcut_hatirlatmalar.pop(h_idx)
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma silindi")
                                st.rerun()
                else:
                    st.caption("*Kayıtlı hatırlatma yok.*")

st.markdown("---")

# ==============================================================================
# DOSYA DETAY / İŞLEMLER BÖLÜMÜ (GERİ GETİRİLEN ESKİ KISIM)
# ==============================================================================
st.subheader("📋 Dosya Arama ve Detaylar")

dosya_listesi = [f"{d.get('Dosya No', '')} - {d.get('Firma', '')}" for d in kayitlar]
secilen_dosya_str = st.selectbox("Dosya Seçiniz / Arayınız", options=[""] + dosya_listesi, index=0)

if secilen_dosya_str:
    secilen_dosya_no = secilen_dosya_str.split(" - ")[0].strip()
    secilen_dosya = next((d for d in kayitlar if d.get("Dosya No") == secilen_dosya_no), None)

    if secilen_dosya:
        st.markdown(f"### 📂 Dosya No: `{secilen_dosya.get('Dosya No')}`")
        
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.write(f"**Firma:** {secilen_dosya.get('Firma', '-')}")
            st.write(f"**Açıklama:** {secilen_dosya.get('Aciklama', '-')}")
        with c_info2:
            st.write(f"**Mail Tarihi:** {secilen_dosya.get('MailTarihi', '-')}")

        st.markdown("---")
        
        # --- BUGÜNE KADAR YAPILAN İŞLEMLER KISMI ---
        st.markdown("#### 🕒 Bugüne Kadar Yapılan İşlemler")
        
        islemler_listesi = secilen_dosya.get("Islemler", [])
        
        # Yeni İşlem Ekleme Formu
        with st.form(key=f"form_yeni_islem_{secilen_dosya_no}", clear_on_submit=True):
            yeni_islem_metni = st.text_area("Yeni İşlem / Not Ekle", placeholder="Yapılan işlemi yazınız...")
            col_islem_btn, _ = st.columns([1, 4])
            with col_islem_btn:
                submit_islem = st.form_submit_button("➕ İşlemi Kaydet", use_container_width=True)

            if submit_islem:
                if yeni_islem_metni.strip():
                    islem_zamani = simdi_dt.strftime("%d.%m.%Y %H:%M")
                    yeni_islem_obj = {
                        "Tarih": islem_zamani,
                        "Aciklama": yeni_islem_metni.strip()
                    }
                    if "Islemler" not in secilen_dosya:
                        secilen_dosya["Islemler"] = []
                    secilen_dosya["Islemler"].insert(0, yeni_islem_obj) # En yeni işlemi üste ekle
                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{secilen_dosya_no} dosyasına işlem eklendi")
                    st.toast("✅ İşlem başarıyla eklendi!")
                    st.rerun()
                else:
                    st.warning("Lütfen işlem açıklaması giriniz.")

        # Eklenmiş İşlemlerin Listelenmesi
        if islemler_listesi:
            for idx, islem in enumerate(islemler_listesi):
                i_tarih = islem.get("Tarih", "-")
                i_aciklama = islem.get("Aciklama", "")
                
                c_islem_txt, c_islem_del = st.columns([90, 10], vertical_alignment="center")
                with c_islem_txt:
                    st.info(f"**[{i_tarih}]** {i_aciklama}")
                with c_islem_del:
                    if st.button("🗑️", key=f"btn_del_islem_{secilen_dosya_no}_{idx}", help="Bu işlemi sil"):
                        secilen_dosya["Islemler"].pop(idx)
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{secilen_dosya_no} dosyasından işlem silindi")
                        st.toast("İşlem silindi!")
                        st.rerun()
        else:
            st.caption("*Bu dosya için henüz yapılmış bir işlem kaydı yok.*")
