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

        # Önemli notları güvenli şekilde string listesine dönüştür
        onemli_notlar_data = []
        if isinstance(onemli_notlar_raw, list):
            for item in onemli_notlar_raw:
                if isinstance(item, dict):
                    val = item.get("Not") or item.get("metin") or str(item)
                    onemli_notlar_data.append(str(val))
                elif item is not None:
                    onemli_notlar_data.append(str(item))
        elif isinstance(onemli_notlar_raw, str) and onemli_notlar_raw.strip():
            onemli_notlar_data = [onemli_notlar_raw.strip()]

        # Hatırlatmaların list/dict yapısını kontrol et
        hatirlatmalar_data = []
        if isinstance(hatirlatmalar_raw, list):
            for h in hatirlatmalar_raw:
                if isinstance(h, dict):
                    hatirlatmalar_data.append(h)
                elif isinstance(h, str):
                    hatirlatmalar_data.append({"Metin": h, "Zaman": "", "Tamamlandi": False})

        if not isinstance(bolum_sirasi_data, list):
            bolum_sirasi_data = list(VARSAYILAN_BOLUM_SIRASI)

        for b in VARSAYILAN_BOLUM_SIRASI:
            if b not in bolum_sirasi_data:
                bolum_sirasi_data.append(b)

        # Dosyaların dict olduğunu doğrula ve eksik alanları tamamla
        yeni_format_data = []
        if isinstance(kayitlar_data, list):
            for item in kayitlar_data:
                if not isinstance(item, dict):
                    continue
                
                item.setdefault("Aciklama", "")
                item.setdefault("Islemler", [])
                item.setdefault("BagliDosya", False)
                item.setdefault("KapatmaRed", False)
                item.setdefault("TescildeBekleyen", False)
                item.setdefault("KapatmaAsamasinda", False)
                item.setdefault("YaziCevabiBekleyen", False)
                item.setdefault("Incelenmedi", False)
                item.setdefault("Incelemede", False)
                item.setdefault("MailAtildi", False)
                item.setdefault("MailTarihi", "")
                item.setdefault("SiraNo", 9999)
                item.setdefault("IncelenmediSiraNo", 9999)
                item.setdefault("IncelemedeSiraNo", 9999)
                
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

# EKRAN YAPILANDIRMASI: Sol Taraf %60, Sağ Taraf %40
col_left, col_right = st.columns([60, 40], gap="large")

