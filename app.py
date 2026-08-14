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

                        try:
                            h_zaman_dt = turkey_tz.localize(datetime.strptime(h_zaman_str, "%Y-%m-%d %H:%M:%S"))
                            zaman_geldi = (simdi_dt >= h_zaman_dt) and not h_tamamlandi
                        except Exception:
                            zaman_geldi = False

                        c_h_text, c_h_action = st.columns([72, 28], vertical_alignment="center")

                        with c_h_text:
                            if zaman_geldi:
                                st.markdown(f"<div class='red-reminder-box'>🔔 {h_metin_val}<br><small>🗓️ {h_zaman_str[11:16]}</small></div>", unsafe_allow_html=True)
                            else:
                                gosterim_tarih = h_zaman_str[8:10] + "." + h_zaman_str[5:7] + " " + h_zaman_str[11:16]
                                if h_tamamlandi:
                                    st.caption(f"✅ ~~{h_metin_val}~~")
                                else:
                                    st.warning(f"⏰ {h_metin_val} ({gosterim_tarih})")

                        with c_h_action:
                            if zaman_geldi:
                                if st.button("Tamam", key=f"btn_ok_h_{h_idx}", type="primary", help="Kapat"):
                                    h_item["Tamamlandi"] = True
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma tamamlandı")
                                    st.rerun()
                            else:
                                if st.button("🗑️", key=f"del_h_{h_idx}", help="Sil"):
                                    mevcut_hatirlatmalar.pop(h_idx)
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma silindi")
                                    st.rerun()
                else:
                    st.caption("*Henüz kayıtlı hatırlatma yok.*")

st.markdown("---")

# EKRAN YAPILANDIRMASI: Sol Taraf %65, Sağ Taraf %35
col_left, col_right = st.columns([65, 35], gap="large")

