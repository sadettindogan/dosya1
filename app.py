import streamlit as st
import pandas as pd
import json
import os

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Dosya Takip & Ön İnceleme Portalı",
    page_icon="📂",
    layout="wide"
)

# --- VERİ YÜKLEME VE SAKLAMA MANTIKLARI ---
DATA_FILE = "veriler.json"

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def verileri_kaydet(veri_listesi):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(veri_listesi, f, ensure_ascii=False, indent=4)

# Oturum Durumu (Session State) Başlatma
if "veriler" not in st.session_state:
    st.session_state.veriler = verileri_yukle()

# --- BAŞLIK VE GENEL BİLGİ ---
st.title("📂 Dosya Takip & İşlem Portalı")
st.markdown("---")

# --- DOSYA BAŞLIĞI VE ÖN İNCELEME MODÜLÜ ---
st.header("📁 Dosya")

with st.expander("🔍 Ön İnceleme", expanded=True):
    st.write("Lütfen dosya evraklarının kontrol durumunu işaretleyiniz:")
    st.write("")
    
    # 1. Ekspertiz Şartı
    col1, col2 = st.columns([1, 2])
    with col1:
        ekspertiz = st.checkbox("Ekspertiz Şartı", key="chk_ekspertiz")
    with col2:
        if ekspertiz:
            st.success("✅ Kontrol Edildi")
        else:
            st.warning("⏳ Kontrol Edilmedi")

    # 2. 233 Nolu Özel Şart
    col1, col2 = st.columns([1, 2])
    with col1:
        ozel_sart = st.checkbox("233 Nolu Özel Şart", key="chk_ozel_sart")
    with col2:
        if ozel_sart:
            st.success("✅ Kontrol Edildi")
        else:
            st.warning("⏳ Kontrol Edilmedi")

    # 3. YMM Raporu
    col1, col2 = st.columns([1, 2])
    with col1:
        ymm = st.checkbox("YMM Raporu", key="chk_ymm")
    with col2:
        if ymm:
            st.success("✅ Kontrol Edildi")
        else:
            st.warning("⏳ Kontrol Edilmedi")

    # 4. XML Dosyası
    col1, col2 = st.columns([1, 2])
    with col1:
        xml_dosya = st.checkbox("XML Dosyası", key="chk_xml")
    with col2:
        if xml_dosya:
            st.success("✅ Kontrol Edildi")
        else:
            st.warning("⏳ Kontrol Edilmedi")

st.markdown("---")

# --- SAĞ / YAN PANEL (MANUEL EKLEME VE EXCEL) ---
st.sidebar.header("🛠️ İşlem Paneli")

# Manuel Dosya Ekleme Formu
with st.sidebar.expander("➕ Manuel Dosya Ekle", expanded=False):
    with st.form("yeni_dosya_formu", clear_on_submit=True):
        dosya_no = st.text_input("Dosya No")
        firma_adi = st.text_input("Firma Adı")
        aciklama = st.text_area("Açıklama")
        
        btn_kaydet = st.form_submit_button("Dosyayı Kaydet")
        
        if btn_kaydet:
            if dosya_no and firma_adi:
                yeni_kayit = {
                    "dosya_no": dosya_no,
                    "firma_adi": firma_adi,
                    "aciklama": aciklama,
                    "ekspertiz": "Evet" if st.session_state.get("chk_ekspertiz") else "Hayır",
                    "ozel_sart": "Evet" if st.session_state.get("chk_ozel_sart") else "Hayır",
                    "ymm": "Evet" if st.session_state.get("chk_ymm") else "Hayır",
                    "xml": "Evet" if st.session_state.get("chk_xml") else "Hayır"
                }
                st.session_state.veriler.append(yeni_kayit)
                verileri_kaydet(st.session_state.veriler)
                st.sidebar.success(f"'{dosya_no}' numaralı dosya başarıyla kaydedildi!")
            else:
                st.sidebar.error("Lütfen Dosya No ve Firma Adı alanlarını doldurun.")

# Excel / JSON Aktarım ve İndirme
with st.sidebar.expander("📊 Excel ve Veri Aktarımı", expanded=False):
    if st.session_state.veriler:
        df = pd.DataFrame(st.session_state.veriler)
        
        # Excel İndirme Butonu
        excel_veri = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Verileri CSV/Excel Olarak İndir",
            data=excel_veri,
            file_name="dosya_listesi.csv",
            mime="text/csv"
        )
    else:
        st.info("İndirilecek veri bulunmuyor.")

# --- ANA EKRAN VERİ LİSTELEME ---
st.subheader("📋 Kayıtlı Dosya Listesi")

if st.session_state.veriler:
    df_liste = pd.DataFrame(st.session_state.veriler)
    st.dataframe(df_liste, use_container_width=True)
else:
    st.info("Henüz kayıtlı bir dosya bulunmamaktadır. Yan panelden yeni kayıt ekleyebilirsiniz.")