# ==============================================================================
# SOL TARAF: GENİŞ DOSYA LİSTESİ VE GEÇMİŞ İŞLEMLER
# ==============================================================================
with col_left:
    st.subheader("📋 Kayıtlı Dosyalar ve İşlem Akışı")
    
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
                    exp_header = f"📂 **Dosya No:** {d_no} | 🏢 **Firma:** {firma} {simgeler}({len(islemler)} İşlem){mail_baslik_eki}"
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
                    # DURUM İŞARETLEYİCİLERİ VE KAYDET BUTONU
                    st.markdown("##### 📌 Dosya Durumu")
                    
                    c_chk1, c_chk2, c_chk3, c_chk4, c_chk5, c_chk6, c_chk7, c_chk8 = st.columns(8)
                    with c_chk1:
                        new_bagli = st.checkbox("🔗 Bağlı Dosya", value=bagli_durumu, key=f"chk_bagli_{d_no}_{d_idx}")
                    with c_chk2:
                        new_kapatma_red = st.checkbox("🚫 Red", value=kapatma_red_durumu, key=f"chk_red_{d_no}_{d_idx}")
                    with c_chk3:
                        new_tescilde = st.checkbox("⏳ Tescilde", value=tescilde_durumu, key=f"chk_tescilde_{d_no}_{d_idx}")
                    with c_chk4:
                        new_kapatma = st.checkbox("🏁 Kapatmada", value=kapatma_asamasinda_durumu, key=f"chk_kapatma_{d_no}_{d_idx}")
                    with c_chk5:
                        new_yazi = st.checkbox("✉️ Yazı Cevabı", value=yazi_cevabi_durumu, key=f"chk_yazi_{d_no}_{d_idx}")
                    with c_chk6:
                        new_incelenmedi = st.checkbox("🔍 İncelenmedi", value=incelenmedi_durumu, key=f"chk_incelenmedi_{d_no}_{d_idx}")
                    with c_chk7:
                        new_incelemede = st.checkbox("🧐 İncelemede", value=incelemede_durumu, key=f"chk_incelemede_{d_no}_{d_idx}")
                    with c_chk8:
                        new_mail = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"chk_mail_{d_no}_{d_idx}")

                    col_mail_tarihi, col_btn_durum = st.columns([1, 2], vertical_alignment="bottom")
                    with col_mail_tarihi:
                        if new_mail:
                            try:
                                varsayilan_tarih = datetime.strptime(mail_tarihi_val, "%d.%m.%Y").date() if mail_tarihi_val else simdi_dt.date()
                            except Exception:
                                varsayilan_tarih = simdi_dt.date()
                            yeni_mail_tarihi = st.date_input("Mail Tarihi", value=varsayilan_tarih, key=f"dt_mail_{d_no}_{d_idx}")
                            mail_tarihi_str = yeni_mail_tarihi.strftime("%d.%m.%Y")
                        else:
                            mail_tarihi_str = ""

                    with col_btn_durum:
                        st.markdown("<div class='save-status-container'>", unsafe_allow_html=True)
                        if st.button("💾 Durumu Kaydet", key=f"btn_save_status_{d_no}_{d_idx}"):
                            dosya["BagliDosya"] = new_bagli
                            dosya["KapatmaRed"] = new_kapatma_red
                            dosya["TescildeBekleyen"] = new_tescilde
                            dosya["KapatmaAsamasinda"] = new_kapatma
                            dosya["YaziCevabiBekleyen"] = new_yazi
                            dosya["Incelenmedi"] = new_incelenmedi
                            dosya["Incelemede"] = new_incelemede
                            dosya["MailAtildi"] = new_mail
                            dosya["MailTarihi"] = mail_tarihi_str
                            
                            verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} durumları güncellendi")
                            st.toast("✅ Durumlar başarıyla güncellendi!")
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("---")

                    # ANA AÇIKLAMA DÜZENLEME ALANI
                    col_acik_title, col_acik_btn = st.columns([80, 20], vertical_alignment="center")
                    with col_acik_title:
                        st.markdown("**📝 Ana Açıklama / Not:**")
                    with col_acik_btn:
                        if not st.session_state[edit_key]:
                            if st.button("✏️ Düzenle", key=f"btn_edit_acik_{d_no}_{d_idx}"):
                                st.session_state[edit_key] = True
                                st.rerun()

                    if st.session_state[edit_key]:
                        yeni_ana_aciklama = st.text_area("Açıklamayı Düzenle", value=ana_aciklama, key=f"txt_area_{d_no}_{d_idx}")
                        col_save, col_cancel = st.columns([1, 1])
                        with col_save:
                            if st.button("💾 Kaydet", key=f"btn_save_acik_{d_no}_{d_idx}", type="primary"):
                                dosya["Aciklama"] = yeni_ana_aciklama.strip()
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} açıklaması güncellendi")
                                st.session_state[edit_key] = False
                                st.toast("Açıklama güncellendi!")
                                st.rerun()
                        with col_cancel:
                            if st.button("❌ İptal", key=f"btn_cancel_acik_{d_no}_{d_idx}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                    else:
                        if ana_aciklama:
                            st.info(ana_aciklama)
                        else:
                            st.caption("*Henüz ana açıklama eklenmemiş.*")

                    st.markdown("---")

                    # YENİ İŞLEM EKLEME FORMU
                    st.markdown("**➕ Yeni İşlem / Gelişme Ekle:**")
                    with st.form(key=f"form_islem_ekle_{d_no}_{d_idx}", clear_on_submit=True):
                        c_islem_tarih, c_islem_metin = st.columns([2, 5])
                        with c_islem_tarih:
                            islem_tarihi = st.date_input("İşlem Tarihi", value=simdi_dt.date())
                        with c_islem_metin:
                            islem_metni = st.text_input("Yapılan İşlem Detayı", placeholder="Örn: Evraklar gönderildi, onay beklenecek...")
                        
                        submit_islem = st.form_submit_button("İşlemi Kaydet")
                        if submit_islem:
                            if islem_metni.strip() != "":
                                yeni_islem = {
                                    "Tarih": islem_tarihi.strftime("%d.%m.%Y"),
                                    "Islem": islem_metni.strip()
                                }
                                dosya["Islemler"].insert(0, yeni_islem)
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyasına yeni işlem eklendi")
                                st.toast("İşlem kaydedildi!")
                                st.rerun()
                            else:
                                st.warning("İşlem detayı boş olamaz.")

                    # GEÇMİŞ İŞLEMLER LİSTESİ
                    st.markdown("**📜 Geçmiş İşlemler:**")
                    if islemler:
                        for idx, islem in enumerate(islemler):
                            c_tarih, c_detay, c_sil = st.columns([2, 7, 1], vertical_alignment="center")
                            with c_tarih:
                                st.caption(f"📅 **{islem.get('Tarih', '')}**")
                            with c_detay:
                                st.text(islem.get('Islem', ''))
                            with c_sil:
                                if st.button("🗑️", key=f"del_islem_{d_no}_{d_idx}_{idx}", help="İşlemi Sil"):
                                    dosya["Islemler"].pop(idx)
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} işlem silindi")
                                    st.toast("İşlem silindi!")
                                    st.rerun()
                    else:
                        st.caption("*Henüz kayıtlı işlem yok.*")
        else:
            st.warning("Arama kriterinize uygun dosya bulunamadı.")
    else:
        st.info("Henüz kayıtlı dosya bulunmamaktadır. Sağ taraftaki formdan yeni dosya ekleyebilirsiniz.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA EKLEME, EXCEL YÜKLEME VE TOPLU SORGULAMA/DÜZENLEME
# ==============================================================================
with col_right:
    st.subheader("➕ Yeni Dosya Ekle")
    
    with st.form(key="form_yeni_dosya_ekle", clear_on_submit=True):
        yeni_dosya_no = st.text_input("Dosya No *", placeholder="Örn: 2025 D1 5400")
        yeni_firma = st.text_input("Firma Adı", placeholder="Örn: ABC Lojistik A.Ş.")
        yeni_aciklama = st.text_area("Açıklama / Not", placeholder="Dosya hakkında genel notlar...")
        
        st.markdown("**İlk İşlem (Opsiyonel):**")
        c_i_tarih, c_i_metin = st.columns([2, 3])
        with c_i_tarih:
            ilk_islem_tarihi = st.date_input("İşlem Tarihi", value=simdi_dt.date())
        with c_i_metin:
            ilk_islem_metni = st.text_input("İşlem Detayı", placeholder="Örn: Dosya açıldı")
            
        submit_yeni_dosya = st.form_submit_button("➕ Dosyayı Kaydet", use_container_width=True, type="primary")

        if submit_yeni_dosya:
            if yeni_dosya_no.strip() != "":
                zaten_var = any(d.get("Dosya No", "").strip().lower() == yeni_dosya_no.strip().lower() for d in kayitlar)
                
                if zaten_var:
                    st.error(f"'{yeni_dosya_no}' numaralı dosya zaten sistemde mevcut!")
                else:
                    ilk_islemler = []
                    if ilk_islem_metni.strip() != "":
                        ilk_islemler.append({
                            "Tarih": ilk_islem_tarihi.strftime("%d.%m.%Y"),
                            "Islem": ilk_islem_metni.strip()
                        })

                    yeni_kayit = {
                        "Dosya No": yeni_dosya_no.strip(),
                        "Firma": yeni_firma.strip() if yeni_firma else "-",
                        "Aciklama": yeni_aciklama.strip(),
                        "OlusturmaTarihi": simdi_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "Islemler": ilk_islemler,
                        "BagliDosya": False,
                        "KapatmaRed": False,
                        "TescildeBekleyen": False,
                        "KapatmaAsamasinda": False,
                        "YaziCevabiBekleyen": False,
                        "Incelenmedi": False,
                        "Incelemede": False,
                        "MailAtildi": False,
                        "MailTarihi": "",
                        "SiraNo": 9999,
                        "IncelenmediSiraNo": 9999,
                        "IncelemedeSiraNo": 9999
                    }

                    kayitlar.append(yeni_kayit)
                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Yeni dosya eklendi: {yeni_dosya_no}")
                    st.success(f"'{yeni_dosya_no}' başarıyla eklendi!")
                    st.rerun()
            else:
                st.error("Lütfen Dosya No alanını doldurunuz.")

    st.markdown("---")

    # 📑 EXCEL İLE TOPLU DOSYA AÇIKLAMASI GÜNCELLEME
    st.subheader("📑 Excel İle Toplu Açıklama Güncelle")
    st.caption("İçinde **Dosya No** ve **Açıklama** sütunları olan bir Excel dosyası (.xlsx) yükleyiniz.")

    uploaded_file = st.file_uploader("Excel Dosyası Seçin", type=["xlsx", "xls"], key="excel_updater_input")

    if uploaded_file is not None:
        try:
            df_upload = pd.read_excel(uploaded_file)
            
            # Sütun isimlerini esnek kontrol etme (boşluk temizleme)
            df_upload.columns = [str(col).strip() for col in df_upload.columns]
            
            # Kolon başlıklarını esnek yakalama
            dosya_no_col = next((c for c in df_upload.columns if c.lower() in ["dosya no", "dosyano", "dosya_no"]), None)
            aciklama_col = next((c for c in df_upload.columns if c.lower() in ["açıklama", "aciklama", "not", "ana açıklama"]), None)

            if dosya_no_col and aciklama_col:
                st.success(f"✅ Excel okundu: **{len(df_upload)}** satır veri bulundu.")
                
                # Önizleme tablosu
                st.dataframe(df_upload[[dosya_no_col, aciklama_col]].head(5), use_container_width=True)

                if st.button("🚀 Excel'deki Verilerle Açıklamaları Güncelle", type="primary", use_container_width=True):
                    guncellenen_sayi = 0
                    bulunamayanlar = []

                    for _, row in df_upload.iterrows():
                        target_no = str(row[dosya_no_col]).strip()
                        yeni_aciklama = str(row[aciklama_col]).strip() if pd.notna(row[aciklama_col]) else ""

                        if target_no:
                            match = next((d for d in kayitlar if str(d.get("Dosya No", "")).strip().lower() == target_no.lower()), None)
                            if match:
                                match["Aciklama"] = yeni_aciklama
                                guncellenen_sayi += 1
                            else:
                                bulunamayanlar.append(target_no)

                    if guncellenen_sayi > 0:
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{guncellenen_sayi} dosya açıklaması Excel ile güncellendi")
                        st.toast(f"✅ {guncellenen_sayi} adet dosya açıklaması başarıyla güncellendi!")
                        
                    if bulunamayanlar:
                        st.warning(f"⚠️ Sistemde bulunamayan dosyalar ({len(bulunamayanlar)} adet): {', '.join(bulunamayanlar)}")
                    
                    if guncellenen_sayi > 0:
                        st.rerun()
            else:
                st.error("❌ Excel dosyasında 'Dosya No' ve 'Açıklama' sütunları bulunamadı. Lütfen sütun başlıklarınızı kontrol ediniz.")

        except Exception as e:
            st.error(f"Excel dosyası işlenirken bir hata oluştu: {e}")

    st.markdown("---")
    
    # 🔍 MANUEL TOPLU DOSYA AÇIKLAMASI SORGULAMA VE DÜZENLEME MODÜLÜ
    st.subheader("🔍 Toplu Dosya Açıklaması Gör / Düzenle")
    st.caption("Birden fazla dosya numarasını **virgül (,)** veya **alt satıra (Enter)** geçerek yazabilirsiniz.")

    toplu_sorgu_input = st.text_area(
        "Dosya Numaralarını Giriniz", 
        height=90, 
        placeholder="Örn:\n2024 D1 414\n2025 D1 5400, 2023 D1 1012",
        key="txt_toplu_sorgu_dosya_no"
    )

    if toplu_sorgu_input.strip():
        ham_liste = toplu_sorgu_input.replace(",", "\n").split("\n")
        aranan_dosya_nolari = [d.strip() for d in ham_liste if d.strip()]
        aranan_dosya_nolari = list(dict.fromkeys(aranan_dosya_nolari))

        bulunan_dosyalar = []
        bulunamayanlar = []

        for target_no in aranan_dosya_nolari:
            target_lower = target_no.lower()
            match = next((d for d in kayitlar if d.get("Dosya No", "").strip().lower() == target_lower), None)
            if match:
                bulunan_dosyalar.append(match)
            else:
                bulunamayanlar.append(target_no)

        if bulunamayanlar:
            st.warning(f"⚠️ Bulunamayan Dosyalar ({len(bulunamayanlar)}): {', '.join(bulunamayanlar)}")

        if bulunan_dosyalar:
            st.info(f"📋 **{len(bulunan_dosyalar)}** adet dosya bulundu. Aşağıdan açıklamalarını düzenleyebilirsiniz:")
            
            with st.form(key="form_toplu_aciklama_kaydet"):
                yeni_aciklamalar_dict = {}
                
                for b_idx, b_dosya in enumerate(bulunan_dosyalar):
                    b_dno = b_dosya.get("Dosya No", "")
                    b_firma = b_dosya.get("Firma", "-")
                    b_aciklama = b_dosya.get("Aciklama", "")

                    st.markdown(f"**📂 {b_dno}** | <small>Firma: {b_firma}</small>", unsafe_allow_html=True)
                    
                    yeni_val = st.text_area(
                        label=f"Açıklama ({b_dno})",
                        value=b_aciklama,
                        key=f"toplu_txt_{b_dno}_{b_idx}",
                        height=80,
                        label_visibility="collapsed"
                    )
                    yeni_aciklamalar_dict[b_dno] = yeni_val
                    st.markdown("<hr style='margin: 0.4rem 0 !important;'>", unsafe_allow_html=True)

                submit_toplu_kaydet = st.form_submit_button("💾 Listelenen Tüm Dosya Açıklamalarını Kaydet", type="primary", use_container_width=True)

                if submit_toplu_kaydet:
                    guncellenen_sayisi = 0
                    for b_dosya in bulunan_dosyalar:
                        d_no_key = b_dosya.get("Dosya No", "")
                        if d_no_key in yeni_aciklamalar_dict:
                            b_dosya["Aciklama"] = yeni_aciklamalar_dict[d_no_key].strip()
                            guncellenen_sayisi += 1
                    
                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{guncellenen_sayisi} dosya açıklaması toplu güncellendi")
                    st.toast(f"✅ {guncellenen_sayisi} adet dosya açıklaması başarıyla güncellendi!")
                    st.rerun()

    st.markdown("---")

    # JSON VE SADECE ÖZET EXCEL İNDİRME / YEDEKLEME
    st.subheader("📊 Veri İndir ve Yedekle")

    if kayitlar:
        ozet_excel_listesi = []
        for d in kayitlar:
            tam_dosya_no = str(d.get("Dosya No", "")).strip()
            parcalar = tam_dosya_no.split()
            
            yil = parcalar[0] if len(parcalar) > 0 else ""
            kod = parcalar[1] if len(parcalar) > 1 else ""
            sira_no = " ".join(parcalar[2:]) if len(parcalar) > 2 else ""

            ozet_excel_listesi.append({
                "Yıl / Dönem": yil,
                "Birim / Kod": kod,
                "Dosya Sıra No": sira_no,
                "Ana Açıklama / Not": d.get("Aciklama", "")
            })

        df_ozet = pd.DataFrame(ozet_excel_listesi)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_ozet.to_excel(writer, index=False, sheet_name='Ozet_Rapor')
        
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="📥 Özet Rapor İndir",
            data=excel_data,
            file_name=f"Ozet_Rapor_{simdi_dt.strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    json_str = json.dumps({
        "Dosyalar": kayitlar,
        "OnemliNotlar": mevcut_onemli_notlar,
        "Hatirlatmalar": mevcut_hatirlatmalar,
        "BolumSirasi": mevcut_bolum_sirasi
    }, ensure_ascii=False, indent=2)

    st.download_button(
        label="💾 JSON Yedeği İndir",
        data=json_str,
        file_name=f"dosya_takip_backup_{simdi_dt.strftime('%d_%m_%Y')}.json",
        mime="application/json",
        use_container_width=True
    )
