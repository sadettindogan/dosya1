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

# Ultra Sıkılaştırılmış CSS ve Sanatsal Mavi Kaydırma Tuşları
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

    /* Yanıp Sönen Hatırlatma Stili */
    @keyframes blinker {
        0% { background-color: #ffe4e6; border-color: #ef4444; color: #991b1b; }
        50% { background-color: #fef08a; border-color: #eab308; color: #854d0e; }
        100% { background-color: #ffe4e6; border-color: #ef4444; color: #991b1b; }
    }
    .blinking-reminder {
        animation: blinker 1s linear infinite;
        padding: 4px 8px;
        border-radius: 4px;
        border: 1.5px solid #ef4444;
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }

    /* SANATSAL, MİNİMAL VE MAVİ KAYDIRMA TUŞLARI */
    .stButton > button {
        opacity: 0.15;
        color: #2563eb !important; /* Mavi Simge */
        border: none !important;
        background: transparent !important;
        padding: 0px !important;
        font-size: 0.7rem !important; /* Küçük sanatsal boyut */
        width: 22px !important;
        height: 22px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        opacity: 1.0 !important;
        color: #1d4ed8 !important;
        background-color: #eff6ff !important; /* Açık Mavi Arka Plan */
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
        transform: scale(1.2) !important; /* Büyüme Animasyonu */
    }
</style>
""", unsafe_allow_html=True)

st.title("📁 Dosya Takibi")
st.markdown("---")

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
# DİNAMİK BÖLÜM SIRALAMA MEKANİZMASI (SANATSAL MAVİ BUTONLAR)
# ==============================================================================
turkey_tz = pytz.timezone("Europe/Istanbul")
simdi_dt = datetime.now(turkey_tz)

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
                            h_zaman_dt = datetime.strptime(h_zaman_str, "%Y-%m-%d %H:%M:%S")
                            h_zaman_dt = turkey_tz.localize(h_zaman_dt)
                            zaman_geldi = (simdi_dt >= h_zaman_dt) and not h_tamamlandi
                        except Exception:
                            zaman_geldi = False

                        c_h_text, c_h_action = st.columns([75, 25], vertical_alignment="center")

                        with c_h_text:
                            if zaman_geldi:
                                st.markdown(f"<div class='blinking-reminder'>🔔 {h_metin_val}<br><small>🗓️ {h_zaman_str[11:16]}</small></div>", unsafe_allow_html=True)
                            else:
                                gosterim_tarih = h_zaman_str[8:10] + "." + h_zaman_str[5:7] + " " + h_zaman_str[11:16]
                                if h_tamamlandi:
                                    st.caption(f"✅ ~~{h_metin_val}~~")
                                else:
                                    st.warning(f"⏰ {h_metin_val} ({gosterim_tarih})")

                        with c_h_action:
                            if zaman_geldi:
                                if st.button("Tamam", key=f"btn_ok_h_{h_idx}", type="primary", help="Duraklat"):
                                    h_item["Tamamlandi"] = True
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma tamamlandı")
                                    st.rerun()
                            else:
                                if st.button("🗑️", key=f"btn_del_h_{h_idx}", help="Sil"):
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
                    st.markdown("**📌 Dosya Durumu**")
                    col_b1, col_b2, col_b3, col_b4, col_b5, col_b6, col_b7, col_b8 = st.columns(8)
                    
                    with col_b1:
                        ch_bagli = st.checkbox("🔗 Bağlı", value=bagli_durumu, key=f"chk_bagli_{d_no}_{d_idx}")
                    with col_b2:
                        ch_red = st.checkbox("❌ Kapatma Red", value=kapatma_red_durumu, key=f"chk_red_{d_no}_{d_idx}")
                    with col_b3:
                        ch_tescild = st.checkbox("⏳ Tescilde", value=tescilde_durumu, key=f"chk_tescild_{d_no}_{d_idx}")
                    with col_b4:
                        ch_kapatma = st.checkbox("🏁 Kapatmada", value=kapatma_asamasinda_durumu, key=f"chk_kapatma_{d_no}_{d_idx}")
                    with col_b5:
                        ch_yazi = st.checkbox("✉️ Yazı Cevabı", value=yazi_cevabi_durumu, key=f"chk_yazi_{d_no}_{d_idx}")
                    with col_b6:
                        ch_incel = st.checkbox("🔍 İncelenmedi", value=incelenmedi_durumu, key=f"chk_incel_{d_no}_{d_idx}")
                    with col_b7:
                        ch_incmd = st.checkbox("🧐 İncelemede", value=incelemede_durumu, key=f"chk_incmd_{d_no}_{d_idx}")
                    with col_b8:
                        ch_mail = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"chk_mail_{d_no}_{d_idx}")

                    guncel_mail_tarihi = mail_tarihi_val
                    if ch_mail:
                        c_m_lbl, c_m_input = st.columns([2, 3], vertical_alignment="center")
                        with c_m_lbl:
                            st.caption("📅 **Mail Gönderim Tarihi:**")
                        with c_m_input:
                            guncel_mail_tarihi = st.text_input(
                                "Mail Tarihi", 
                                value=mail_tarihi_val if mail_tarihi_val else datetime.now().strftime("%d.%m.%Y"), 
                                key=f"inp_mail_date_{d_no}_{d_idx}",
                                label_visibility="collapsed",
                                placeholder="GG.AA.YYYY"
                            )

                    c_status_save, _ = st.columns([2, 5])
                    with c_status_save:
                        if st.button("💾 Durumu Kaydet", key=f"btn_save_status_{d_no}_{d_idx}", use_container_width=True):
                            dosya["BagliDosya"] = ch_bagli
                            dosya["KapatmaRed"] = ch_red
                            dosya["TescildeBekleyen"] = ch_tescild
                            dosya["KapatmaAsamasinda"] = ch_kapatma
                            dosya["YaziCevabiBekleyen"] = ch_yazi
                            dosya["Incelenmedi"] = ch_incel
                            dosya["Incelemede"] = ch_incmd
                            dosya["MailAtildi"] = ch_mail
                            dosya["MailTarihi"] = guncel_mail_tarihi.strip() if ch_mail else ""
                            
                            verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosya durumu güncellendi")
                            st.toast(f"✅ '{d_no}' dosyasının durumu başarıyla kaydedildi!")
                            st.rerun()

                    st.markdown("---")

                    st.markdown("**📝 Dosya Durum Detayı**")

                    if not st.session_state[edit_key]:
                        c_aciklama, c_edit_btn = st.columns([5, 1], vertical_alignment="center")
                        with c_aciklama:
                            if ana_aciklama.strip() != "":
                                st.info(ana_aciklama)
                            else:
                                st.caption("*Bu dosya için henüz durum detayı eklenmemiş.*")
                        with c_edit_btn:
                            if st.button("✏️ Düzenle", key=f"btn_edit_{d_no}_{d_idx}", use_container_width=True):
                                st.session_state[edit_key] = True
                                st.rerun()
                    else:
                        with st.form(key=f"form_edit_aciklama_{d_no}_{d_idx}"):
                            yeni_aciklama_val = st.text_area("Durum Detayını Güncelle", value=ana_aciklama, height=70)
                            col_save, col_cancel = st.columns([1, 1])
                            
                            with col_save:
                                submit_aciklama = st.form_submit_button("💾 Kaydet", use_container_width=True)
                            with col_cancel:
                                cancel_aciklama = st.form_submit_button("❌ İptal", use_container_width=True)
                                
                            if submit_aciklama:
                                dosya["Aciklama"] = yeni_aciklama_val.strip()
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyasının durum detayı güncellendi")
                                st.session_state[edit_key] = False
                                st.toast("✅ Durum detayı güncellendi!")
                                st.rerun()
                                
                            if cancel_aciklama:
                                st.session_state[edit_key] = False
                                st.rerun()

                    st.markdown(f"**➕ `{d_no}` Nolu Dosyaya Yeni İşlem Ekle**")
                    with st.form(key=f"add_islem_form_main_{d_no}_{d_idx}", clear_on_submit=True):
                        col_inp, col_btn = st.columns([3, 1], vertical_alignment="center")
                        
                        with col_inp:
                            yeni_islem_text = st.text_input("İşlem Açıklaması", key=f"inp_{d_no}_{d_idx}", placeholder="Yapılan işlemi yazınız...", label_visibility="collapsed")
                        
                        with col_btn:
                            submit_islem = st.form_submit_button("➕ İşlem Ekle", use_container_width=True)
                            
                        if submit_islem:
                            if yeni_islem_text.strip() != "":
                                simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                                
                                islemler.append({
                                    "Aciklama": yeni_islem_text.strip(),
                                    "Tarih": simdi
                                })
                                
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyasına yeni işlem eklendi")
                                st.toast("✅ İşlem başarıyla eklendi!")
                                st.rerun()
                            else:
                                st.warning("İşlem açıklaması boş olamaz.")

                    st.markdown("**🕒 Dosyada bugüne kadar yapılan işlemler**")
                    if islemler:
                        for i_idx, item in enumerate(islemler):
                            c_text, c_date, c_del = st.columns([5, 3, 1], vertical_alignment="center")
                            
                            with c_text:
                                st.markdown(f"**{i_idx + 1}. Adım:** {item.get('Aciklama')}")
                            
                            with c_date:
                                st.caption(f"🗓️ {item.get('Tarih')}")
                            
                            with c_del:
                                if st.button("🗑️ Sil", key=f"del_main_{d_no}_{i_idx}", help="Bu işlemi sil"):
                                    islemler.pop(i_idx)
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyasından işlem silindi")
                                    st.toast("Silindi!")
                                    st.rerun()
                    else:
                        st.caption("*Henüz ilave bir işlem adımı eklenmedi.*")
                st.write("") 
        else:
            st.info("Arama kriterinize uygun dosya bulunamadı.")
    else:
        st.info("Sistemde henüz kayıtlı dosya bulunmuyor.")

# ==============================================================================
# SAĞ TARAF: VERİ GİRİŞİ, TOPLU İŞLEM, RAPORLAMA VE TÜMÜNÜ SİL PANELİ
# ==============================================================================
with col_right:
    st.subheader("📌 İşlem Paneli")
    
    tab_tekli, tab_excel, tab_rapor = st.tabs(["✏️ Tekli Ekle", "📋 Toplu Yapıştır", "📊 Rapor Oluştur"])
    
    with tab_tekli:
        with st.form("yeni_dosya_formu_sag", clear_on_submit=True):
            dosya_no = st.text_input("Dosya No / Adı (Örn: 2025 D1 5400)", placeholder="Örn: 2025 D1 5400")
            firma = st.text_input("Firma Unvanı", placeholder="Örn: ISIK CELIK SAN.VE TIC.A.S.")
            islem = st.text_area("Dosya Durum Detayı", placeholder="Detay metnini girin...", height=80)
            
            c_in1, c_in2 = st.columns(2)
            with c_in1:
                bagli_durumu_input = st.checkbox("🔗 Bağlı Dosya")
                tescilde_durumu_input = st.checkbox("⏳ Tescilde Bekleyen")
                yazi_cevabi_input = st.checkbox("✉️ Yazı Cevabı Bekleyen")
                incelenmedi_input = st.checkbox("🔍 İncelenmedi")
            with c_in2:
                kapatma_red_input = st.checkbox("❌ Kapatma Red")
                kapatma_asamasinda_input = st.checkbox("🏁 Kapatma Aşamasında")
                incelemede_input = st.checkbox("🧐 İncelemede")
                mail_atildi_input = st.checkbox("📧 Firmaya Mail Atıldı")
                
            mail_tarihi_input = st.text_input("Mail Tarihi (Opsiyonel)", value=datetime.now().strftime("%d.%m.%Y"), placeholder="GG.AA.YYYY")

            submit_yeni = st.form_submit_button("📂 Dosya Oluştur / Güncelle", use_container_width=True)

            if submit_yeni:
                if dosya_no.strip() != "":
                    clean_dosya = dosya_no.strip()
                    clean_firma = firma.strip() if firma.strip() != "" else "-"
                    clean_aciklama = islem.strip()
                    simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")

                    mevcut = next((d for d in kayitlar if str(d.get("Dosya No")) == clean_dosya), None)
                    
                    if mevcut:
                        if clean_aciklama != "":
                            mevcut["Aciklama"] = clean_aciklama
                        if clean_firma != "-" and clean_firma != "":
                            mevcut["Firma"] = clean_firma
                        mevcut["BagliDosya"] = bagli_durumu_input
                        mevcut["KapatmaRed"] = kapatma_red_input
                        mevcut["TescildeBekleyen"] = tescilde_durumu_input
                        mevcut["KapatmaAsamasinda"] = kapatma_asamasinda_input
                        mevcut["YaziCevabiBekleyen"] = yazi_cevabi_input
                        mevcut["Incelenmedi"] = incelenmedi_input
                        mevcut["Incelemede"] = incelemede_input
                        mevcut["MailAtildi"] = mail_atildi_input
                        mevcut["MailTarihi"] = mail_tarihi_input.strip() if mail_atildi_input else ""
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{clean_dosya} dosyasının bilgileri güncellendi")
                        st.toast(f"✅ '{clean_dosya}' güncellendi!")
                    else:
                        yeni_dosya = {
                            "Dosya No": clean_dosya,
                            "Firma": clean_firma,
                            "Aciklama": clean_aciklama,
                            "BagliDosya": bagli_durumu_input,
                            "KapatmaRed": kapatma_red_input,
                            "TescildeBekleyen": tescilde_durumu_input,
                            "KapatmaAsamasinda": kapatma_asamasinda_input,
                            "YaziCevabiBekleyen": yazi_cevabi_input,
                            "Incelenmedi": incelenmedi_input,
                            "Incelemede": incelemede_input,
                            "MailAtildi": mail_atildi_input,
                            "MailTarihi": mail_tarihi_input.strip() if mail_atildi_input else "",
                            "OlusturmaTarihi": simdi,
                            "SiraNo": 9999,
                            "IncelenmediSiraNo": 9999,
                            "IncelemedeSiraNo": 9999,
                            "Islemler": []
                        }
                        kayitlar.append(yeni_dosya)
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Yeni dosya eklendi: {clean_dosya}")
                        st.toast(f"✅ '{clean_dosya}' oluşturuldu!")
                    st.rerun()
                else:
                    st.warning("Lütfen Dosya No alanını doldurun.")

    with tab_excel:
        st.caption("Excel'deki **5 Sütunluk** veriyi buraya yapıştırabilirsiniz:")
        st.caption("`DIIBNO1` | `DIIBNO2` | `DIIBNO3` | `Firma Unvanı` | `Durum Detayı`")
        
        with st.form("excel_paste_form", clear_on_submit=True):
            pasted_data = st.text_area("Excel Verisini Yapıştırın", placeholder="2025\tD1\t5400\tISIK CELIK SAN.VE TIC.A.S.\tİnceleme yapılıyor.", height=120)
            submit_excel = st.form_submit_button("⚡ Toplu Verileri Kaydet", use_container_width=True)
            
            if submit_excel:
                if pasted_data.strip() != "":
                    eklenen_sayi = 0
                    lines = pasted_data.strip().split("\n")
                    for line in lines:
                        parts = line.split("\t")
                        if len(parts) >= 4:
                            sutun1 = parts[0].strip()
                            sutun2 = parts[1].strip()
                            sutun3 = parts[2].strip()
                            c_firma = parts[3].strip()
                            c_aciklama = parts[4].strip() if len(parts) >= 5 else ""
                            
                            c_dno = " ".join(filter(None, [sutun1, sutun2, sutun3]))
                            simdi = datetime.now(turkey_tz).strftime("%Y-%m-%d %H:%M:%S")
                            
                            if c_dno:
                                mevcut = next((d for d in kayitlar if str(d.get("Dosya No")) == c_dno), None)
                                if mevcut:
                                    if c_aciklama:
                                        mevcut["Aciklama"] = c_aciklama
                                    if c_firma and mevcut.get("Firma") in ["-", ""]:
                                        mevcut["Firma"] = c_firma
                                else:
                                    kayitlar.append({
                                        "Dosya No": c_dno,
                                        "Firma": c_firma if c_firma else "-",
                                        "Aciklama": c_aciklama,
                                        "BagliDosya": False,
                                        "KapatmaRed": False,
                                        "TescildeBekleyen": False,
                                        "KapatmaAsamasinda": False,
                                        "YaziCevabiBekleyen": False,
                                        "Incelenmedi": False,
                                        "Incelemede": False,
                                        "MailAtildi": False,
                                        "MailTarihi": "",
                                        "OlusturmaTarihi": simdi,
                                        "SiraNo": 9999,
                                        "IncelenmediSiraNo": 9999,
                                        "IncelemedeSiraNo": 9999,
                                        "Islemler": []
                                    })
                                eklenen_sayi += 1
                                
                    if eklenen_sayi > 0:
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Excel'den {eklenen_sayi} adet kayıt eklendi")
                        st.toast(f"✅ Toplam {eklenen_sayi} adet dosya kaydı işlendi!")
                        st.rerun()
                    else:
                        st.warning("Geçerli formatta veri bulunamadı.")
                else:
                    st.warning("Yapıştırılan alan boş olamaz.")

    with tab_rapor:
        st.caption("Excel tablonuzla birebir aynı formatta (5 Sütunlu) rapor oluşturur.")
        
        col_rapor, col_temizle = st.columns(2)
        
        with col_rapor:
            if st.button("📊 Rapor Oluştur", use_container_width=True):
                if kayitlar:
                    rapor_metni = "DIIBNO1\tDIIBNO2\tDIIBNO3\tFirma Unvanı\tDurum Detayı\n"
                    
                    for dosya in kayitlar:
                        d_no = dosya.get("Dosya No", "")
                        firma = dosya.get("Firma", "")
                        ana_aciklama = dosya.get("Aciklama", "")
                        islemler = dosya.get("Islemler", [])
                        
                        parcalar = d_no.split(" ")
                        d1 = parcalar[0] if len(parcalar) > 0 else ""
                        d2 = parcalar[1] if len(parcalar) > 1 else ""
                        d3 = " ".join(parcalar[2:]) if len(parcalar) > 2 else ""
                        
                        tum_aciklamalar = []
                        if ana_aciklama.strip() != "":
                            tum_aciklamalar.append(ana_aciklama.strip())
                        
                        for item in islemler:
                            if item.get("Aciklama"):
                                tum_aciklamalar.append(item.get("Aciklama").strip())
                        
                        final_aciklama = " | ".join(tum_aciklamalar)
                        
                        rapor_metni += f"{d1}\t{d2}\t{d3}\t{firma}\t{final_aciklama}\n"
                    
                    st.session_state["rapor_cikti"] = rapor_metni
                else:
                    st.info("Raporlanacak kayıtlı dosya bulunmuyor.")

        with col_temizle:
            if st.button("🧹 Temizle", use_container_width=True):
                if "rapor_cikti" in st.session_state:
                    st.session_state["rapor_cikti"] = ""
                    st.rerun()

        if "rapor_cikti" in st.session_state and st.session_state["rapor_cikti"]:
            st.markdown("**Excel Tablo Çıktısı:**")
            st.caption("📋 Sağ üstteki **Kopyala** simgesine tıklayıp Excel sayfanıza doğrudan `Ctrl + V` ile yapıştırabilirsiniz.")
            st.code(st.session_state["rapor_cikti"], language="text")

    st.divider()
    
    st.markdown("##### ⚠️ Veritabanı Yönetimi")
    
    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False

    if not st.session_state.confirm_delete_all:
        if st.button("🚨 Tüm Dosyaları Sil", use_container_width=True, type="secondary"):
            st.session_state.confirm_delete_all = True
            st.rerun()
    else:
        st.error("Tüm veritabanı silinecek! Emin misiniz?")
        col_evet, col_hayir = st.columns(2)
        
        with col_evet:
            if st.button("✅ Evet, Tümünü Sil", type="primary", use_container_width=True):
                verileri_kaydet([], [], [], VARSAYILAN_BOLUM_SIRASI, "Tüm dosyalar veritabanından silindi")
                st.session_state.confirm_delete_all = False
                if "rapor_cikti" in st.session_state:
                    st.session_state["rapor_cikti"] = ""
                st.toast("✅ Tüm dosyalar silindi!")
                st.rerun()
                
        with col_hayir:
            if st.button("❌ İptal Et", use_container_width=True):
                st.session_state.confirm_delete_all = False
                st.rerun()
