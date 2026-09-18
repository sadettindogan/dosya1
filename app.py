import datetime
import json
import os
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. SAYFA YAPILANDIRMASI VE BAŞLIK
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dosya & Takip Yönetim Sistemi",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Dosya & Takip Yönetim Sistemi")

VERI_DOSYASI = "veriler.json"

# -----------------------------------------------------------------------------
# 2. VERİ YÜKLEME VE KAYDETME FONKSİYONLARI
# -----------------------------------------------------------------------------
def verileri_yukle():
    """veriler.json dosyasından verileri okur."""
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Veri okunurken hata oluştu: {e}")
            return []
    return []

def verileri_kaydet(veriler):
    """Verileri veriler.json dosyasına kaydeder."""
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

# Uygulama başında mevcut verileri yükleyelim
mevcut_veriler = verileri_yukle()

# -----------------------------------------------------------------------------
# 3. SEKMELER (TABS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📋 Dosya Listesi & Arama", "➕ Yeni Kayıt Ekleme", "📤 Toplu Veri Güncelle / Yükle"])

# -----------------------------------------------------------------------------
# TAB 1: DOSYA LİSTESİ VE ARAMA
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("📋 Kayıtlı Dosyalar")
    
    if mevcut_veriler:
        df = pd.DataFrame(mevcut_veriler)
        
        # Arama Filtresi
        arama_metni = st.text_input("🔍 Dosya Adı / No ile Arama Yapın", "")
        if arama_metni:
            # Tüm sütunlarda arama yap
            mask = df.astype(str).apply(lambda row: row.str.contains(arama_metni, case=False, na=False)).any(axis=1)
            df = df[mask]
            
        st.dataframe(df, use_container_width=True)
        st.caption(f"Toplam Gösterilen Kayıt: {len(df)}")
    else:
        st.info("Henüz kayıtlı bir veri bulunamadı.")

# -----------------------------------------------------------------------------
# TAB 2: YENİ TEKİL KAYIT EKLENMESİ
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("➕ Yeni Dosya Kaydı")
    
    with st.form("yeni_kayit_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            dosya_adi = st.text_input("Dosya Adı / No *")
            musteri_unvan = st.text_input("Müşteri / Firma Ünvanı")
            islem_turu = st.selectbox("İşlem Türü", ["Tescil", "Yazı Cevabı", "Kapatma", "Diğer"])
            
        with col2:
            durum = st.selectbox("Durumu", [
                "Tescilde Bekleyen", 
                "Kapatma Aşamasında", 
                "Yazı Cevabı Bekleyen", 
                "Tamamlandı", 
                "İptal Edildi"
            ])
            tarih = st.date_input("Kayıt / İşlem Tarihi", datetime.date.today())
            aciklama = st.text_area("Açıklama / Notlar")
            
        kaydet_btn = st.form_submit_button("💾 Kaydı Oluştur")
        
        if kaydet_btn:
            if not dosya_adi.strip():
                st.error("Lütfen Dosya Adı / No alanını doldurun!")
            else:
                yeni_kayit = {
                    "Dosya Adı": dosya_adi.strip(),
                    "Müşteri Ünvanı": musteri_unvan.strip(),
                    "İşlem Türü": islem_turu,
                    "Durum": durum,
                    "Tarih": str(tarih),
                    "Açıklama": aciklama.strip()
                }
                
                mevcut_veriler.append(yeni_kayit)
                verileri_kaydet(mevcut_veriler)
                st.success(f"'{dosya_adi}' başarıyla kaydedildi!")
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 3: TOPLU VERİ GÜNCELLE / YÜKLE (GÜNCELLENEN MANTIK)
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("📤 Toplu Veri Güncelle / Geri Yükle")
    st.markdown("""
    * **Excel (.xlsx) Yükleme:** Excel dosyanızdaki **'Dosya Adı'** veya **'Dosya No'** sütununa göre sistemdeki eşleşen kayıt bulunur ve **sadece ilgili dosya güncellenir**. Diğer verilerinize dokunulmaz. Sistemde yoksa yeni dosya olarak eklenir.
    * **JSON (.json) Yükleme:** Dosyadaki tüm yedek veriyi tam olarak geri yükler.
    """)
    
    uploaded_file = st.file_uploader("Excel (.xlsx) veya JSON (.json) Yükle", type=["xlsx", "json"])
    
    if uploaded_file is not None:
        # ---------------------------------------------------------------------
        # 1. EXCEL YÜKLENDİĞİNDE: TEKİL / KISMİ GÜNCELLEME MANTIĞI
        # ---------------------------------------------------------------------
        if uploaded_file.name.endswith(".xlsx"):
            try:
                df_excel = pd.read_excel(uploaded_file)
                df_excel = df_excel.fillna("") # Boş Hücreleri temizle
                
                guncellenen_sayi = 0
                eklenen_sayi = 0
                
                for _, row in df_excel.iterrows():
                    excel_kayit = row.to_dict()
                    
                    # Eşleştirme anahtarı: 'Dosya Adı' veya 'Dosya No'
                    dosya_anahtari = (
                        excel_kayit.get("Dosya Adı") or 
                        excel_kayit.get("Dosya No") or 
                        excel_kayit.get("Dosya_Adi")
                    )
                    
                    if not dosya_anahtari:
                        continue
                        
                    bulundu = False
                    # Mevcut verilerde arama yap
                    for mevcut_kayit in mevcut_veriler:
                        mevcut_anahtar = (
                            mevcut_kayit.get("Dosya Adı") or 
                            mevcut_kayit.get("Dosya No") or 
                            mevcut_kayit.get("Dosya_Adi")
                        )
                        
                        if mevcut_anahtar and str(mevcut_anahtar).strip().lower() == str(dosya_anahtari).strip().lower():
                            # Eşleşme bulundu: Yalnızca Excel'deki verilerle güncelle
                            mevcut_kayit.update(excel_kayit)
                            guncellenen_sayi += 1
                            bulundu = True
                            break
                    
                    # Eşleşen dosya yoksa yeni kayıt olarak ekle
                    if not bulundu:
                        mevcut_veriler.append(excel_kayit)
                        eklenen_sayi += 1
                
                # Güncel veriyi kaydet
                verileri_kaydet(mevcut_veriler)
                st.success(f"✅ İşlem Başarılı! {guncellenen_sayi} adet dosya güncellendi, {eklenen_sayi} adet yeni dosya sisteme eklendi.")
                st.rerun()

            except Exception as e:
                st.error(f"Excel işlenirken bir hata oluştu: {e}")

        # ---------------------------------------------------------------------
        # 2. JSON YÜKLENDİĞİNDE: YEDEK GERİ YÜKLEME
        # ---------------------------------------------------------------------
        elif uploaded_file.name.endswith(".json"):
            try:
                yeni_json_verisi = json.load(uploaded_file)
                verileri_kaydet(yeni_json_verisi)
                st.success("✅ JSON yedeği başarıyla yüklendi ve tüm sistem verileri güncellendi!")
                st.rerun()
            except Exception as e:
                st.error(f"JSON dosyası okunurken hata oluştu: {e}")
