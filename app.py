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

# Kesin CSS Düzeltmeleri ve Kompakt Görünüm
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
        padding-top: 0.1rem !important;
        padding-bottom: 0.1rem !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        margin-bottom: 0.2rem !important;
        min-height: auto !important;
    }

    /* Üst Sütun Alanları İçin Kompakt Fontlar */
    h3 {
        font-size: 0.95rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* Dijital Saat Stili */
    .digital-clock {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.75rem;
        font-weight: bold;
        color: #008080;
        background-color: #f0f4f8;
        padding: 1px 4px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 2px;
        border: 1px solid #cbd5e1;
    }

    /* Zamanı Gelen Hatırlatma Stili */
    .red-reminder-box {
        background-color: #fee2e2;
        border: 1px solid #ef4444;
        color: #991b1b;
        padding: 4px 6px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.75rem;
        margin-bottom: 2px;
    }

    /* Ana Başlık Altındaki Kırmızı Uyarı Yazısı */
    .header-red-alert {
        background-color: #dc2626;
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 2px;
        margin-bottom: 5px;
    }

    /* MODERN, KÜÇÜK VE KALİTELİ TAŞIMA BUTONLARI */
    button[help*="Taş"], button[help*="Kaydır"] {
        opacity: 0.85 !important;
        color: #2563eb !important; /* Canlı Mavi */
        border: 1px solid #bfdbfe !important; /* İnce Yumuşak Çerçeve */
        background-color: #f0f9ff !important; /* İptal Etiketi Zemin Rengi */
        padding: 0px !important;
        font-size: 0.70rem !important;
        font-weight: bold !important;
        width: 20px !important;
        height: 20px !important;
        min-width: 20px !important;
        min-height: 20px !important;
        border-radius: 6px !important; /* Hafif Yuvarlatılmış Köşeler */
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important; /* Hafif Derinlik Gölgesi */
        transition: all 0.15s ease-in-out !important;
    }

    /* Üzerine Gelindiğinde (Hover Stili) */
    button[help*="Taş"]:hover, button[help*="Kaydır"]:hover {
        opacity: 1.0 !important;
        color: #ffffff !important;
        background-color: #2563eb !important; /* Mavi Dolgu */
        border-color: #1d4ed8 !important;
        transform: translateY(-1px) !important; /* Hafif Yükselme Efekti */
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25) !important;
    }

    /* DURUMU KAYDET BUTONU */
    .save-status-container button {
        width: auto !important;
        min-width: 130px !important;
        height: 28px !important;
        padding: 2px 12px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        background-color: #2563eb !important;
        border: 1px solid #1d4ed8 !important;
        border-radius: 5px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GITHUB BAĞLANTISI VE VERİ OKUMA ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = st.secrets["FILE_PATH"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

VARSAYILAN_BOLUM_SIRASI = [
    "kapatma", "incelenmedi", "incelemede", "bagli", 
    "kapatma_red", "tescilde", "yazi_cevabi", "mail_atildi", 
    "notlar", "hatirlatma"
]

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
                
                # Sıralama No Alanları
                item.setdefault("SiraNo", 9999)
                item.setdefault("IncelenmediSiraNo", 9999)
                item.setdefault("IncelemedeSiraNo", 9999)
                item.setdefault("BagliSiraNo", 9999)
                item.setdefault("KapatmaRedSiraNo", 9999)
                item.setdefault("TescildeSiraNo", 9999)
                item.setdefault("YaziCevabiSiraNo", 9999)
                item.setdefault("MailAtildiSiraNo", 9999)
                
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
# DİNAMİK 10 SÜTUNLU SIRALAMA MEKANİZMASI (8 BAYRAK LİSTESİ + NOTLAR + HATIRLATMA)
# ==============================================================================
def bolum_sol_sag_kaydir(bolum_kodu, yon):
    idx = mevcut_bolum_sirasi.index(bolum_kodu)
    if yon == "sol" and idx > 0:
        mevcut_bolum_sirasi[idx], mevcut_bolum_sirasi[idx - 1] = mevcut_bolum_sirasi[idx - 1], mevcut_bolum_sirasi[idx]
    elif yon == "sag" and idx < len(mevcut_bolum_sirasi) - 1:
        mevcut_bolum_sirasi[idx], mevcut_bolum_sirasi[idx + 1] = mevcut_bolum_sirasi[idx + 1], mevcut_bolum_sirasi[idx]
    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{bolum_kodu} bölümü {yon}a kaydırıldı")
    st.rerun()

def liste_siralama_render(filtre_anahtar, sira_anahtar, baslik_metni, baslik_emoji, bolum_kodu):
    st.markdown(f"**{baslik_emoji} {baslik_metni}**")
    hedef_dosyalar = [d for d in kayitlar if d.get(filtre_anahtar, False)]
    hedef_dosyalar = sorted(hedef_dosyalar, key=lambda x: x.get(sira_anahtar, 9999))
    
    with st.container(height=260):
        if hedef_dosyalar:
            for idx, dosya in enumerate(hedef_dosyalar):
                d_no = dosya.get("Dosya No", "")
                firma = dosya.get("Firma", "-")
                
                c_txt, c_up, c_down = st.columns([72, 14, 14], vertical_alignment="center")
                with c_txt:
                    st.markdown(f"<small><b>{idx + 1}.</b> <code>{d_no}</code> | {firma[:12]}</small>", unsafe_allow_html=True)
                
                with c_up:
                    if st.button("▲", key=f"btn_up_{bolum_kodu}_{d_no}_{idx}", help="Yukarı Taş"):
                        if idx > 0:
                            ust_dosya = hedef_dosyalar[idx - 1]
                            curr_sira = dosya.get(sira_anahtar, idx)
                            ust_sira = ust_dosya.get(sira_anahtar, idx - 1)
                            dosya[sira_anahtar] = ust_sira if ust_sira != curr_sira else idx - 1
                            ust_dosya[sira_anahtar] = curr_sira if ust_sira != curr_sira else idx
                        else:
                            dosya[sira_anahtar] = -1
                            
                        for i_s, d_s in enumerate(sorted(hedef_dosyalar, key=lambda x: x.get(sira_anahtar, 9999))):
                            d_s[sira_anahtar] = i_s
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} {bolum_kodu} yukarı")
                        st.rerun()

                with c_down:
                    if st.button("▼", key=f"btn_dn_{bolum_kodu}_{d_no}_{idx}", help="Aşağı Taş"):
                        if idx < len(hedef_dosyalar) - 1:
                            alt_dosya = hedef_dosyalar[idx + 1]
                            curr_sira = dosya.get(sira_anahtar, idx)
                            alt_sira = alt_dosya.get(sira_anahtar, idx + 1)
                            dosya[sira_anahtar] = alt_sira if alt_sira != curr_sira else idx + 1
                            alt_dosya[sira_anahtar] = curr_sira if alt_sira != curr_sira else idx
                            
                        for i_s, d_s in enumerate(sorted(hedef_dosyalar, key=lambda x: x.get(sira_anahtar, 9999))):
                            d_s[sira_anahtar] = i_s
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} {bolum_kodu} aşağı")
                        st.rerun()
        else:
            st.caption("*Kayıt yok.*")