# ==============================================================================
# SOL TARAF: GENİŞ DOSYA LİSTESİ VE GEÇMİŞ İŞLEMLER
# ==============================================================================
with col_left:
    st.subheader("📋 Kayıtlı Dosyalar ve Dosyada Bugüne Kadar Yapılan İşlemler")
    
    search_col, _ = st.columns([1, 2])
    with search_col:
        arama = st.text_input("🔍 Dosya No veya Firma ile Ara", "", placeholder="Örn: 2025 D1 5400 veya Firma Adı")

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
                ana_aciklama = dosya.get("Aciklama", "")
                islemler = dosya.get("Islemler", [])
                bagli_durumu = dosya.get("BagliDosya", False)
                kapatma_red_durumu = dosya.get("KapatmaRed", False)
                tescilde_durumu = dosya.get("TescildeBekleyen", False)
                kapatma_asamasinda_durumu = dosya.get("KapatmaAsamasinda", False)
                yazi_cevabi_durumu = dosya.get("YaziCevabiBekleyen", False)
                incelenmedi_durumu = dosya.get("Incelenmedi", False)
                incelemede_durumu = dosya.get("Incelemede", False)
                mail_atildi_durumu = dosya.get("MailAtildi", False)
                mail_tarihi_val = dosya.get("MailTarihi", "")
                
                # Ön İnceleme Sözlüğü
                on_inc = dosya.get("OnInceleme", {
                    "Ekspertiz": False, "EkspertizKontrol": False,
                    "OzelSart233": False, "OzelSart233Kontrol": False,
                    "YMM": False, "YMMKontrol": False,
                    "IIGU": False, "IIGUKontrol": False
                })
                
                edit_key = f"edit_aciklama_{d_no}_{d_idx}"
                confirm_del_key = f"confirm_del_single_{d_no}_{d_idx}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                if confirm_del_key not in st.session_state:
                    st.session_state[confirm_del_key] = False

                simgeler = ""
                if bagli_durumu: simgeler += "🔗 "
                if kapatma_red_durumu: simgeler += "🚫 "
                if tescilde_durumu: simgeler += "⏳ "
                if kapatma_asamasinda_durumu: simgeler += "🏁 "
                if yazi_cevabi_durumu: simgeler += "✉️ "
                if incelenmedi_durumu: simgeler += "🔍 "
                if incelemede_durumu: simgeler += "🧐 "

                mail_baslik_eki = ""
                if mail_atildi_durumu:
                    if mail_tarihi_val:
                        mail_baslik_eki = f" 📧 ({mail_tarihi_val} mail atıldı)"
                    else:
                        mail_baslik_eki = " 📧 (mail atıldı)"

                col_exp, _space, col_dosya_sil = st.columns([60, 33, 7], vertical_alignment="center")
                
                with col_exp:
                    exp_header = f"📂 **Dosya No:** {d_no}\n\n🏢 **Firma:** {firma} {simgeler}({len(islemler)} İşlem){mail_baslik_eki}"
                    exp_container = st.expander(exp_header, expanded=False)
                
                with col_dosya_sil:
                    if not st.session_state[confirm_del_key]:
                        if st.button("🗑️", key=f"del_dosya_btn_{d_no}_{d_idx}", help="Dosyayı Sil"):
                            st.session_state[confirm_del_key] = True
                            st.rerun()
                    else:
                        st.caption("Emin misiniz?")
                        c_s_evet, c_s_iptal = st.columns(2)
                        with c_s_evet:
                            if st.button("✅", key=f"yes_del_{d_no}_{d_idx}", help="Evet, sil"):
                                kayitlar.remove(dosya)
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} nolu dosya silindi")
                                st.session_state[confirm_del_key] = False
                                st.success(f"'{d_no}' silindi!")
                                st.rerun()
                        with c_s_iptal:
                            if st.button("❌", key=f"no_del_{d_no}_{d_idx}", help="İptal"):
                                st.session_state[confirm_del_key] = False
                                st.rerun()

                with exp_container:
                    # DURUM DÜZENLEME SEÇENEKLERİ
                    st.markdown("##### 📌 Dosya Durumu Düzenle")
                    col_cb1, col_cb2, col_cb3, col_cb4 = st.columns(4)
                    with col_cb1:
                        ch_bagli = st.checkbox("🔗 Bağlı", value=bagli_durumu, key=f"cb_bagli_{d_no}_{d_idx}")
                        ch_red = st.checkbox("🚫 Red", value=kapatma_red_durumu, key=f"cb_red_{d_no}_{d_idx}")
                    with col_cb2:
                        ch_tescilde = st.checkbox("⏳ Tescilde Bekleyen", value=tescilde_durumu, key=f"cb_tescilde_{d_no}_{d_idx}")
                        ch_kapatma = st.checkbox("🏁 Kapatma Aşamasında", value=kapatma_asamasinda_durumu, key=f"cb_kapatma_{d_no}_{d_idx}")
                    with col_cb3:
                        ch_yazi = st.checkbox("✉️ Yazı Cevabı Bekleyen", value=yazi_cevabi_durumu, key=f"cb_yazi_{d_no}_{d_idx}")
                        ch_incelenmedi = st.checkbox("🔍 İncelenmedi", value=incelenmedi_durumu, key=f"cb_incelenmedi_{d_no}_{d_idx}")
                    with col_cb4:
                        ch_incelemede = st.checkbox("🧐 İncelemede", value=incelemede_durumu, key=f"cb_incelemede_{d_no}_{d_idx}")
                        ch_mail = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"cb_mail_{d_no}_{d_idx}")

                    mail_tarih_giris = mail_tarihi_val
                    if ch_mail:
                        mail_tarih_giris = st.text_input("Mail Tarihi", value=mail_tarihi_val, placeholder="Örn: 12.08.2025", key=f"txt_mail_tarihi_{d_no}_{d_idx}")

                    st.markdown("---")

                    # İŞLEM EKLEME VEYA DÜZENLEME FORMU
                    st.markdown("##### 📝 Dosyada Bugüne Kadar Yapılan İşlemler")
                    
                    if not st.session_state[edit_key]:
                        if ana_aciklama:
                            st.info(f"**Açıklama:** {ana_aciklama}")
                        if st.button("✏️ Açıklamayı / İşlemleri Düzenle", key=f"btn_edit_aciklama_{d_no}_{d_idx}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    else:
                        with st.form(key=f"form_edit_aciklama_{d_no}_{d_idx}"):
                            yeni_aciklama_input = st.text_area("İşlem / Açıklama Metni", value=ana_aciklama)
                            col_f1, col_f2 = st.columns(2)
                            with col_f1:
                                submit_aciklama = st.form_submit_button("💾 Kaydet")
                            with col_f2:
                                cancel_aciklama = st.form_submit_button("❌ İptal")

                            if submit_aciklama:
                                bugun_str = simdi_dt.strftime("%d.%m.%Y %H:%M")
                                dosya["Aciklama"] = yeni_aciklama_input
                                dosya["Islemler"].append({"Tarih": bugun_str, "Islem": yeni_aciklama_input})
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} işlem eklendi")
                                st.session_state[edit_key] = False
                                st.toast("✅ İşlem kaydedildi!")
                                st.rerun()
                            elif cancel_aciklama:
                                st.session_state[edit_key] = False
                                st.rerun()

                    st.markdown("---")

                    # ==========================================================
                    # ÖN İNCELEME BÖLÜMÜ (YENİ EKLENEN KISIM)
                    # ==========================================================
                    st.markdown("##### 🔎 Ön İnceleme Konuları")
                    
                    # 1. Ekspertiz Şartı
                    c_oi1_l, c_oi1_r = st.columns([50, 50], vertical_alignment="center")
                    with c_oi1_l:
                        chk_eks = st.checkbox("1. Ekspertiz Şartı", value=on_inc.get("Ekspertiz", False), key=f"chk_eks_{d_no}_{d_idx}")
                    with c_oi1_r:
                        if chk_eks:
                            chk_eks_ctrl = st.checkbox("Kontrol Edildi", value=on_inc.get("EkspertizKontrol", False), key=f"chk_eks_ctrl_{d_no}_{d_idx}")
                        else:
                            chk_eks_ctrl = False

                    # 2. 233 NOlu Özel Şart
                    c_oi2_l, c_oi2_r = st.columns([50, 50], vertical_alignment="center")
                    with c_oi2_l:
                        chk_233 = st.checkbox("2. 233 Nolu Özel Şart", value=on_inc.get("OzelSart233", False), key=f"chk_233_{d_no}_{d_idx}")
                    with c_oi2_r:
                        if chk_233:
                            chk_233_ctrl = st.checkbox("Kontrol Edildi", value=on_inc.get("OzelSart233Kontrol", False), key=f"chk_233_ctrl_{d_no}_{d_idx}")
                        else:
                            chk_233_ctrl = False

                    # 3. YMM
                    c_oi3_l, c_oi3_r = st.columns([50, 50], vertical_alignment="center")
                    with c_oi3_l:
                        chk_ymm = st.checkbox("3. YMM", value=on_inc.get("YMM", False), key=f"chk_ymm_{d_no}_{d_idx}")
                    with c_oi3_r:
                        if chk_ymm:
                            chk_ymm_ctrl = st.checkbox("Kontrol Edildi", value=on_inc.get("YMMKontrol", False), key=f"chk_ymm_ctrl_{d_no}_{d_idx}")
                        else:
                            chk_ymm_ctrl = False

                    # 4. İİGÜ
                    c_oi4_l, c_oi4_r = st.columns([50, 50], vertical_alignment="center")
                    with c_oi4_l:
                        chk_iigu = st.checkbox("4. İİGÜ", value=on_inc.get("IIGU", False), key=f"chk_iigu_{d_no}_{d_idx}")
                    with c_oi4_r:
                        if chk_iigu:
                            chk_iigu_ctrl = st.checkbox("Kontrol Edildi", value=on_inc.get("IIGUKontrol", False), key=f"chk_iigu_ctrl_{d_no}_{d_idx}")
                        else:
                            chk_iigu_ctrl = False

                    st.markdown("<div class='save-status-container' style='margin-top: 10px;'>", unsafe_allow_html=True)
                    if st.button("💾 Tüm Durumu / Ön İncelemeyi Kaydet", key=f"btn_save_status_{d_no}_{d_idx}"):
                        # Durum Güncellemeleri
                        dosya["BagliDosya"] = ch_bagli
                        dosya["KapatmaRed"] = ch_red
                        dosya["TescildeBekleyen"] = ch_tescilde
                        dosya["KapatmaAsamasinda"] = ch_kapatma
                        dosya["YaziCevabiBekleyen"] = ch_yazi
                        dosya["Incelenmedi"] = ch_incelenmedi
                        dosya["Incelemede"] = ch_incelemede
                        dosya["MailAtildi"] = ch_mail
                        dosya["MailTarihi"] = mail_tarih_giris if ch_mail else ""
                        
                        # Ön İnceleme Güncellemeleri
                        dosya["OnInceleme"] = {
                            "Ekspertiz": chk_eks,
                            "EkspertizKontrol": chk_eks_ctrl,
                            "OzelSart233": chk_233,
                            "OzelSart233Kontrol": chk_233_ctrl,
                            "YMM": chk_ymm,
                            "YMMKontrol": chk_ymm_ctrl,
                            "IIGU": chk_iigu,
                            "IIGUKontrol": chk_iigu_ctrl
                        }
                        
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} durumu ve ön incelemesi güncellendi")
                        st.toast("✅ Durum ve Ön İnceleme kaydedildi!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("---")

                    # GEÇMİŞ İŞLEMLER LİSTESİ
                    if islemler:
                        st.markdown("**Geçmiş İşlem Zaman Çizelgesi:**")
                        for islem_item in reversed(islemler):
                            i_tarih = islem_item.get("Tarih", "-")
                            i_metin = islem_item.get("Islem", "")
                            st.caption(f"🗓️ **{i_tarih}**: {i_metin}")
                    else:
                        st.caption("*Henüz kayıtlı bir işlem yok.*")

        else:
            st.warning("Arama kriterinize uygun dosya bulunamadı.")
    else:
        st.info("Sistemde kayıtlı dosya bulunmamaktadır.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA EKLEME FORMU
# ==============================================================================
with col_right:
    st.subheader("➕ Yeni Dosya Ekle")
    
    with st.form(key="form_yeni_dosya_ekle", clear_on_submit=True):
        yeni_dosya_no = st.text_input("Dosya No", placeholder="Örn: 2025 D1 5400")
        yeni_firma = st.text_input("Firma Adı", placeholder="Örn: ABC Dış Ticaret Ltd. Şti.")
        yeni_aciklama = st.text_area("Açıklama / İlk İşlem", placeholder="Dosya ile ilgili ilk not veya durumu giriniz...")
        
        st.markdown("**İlk Durum Seçenekleri:**")
        c_add1, c_add2 = st.columns(2)
        with c_add1:
            add_bagli = st.checkbox("🔗 Bağlı", value=False)
            add_red = st.checkbox("🚫 Red", value=False)
            add_tescilde = st.checkbox("⏳ Tescilde Bekleyen", value=False)
            add_kapatma = st.checkbox("🏁 Kapatma Aşamasında", value=False)
        with c_add2:
            add_yazi = st.checkbox("✉️ Yazı Cevabı Bekleyen", value=False)
            add_incelenmedi = st.checkbox("🔍 İncelenmedi", value=False)
            add_incelemede = st.checkbox("🧐 İncelemede", value=False)
            add_mail = st.checkbox("📧 Mail Atıldı", value=False)
            
        btn_yeni_dosya = st.form_submit_button("➕ Dosyayı Kaydet", use_container_width=True)
        
        if btn_yeni_dosya:
            if yeni_dosya_no.strip() != "":
                # Aynı dosya numarasından var mı kontrolü
                var_mi = any(d.get("Dosya No", "").strip().lower() == yeni_dosya_no.strip().lower() for d in kayitlar)
                if var_mi:
                    st.error("Bu dosya numarası zaten kayıtlı!")
                else:
                    bugun_tarih = simdi_dt.strftime("%d.%m.%Y %H:%M")
                    ilk_islemler = []
                    if yeni_aciklama.strip() != "":
                        ilk_islemler.append({"Tarih": bugun_tarih, "Islem": yeni_aciklama.strip()})
                    
                    yeni_kayit = {
                        "Dosya No": yeni_dosya_no.strip(),
                        "Firma": yeni_firma.strip(),
                        "Aciklama": yeni_aciklama.strip(),
                        "OlusturmaTarihi": bugun_tarih,
                        "Islemler": ilk_islemler,
                        "BagliDosya": add_bagli,
                        "KapatmaRed": add_red,
                        "TescildeBekleyen": add_tescilde,
                        "KapatmaAsamasinda": add_kapatma,
                        "YaziCevabiBekleyen": add_yazi,
                        "Incelenmedi": add_incelenmedi,
                        "Incelemede": add_incelemede,
                        "MailAtildi": add_mail,
                        "MailTarihi": bugun_tarih[:10] if add_mail else "",
                        "SiraNo": 9999,
                        "IncelenmediSiraNo": 9999,
                        "IncelemedeSiraNo": 9999,
                        "OnInceleme": {
                            "Ekspertiz": False, "EkspertizKontrol": False,
                            "OzelSart233": False, "OzelSart233Kontrol": False,
                            "YMM": False, "YMMKontrol": False,
                            "IIGU": False, "IIGUKontrol": False
                        }
                    }
                    
                    kayitlar.append(yeni_kayit)
                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Yeni dosya eklendi: {yeni_dosya_no}")
                    st.success(f"✅ '{yeni_dosya_no}' nolu dosya başarıyla eklendi!")
                    st.rerun()
            else:
                st.warning("Lütfen bir Dosya No giriniz.")