# 10 Sütun için Eşit Genişlik Yapılandırması
top_cols = st.columns(len(mevcut_bolum_sirasi))

for col_idx, bolum_kodu in enumerate(mevcut_bolum_sirasi):
    target_col = top_cols[col_idx]
    
    with target_col:
        # Sola/Sağa Taşıma Butonları
        c_head_left, c_head_right = st.columns([1, 1])
        with c_head_left:
            if col_idx > 0:
                if st.button("◀", key=f"btn_m_left_{bolum_kodu}", help="Bölümü Sola Kaydır"):
                    bolum_sol_sag_kaydir(bolum_kodu, "sol")
        with c_head_right:
            if col_idx < len(mevcut_bolum_sirasi) - 1:
                if st.button("▶", key=f"btn_m_right_{bolum_kodu}", help="Bölümü Sağa Kaydır"):
                    bolum_sol_sag_kaydir(bolum_kodu, "sag")

        # DURUM BAYRAKLARI (8 ADET LİSTE)
        if bolum_kodu == "kapatma":
            liste_siralama_render("KapatmaAsamasinda", "SiraNo", "Kapatmada", "🏁", bolum_kodu)
        elif bolum_kodu == "incelenmedi":
            liste_siralama_render("Incelenmedi", "IncelenmediSiraNo", "İncelenmedi", "🔍", bolum_kodu)
        elif bolum_kodu == "incelemede":
            liste_siralama_render("Incelemede", "IncelemedeSiraNo", "İncelemede", "🧐", bolum_kodu)
        elif bolum_kodu == "bagli":
            liste_siralama_render("BagliDosya", "BagliSiraNo", "Bağlı", "🔗", bolum_kodu)
        elif bolum_kodu == "kapatma_red":
            liste_siralama_render("KapatmaRed", "KapatmaRedSiraNo", "Red", "🚫", bolum_kodu)
        elif bolum_kodu == "tescilde":
            liste_siralama_render("TescildeBekleyen", "TescildeSiraNo", "Tescilde", "⏳", bolum_kodu)
        elif bolum_kodu == "yazi_cevabi":
            liste_siralama_render("YaziCevabiBekleyen", "YaziCevabiSiraNo", "Yazı Cevabı", "✉️", bolum_kodu)
        elif bolum_kodu == "mail_atildi":
            liste_siralama_render("MailAtildi", "MailAtildiSiraNo", "Mail Atıldı", "📧", bolum_kodu)

        # ÖNEMLİ NOTLAR
        elif bolum_kodu == "notlar":
            st.markdown("**📌 Önemli Notlar**")
            with st.form(key="form_yeni_not_ekle", clear_on_submit=True):
                yeni_not_metni = st.text_input("Yeni Not", placeholder="Not...", label_visibility="collapsed")
                submit_not = st.form_submit_button("➕ Ekle", use_container_width=True)
                    
                if submit_not:
                    if yeni_not_metni.strip() != "":
                        mevcut_onemli_notlar.append(yeni_not_metni.strip())
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Yeni önemli not eklendi")
                        st.toast("✅ Not eklendi!")
                        st.rerun()

            with st.container(height=180):
                if mevcut_onemli_notlar:
                    for n_idx, not_item in enumerate(mevcut_onemli_notlar):
                        c_not_text, c_not_del = st.columns([75, 25], vertical_alignment="center")
                        with c_not_text:
                            st.caption(f"📌 {not_item}")
                        with c_not_del:
                            if st.button("🗑️", key=f"btn_del_not_{n_idx}", help="Bu notu sil"):
                                mevcut_onemli_notlar.pop(n_idx)
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Önemli not silindi")
                                st.rerun()
                else:
                    st.caption("*Not yok.*")

        # HATIRLATMALAR
        elif bolum_kodu == "hatirlatma":
            saat_str = simdi_dt.strftime("%d.%m | %H:%M")
            st.markdown(f"**⏰ Hatırlatma** <small>({saat_str})</small>", unsafe_allow_html=True)

            with st.form(key="form_yeni_hatirlatma_ekle", clear_on_submit=True):
                h_metin = st.text_input("Hatırlatma Metni", placeholder="Hatırlatma...", label_visibility="collapsed")
                h_tarih = st.date_input("Tarih", value=simdi_dt.date(), label_visibility="collapsed")
                h_saat = st.time_input("Saat", value=simdi_dt.time(), label_visibility="collapsed")
                    
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

            with st.container(height=140):
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

                        c_h_text, c_h_action = st.columns([70, 30], vertical_alignment="center")

                        with c_h_text:
                            if zaman_geldi:
                                st.markdown(f"<div class='red-reminder-box'>🔔 {h_metin_val}</div>", unsafe_allow_html=True)
                            else:
                                if h_tamamlandi:
                                    st.caption(f"✅ ~~{h_metin_val}~~")
                                else:
                                    st.caption(f"⏰ {h_metin_val}")

                        with c_h_action:
                            if zaman_geldi:
                                if st.button("OK", key=f"btn_ok_h_{h_idx}", type="primary"):
                                    h_item["Tamamlandi"] = True
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma tamamlandı")
                                    st.rerun()
                            else:
                                if st.button("🗑️", key=f"del_h_{h_idx}", help="Sil"):
                                    mevcut_hatirlatmalar.pop(h_idx)
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, "Hatırlatma silindi")
                                    st.rerun()
                else:
                    st.caption("*Hatırlatma yok.*")

st.markdown("---")

# EKRAN YAPILANDIRMASI: Sol Taraf %60, Sağ Taraf %40
col_left, col_right = st.columns([60, 40], gap="large")

# ==============================================================================
# SOL TARAF: GENİŞ DOSYA LİSTESİ VE GEÇMİŞ İŞLEMLER
# ==============================================================================
with col_left:
    st.subheader("📋 Kayıtlı Dosyalar ve İşlem Akışı")
    
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
                        c_s_evet, c_s_hayir = st.columns(2)
                        with c_s_evet:
                            if st.button("Evet", key=f"confirm_yes_{d_no}_{d_idx}"):
                                kayitlar = [k for k in kayitlar if k.get("Dosya No") != d_no]
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} dosyası silindi")
                                st.session_state[confirm_del_key] = False
                                st.toast("Dosya silindi!")
                                st.rerun()
                        with c_s_hayir:
                            if st.button("Hayır", key=f"confirm_no_{d_no}_{d_idx}"):
                                st.session_state[confirm_del_key] = False
                                st.rerun()

                with exp_container:
                    st.markdown("<div class='save-status-container'>", unsafe_allow_html=True)
                    st.write("**📌 Dosya Durum Bayrakları:**")
                    c_chk1, c_chk2, c_chk3, c_chk4 = st.columns(4)
                    with c_chk1:
                        new_bagli = st.checkbox("🔗 Bağlı Dosya", value=bagli_durumu, key=f"chk_bagli_{d_no}_{d_idx}")
                        new_kapatma_red = st.checkbox("🚫 Red", value=kapatma_red_durumu, key=f"chk_kred_{d_no}_{d_idx}")
                    with c_chk2:
                        new_tescilde = st.checkbox("⏳ Tescilde", value=tescilde_durumu, key=f"chk_tescil_{d_no}_{d_idx}")
                        new_kapatma_asamasinda = st.checkbox("🏁 Kapatmada", value=kapatma_asamasinda_durumu, key=f"chk_kasama_{d_no}_{d_idx}")
                    with c_chk3:
                        new_yazi_cevabi = st.checkbox("✉️ Yazı Cevabı", value=yazi_cevabi_durumu, key=f"chk_yazi_{d_no}_{d_idx}")
                        new_incelenmedi = st.checkbox("🔍 İncelenmedi", value=incelenmedi_durumu, key=f"chk_incmed_{d_no}_{d_idx}")
                    with c_chk4:
                        new_incelemede = st.checkbox("🧐 İncelemede", value=incelemede_durumu, key=f"chk_incmde_{d_no}_{d_idx}")
                        new_mail_atildi = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"chk_mail_{d_no}_{d_idx}")

                    if st.button("💾 Durumu Kaydet", key=f"btn_save_status_{d_no}_{d_idx}"):
                        dosya["BagliDosya"] = new_bagli
                        dosya["KapatmaRed"] = new_kapatma_red
                        dosya["TescildeBekleyen"] = new_tescilde
                        dosya["KapatmaAsamasinda"] = new_kapatma_asamasinda
                        dosya["YaziCevabiBekleyen"] = new_yazi_cevabi
                        dosya["Incelenmedi"] = new_incelenmedi
                        dosya["Incelemede"] = new_incelemede
                        dosya["MailAtildi"] = new_mail_atildi
                        
                        if new_mail_atildi and not mail_atildi_durumu:
                            dosya["MailTarihi"] = simdi_dt.strftime("%d.%m.%Y")
                        elif not new_mail_atildi:
                            dosya["MailTarihi"] = ""
                            
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} durumları güncellendi")
                        st.toast("✅ Durumlar güncellendi!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")

                    st.write("**📝 Genel Açıklama:**")
                    if not st.session_state[edit_key]:
                        st.info(ana_aciklama if ana_aciklama else "*Henüz açıklama girilmedi.*")
                        if st.button("✏️ Açıklamayı Düzenle", key=f"btn_edit_aciklama_{d_no}_{d_idx}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    else:
                        yeni_aciklama_val = st.text_area("Açıklama Metni", value=ana_aciklama, key=f"txt_aciklama_{d_no}_{d_idx}")
                        c_sav, c_cncl = st.columns([1, 1])
                        with c_sav:
                            if st.button("💾 Kaydet", key=f"btn_save_aciklama_{d_no}_{d_idx}", type="primary"):
                                dosya["Aciklama"] = yeni_aciklama_val.strip()
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} açıklaması güncellendi")
                                st.session_state[edit_key] = False
                                st.toast("Açıklama kaydedildi!")
                                st.rerun()
                        with c_cncl:
                            if st.button("❌ İptal", key=f"btn_cancel_aciklama_{d_no}_{d_idx}"):
                                st.session_state[edit_key] = False
                                st.rerun()

                    st.markdown("---")
                    
                    st.write("**📜 İşlem Geçmişi:**")
                    if islemler:
                        for idx_isl, isl in enumerate(islemler):
                            tarih = isl.get("Tarih", "")
                            metin = isl.get("Metin", "")
                            c_t, c_m, c_d = st.columns([25, 65, 10])
                            with c_t: st.caption(f"🗓️ {tarih}")
                            with c_m: st.write(metin)
                            with c_d:
                                if st.button("🗑️", key=f"del_isl_{d_no}_{d_idx}_{idx_isl}", help="İşlemi Sil"):
                                    islemler.pop(idx_isl)
                                    verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} işlemi silindi")
                                    st.toast("İşlem silindi!")
                                    st.rerun()
                    else:
                        st.caption("*Henüz işlem kaydı yok.*")

                    with st.form(key=f"form_islem_ekle_{d_no}_{d_idx}", clear_on_submit=True):
                        yeni_islem_metni = st.text_input("Yeni İşlem Ekle", placeholder="İşlem detayı...")
                        sub_isl = st.form_submit_button("➕ İşlemi Kaydet")
                        if sub_isl:
                            if yeni_islem_metni.strip():
                                simdi_str = simdi_dt.strftime("%d.%m.%Y %H:%M")
                                islemler.append({"Tarih": simdi_str, "Metin": yeni_islem_metni.strip()})
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} yeni işlem eklendi")
                                st.toast("Yeni işlem eklendi!")
                                st.rerun()
                            else:
                                st.warning("İşlem metni boş olamaz.")
        else:
            st.warning("Aramanıza uygun dosya bulunamadı.")
    else:
        st.info("Sistemde henüz kayıtlı dosya bulunmuyor.")

# ==============================================================================
# SAĞ TARAF: YENİ DOSYA EKLEME VE YEDEK İŞLEMLERİ
# ==============================================================================
with col_right:
    st.subheader("➕ Yeni Dosya Ekle / Yedek İşlemleri")
    
    tab1, tab2 = st.tabs(["📝 Tekli Dosya Ekle", "📊 Yedek İşlemleri (Excel)"])
    
    with tab1:
        with st.form(key="form_tekli_dosya", clear_on_submit=True):
            tek_dno = st.text_input("Dosya No *", placeholder="Örn: 2025 D1 5400")
            tek_firma = st.text_input("Firma Adı", placeholder="Örn: ABC Lojistik")
            tek_aciklama = st.text_area("Açıklama", placeholder="Dosya açıklaması...")
            
            sub_tekli = st.form_submit_button("💾 Dosyayı Kaydet", use_container_width=True, type="primary")
            
            if sub_tekli:
                if tek_dno.strip():
                    mevcut_var_mi = any(d.get("Dosya No") == tek_dno.strip() for d in kayitlar)
                    if mevcut_var_mi:
                        st.error(f"`{tek_dno.strip()}` numaralı dosya zaten sistemde mevcut!")
                    else:
                        yeni_dosya_obj = {
                            "Dosya No": tek_dno.strip(),
                            "Firma": tek_firma.strip() if tek_firma.strip() else "-",
                            "Aciklama": tek_aciklama.strip(),
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
                            "SiraNo": 9999,
                            "IncelenmediSiraNo": 9999,
                            "IncelemedeSiraNo": 9999,
                            "BagliSiraNo": 9999,
                            "KapatmaRedSiraNo": 9999,
                            "TescildeSiraNo": 9999,
                            "YaziCevabiSiraNo": 9999,
                            "MailAtildiSiraNo": 9999
                        }
                        kayitlar.append(yeni_dosya_obj)
                        verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"Tekli dosya eklendi: {tek_dno}")
                        st.success(f"`{tek_dno}` başarıyla eklendi!")
                        st.rerun()
                else:
                    st.warning("Lütfen Dosya No alanını doldurun.")

    with tab2:
        st.markdown("### 📥 1. Tam Sistem Yedeğini İndir")
        st.caption("Sitedeki tüm dosyaları, önemli notları, hatırlatmaları ve bölüm sıralamasını kapsayan tam Excel yedeğini indirir.")
        
        export_b_list = []
        for d in kayitlar:
            islem_gecmisi_str = " | ".join([f"[{i.get('Tarih', '')}] {i.get('Metin', '')}" for i in d.get("Islemler", [])])
            
            export_b_list.append({
                "Dosya No": d.get("Dosya No", ""),
                "Firma": d.get("Firma", "-"),
                "Açıklama": d.get("Aciklama", ""),
                "Oluşturma Tarihi": d.get("OlusturmaTarihi", ""),
                "İşlem Geçmişi": islem_gecmisi_str,
                "Bağlı Dosya": "EVET" if d.get("BagliDosya") else "HAYIR",
                "Kapatma Red": "EVET" if d.get("KapatmaRed") else "HAYIR",
                "Tescilde Bekleyen": "EVET" if d.get("TescildeBekleyen") else "HAYIR",
                "Kapatma Aşamasında": "EVET" if d.get("KapatmaAsamasinda") else "HAYIR",
                "Yazı Cevabı Bekleyen": "EVET" if d.get("YaziCevabiBekleyen") else "HAYIR",
                "İncelenmedi": "EVET" if d.get("Incelenmedi") else "HAYIR",
                "İncelemede": "EVET" if d.get("Incelemede") else "HAYIR",
                "Mail Atıldı": "EVET" if d.get("MailAtildi") else "HAYIR",
                "Mail Tarihi": d.get("MailTarihi", ""),
                "Sıra No": d.get("SiraNo", 9999),
                "İncelenmedi Sıra No": d.get("IncelenmediSiraNo", 9999),
                "İncelemede Sıra No": d.get("IncelemedeSiraNo", 9999),
                "Bağlı Sıra No": d.get("BagliSiraNo", 9999),
                "Kapatma Red Sıra No": d.get("KapatmaRedSiraNo", 9999),
                "Tescilde Sıra No": d.get("TescildeSiraNo", 9999),
                "Yazı Cevabı Sıra No": d.get("YaziCevabiSiraNo", 9999),
                "Mail Atıldı Sıra No": d.get("MailAtildiSiraNo", 9999)
            })
        df_dosyalar = pd.DataFrame(export_b_list)
        df_notlar = pd.DataFrame([{"Not": n} for n in mevcut_onemli_notlar])
        df_hatirlatmalar = pd.DataFrame([
            {
                "Hatırlatma Metni": h.get("Metin", ""),
                "Zaman": h.get("Zaman", ""),
                "Tamamlandı": "EVET" if h.get("Tamamlandi") else "HAYIR"
            } for h in mevcut_hatirlatmalar
        ])
        df_ayarlar = pd.DataFrame([{"Bölüm Sırası": ",".join(mevcut_bolum_sirasi)}])
        
        out_b = io.BytesIO()
        with pd.ExcelWriter(out_b, engine='xlsxwriter') as writer:
            df_dosyalar.to_excel(writer, index=False, sheet_name='Sistem_Yedegi')
            df_notlar.to_excel(writer, index=False, sheet_name='Onemli_Notlar')
            df_hatirlatmalar.to_excel(writer, index=False, sheet_name='Hatirlatmalar')
            df_ayarlar.to_excel(writer, index=False, sheet_name='Sistem_Ayarlari')
            
        excel_b_data = out_b.getvalue()
        
        st.download_button(
            label="📥 Tam Sistem Yedeğini İndir (.xlsx)",
            data=excel_b_data,
            file_name=f"tam_sistem_yedegi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown("---")
        
        st.markdown("### 📤 2. Excel Yedeğini Geri Yükle")
        st.caption("Daha önce indirdiğiniz tam sistem Excel yedeğini seçerek siteyi o haline geri getirebilirsiniz.")
        
        uploaded_file = st.file_uploader("Yedek Excel Dosyası Seçin (.xlsx)", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            try:
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names
                
                df_std = pd.read_excel(excel_file, sheet_name='Sistem_Yedegi') if 'Sistem_Yedegi' in sheet_names else pd.read_excel(excel_file, sheet_name=sheet_names[0])
                st.write("**📄 Dosyalar Önizleme:**")
                st.dataframe(df_std.head(3), use_container_width=True)
                
                if st.button("🚀 Excel Yedeğini Sisteme Yükle", type="primary", use_container_width=True):
                    eklenen, guncellenen = 0, 0
                    
                    dno_col = next((c for c in df_std.columns if "dosya" in str(c).lower()), df_std.columns[0])
                    firma_col = next((c for c in df_std.columns if "firma" in str(c).lower()), None)
                    ack_col = next((c for c in df_std.columns if "açıklama" in str(c).lower() or "aciklama" in str(c).lower()), None)
                    islem_col = next((c for c in df_std.columns if "işlem" in str(c).lower() or "islem" in str(c).lower()), None)
                    olusturma_col = next((c for c in df_std.columns if "oluşturma" in str(c).lower() or "olusturma" in str(c).lower()), None)
                    mail_tarihi_col = next((c for c in df_std.columns if "mail tarihi" in str(c).lower()), None)

                    def parse_bool(col_kw, r):
                        col_name = next((c for c in df_std.columns if col_kw in str(c).lower()), None)
                        if col_name and pd.notna(r[col_name]):
                            val = str(r[col_name]).strip().upper()
                            return val in ["EVET", "TRUE", "1", "YES"]
                        return False

                    def parse_int(col_kw, r, default_val=9999):
                        col_name = next((c for c in df_std.columns if col_kw in str(c).lower()), None)
                        if col_name and pd.notna(r[col_name]):
                            try:
                                return int(r[col_name])
                            except Exception:
                                return default_val
                        return default_val

                    for _, row in df_std.iterrows():
                        d_no = str(row[dno_col]).strip()
                        if not d_no or d_no.lower() == "nan":
                            continue
                            
                        firma_val = str(row[firma_col]).strip() if firma_col and pd.notna(row[firma_col]) else "-"
                        aciklama_val = str(row[ack_col]).strip() if ack_col and pd.notna(row[ack_col]) else ""
                        olusturma_val = str(row[olusturma_col]).strip() if olusturma_col and pd.notna(row[olusturma_col]) else simdi_dt.strftime("%Y-%m-%d %H:%M:%S")
                        mail_tarihi_val = str(row[mail_tarihi_col]).strip() if mail_tarihi_col and pd.notna(row[mail_tarihi_col]) else ""

                        islemler_listesi = []
                        if islem_col and pd.notna(row[islem_col]):
                            raw_islem_str = str(row[islem_col]).strip()
                            if raw_islem_str:
                                parcalar = raw_islem_str.split(" | ")
                                for p in parcalar:
                                    p = p.strip()
                                    if p.startswith("[") and "]" in p:
                                        t_part = p[1:p.index("]")]
                                        m_part = p[p.index("]")+1:].strip()
                                        islemler_listesi.append({"Tarih": t_part, "Metin": m_part})
                                    elif p:
                                        islemler_listesi.append({"Tarih": simdi_dt.strftime("%d.%m.%Y %H:%M"), "Metin": p})

                        bulunan_dosya = next((d for d in kayitlar if d.get("Dosya No") == d_no), None)
                        
                        if bulunan_dosya:
                            bulunan_dosya['Aciklama'] = aciklama_val
                            if firma_val != "-": bulunan_dosya['Firma'] = firma_val
                            if islemler_listesi: bulunan_dosya['Islemler'] = islemler_listesi
                            
                            bulunan_dosya['BagliDosya'] = parse_bool("bağlı", row)
                            bulunan_dosya['KapatmaRed'] = parse_bool("red", row)
                            bulunan_dosya['TescildeBekleyen'] = parse_bool("tescilde", row)
                            bulunan_dosya['KapatmaAsamasinda'] = parse_bool("kapatma", row)
                            bulunan_dosya['YaziCevabiBekleyen'] = parse_bool("yazı", row)
                            bulunan_dosya['Incelenmedi'] = parse_bool("incelenmedi", row)
                            bulunan_dosya['Incelemede'] = parse_bool("incelemede", row)
                            bulunan_dosya['MailAtildi'] = parse_bool("mail", row)
                            bulunan_dosya['MailTarihi'] = mail_tarihi_val
                            
                            bulunan_dosya['SiraNo'] = parse_int("sıra no", row)
                            bulunan_dosya['IncelenmediSiraNo'] = parse_int("incelenmedi sıra", row)
                            bulunan_dosya['IncelemedeSiraNo'] = parse_int("incelemede sıra", row)
                            bulunan_dosya['BagliSiraNo'] = parse_int("bağlı sıra", row)
                            bulunan_dosya['KapatmaRedSiraNo'] = parse_int("red sıra", row)
                            bulunan_dosya['TescildeSiraNo'] = parse_int("tescilde sıra", row)
                            bulunan_dosya['YaziCevabiSiraNo'] = parse_int("yazı cevap sıra", row)
                            bulunan_dosya['MailAtildiSiraNo'] = parse_int("mail atıldı sıra", row)
                            
                            guncellenen += 1
                        else:
                            yeni_d = {
                                "Dosya No": d_no,
                                "Firma": firma_val,
                                "Aciklama": aciklama_val,
                                "OlusturmaTarihi": olusturma_val,
                                "Islemler": islemler_listesi,
                                "BagliDosya": parse_bool("bağlı", row),
                                "KapatmaRed": parse_bool("red", row),
                                "TescildeBekleyen": parse_bool("tescilde", row),
                                "KapatmaAsamasinda": parse_bool("kapatma", row),
                                "YaziCevabiBekleyen": parse_bool("yazı", row),
                                "Incelenmedi": parse_bool("incelenmedi", row),
                                "Incelemede": parse_bool("incelemede", row),
                                "MailAtildi": parse_bool("mail", row),
                                "MailTarihi": mail_tarihi_val,
                                "SiraNo": parse_int("sıra no", row),
                                "IncelenmediSiraNo": parse_int("incelenmedi sıra", row),
                                "IncelemedeSiraNo": parse_int("incelemede sıra", row),
                                "BagliSiraNo": parse_int("bağlı sıra", row),
                                "KapatmaRedSiraNo": parse_int("red sıra", row),
                                "TescildeSiraNo": parse_int("tescilde sıra", row),
                                "YaziCevabiSiraNo": parse_int("yazı cevap sıra", row),
                                "MailAtildiSiraNo": parse_int("mail atıldı sıra", row)
                            }
                            kayitlar.append(yeni_d)
                            eklenen += 1
                    
                    yeni_notlar = mevcut_onemli_notlar
                    if 'Onemli_Notlar' in sheet_names:
                        df_not_file = pd.read_excel(excel_file, sheet_name='Onemli_Notlar')
                        if not df_not_file.empty:
                            col_n = df_not_file.columns[0]
                            yeni_notlar = [str(x).strip() for x in df_not_file[col_n].dropna().tolist() if str(x).strip()]

                    yeni_hatirlatmalar = mevcut_hatirlatmalar
                    if 'Hatirlatmalar' in sheet_names:
                        df_h_file = pd.read_excel(excel_file, sheet_name='Hatirlatmalar')
                        if not df_h_file.empty:
                            yeni_hatirlatmalar = []
                            for _, h_row in df_h_file.iterrows():
                                h_m = str(h_row.get("Hatırlatma Metni", "")).strip()
                                h_z = str(h_row.get("Zaman", "")).strip()
                                h_t_str = str(h_row.get("Tamamlandı", "")).strip().upper()
                                if h_m and h_m != "nan":
                                    yeni_hatirlatmalar.append({
                                        "Metin": h_m,
                                        "Zaman": h_z if h_z != "nan" else "",
                                        "Tamamlandi": h_t_str in ["EVET", "TRUE", "1", "YES"]
                                    })

                    yeni_bolum_sirasi = mevcut_bolum_sirasi
                    if 'Sistem_Ayarlari' in sheet_names:
                        df_sys_file = pd.read_excel(excel_file, sheet_name='Sistem_Ayarlari')
                        if not df_sys_file.empty and "Bölüm Sırası" in df_sys_file.columns:
                            raw_sira = str(df_sys_file["Bölüm Sırası"].iloc[0]).strip()
                            if raw_sira and raw_sira != "nan":
                                parsed_sira = [b.strip() for b in raw_sira.split(",") if b.strip()]
                                if parsed_sira:
                                    yeni_bolum_sirasi = parsed_sira

                    verileri_kaydet(kayitlar, yeni_notlar, yeni_hatirlatmalar, yeni_bolum_sirasi, f"Tam Yedek Yükleme: {eklenen} eklendi, {guncellenen} güncellendi.")
                    st.success(f"🎉 Tam Yükleme Tamamlandı!")
                    st.rerun()

            except Exception as e:
                st.error(f"Excel okunurken bir hata oluştu: {e}")
