import streamlit as st
from github import Github
import json
import pandas as pd
from datetime import datetime, timedelta
import io

# Page Configuration
st.set_page_config(
    page_title="İş Takip Portalı",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Stiling
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #1f77b4;
    }
    .red-alert-box {
        background-color: #ffebee;
        border: 1px solid #ffcdd2;
        color: #b71c1c;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .clock-display {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# GitHub Credentials Setup
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = st.secrets.get("REPO_NAME", "")
FILE_PATH = st.secrets.get("FILE_PATH", "data.json")

def verileri_getir():
    """GitHub üzerinden verileri çeker."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(FILE_PATH)
        data = json.loads(contents.decoded_content.decode('utf-8'))
        
        # Varsayılan eksik alan tamamlama
        for item in data:
            if "SiraNo" not in item:
                item["SiraNo"] = 0
            if "MailTarihi" not in item:
                item["MailTarihi"] = datetime.now().strftime("%Y-%m-%d")
            if "Durum" not in item:
                item["Durum"] = "İncelenmedi"
            if "Gecmis" not in item:
                item["Gecmis"] = []
            if "Bolum" not in item:
                item["Bolum"] = "İncelenmedi"
        return data, contents.sha
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return [], None

def verileri_kaydet(data, sha, commit_message="Veriler güncellendi"):
    """GitHub üzerindeki veri dosyasını günceller."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        repo.update_file(
            path=FILE_PATH,
            message=commit_message,
            content=json_data,
            sha=sha
        )
        st.success("Veriler başarıyla GitHub'a kaydedildi!")
        st.rerun()
    except Exception as e:
        st.error(f"Veri kaydetme hatası: {e}")

# Uygulama Başlığı ve Saat
col_title, col_clock = st.columns([3, 1])
with col_title:
    st.title("📋 İş Takip Portalı")
with col_clock:
    suanki_saat = datetime.now().strftime("%d.%m.%Y %H:%M")
    st.markdown(f"<div class='clock-display'>⏰ {suanki_saat}</div>", unsafe_allow_html=True)

# Verileri Yükle
data, sha = verileri_getir()

# Sidebar - Dosya Ekleme ve Yedekleme İşlemleri
st.sidebar.header("⚙️ Yönetim Paneli")

# Yeni Dosya Ekleme Formu
with st.sidebar.expander("➕ Yeni Dosya Ekle", expanded=False):
    with st.form("yeni_dosya_formu"):
        yeni_firma = st.text_input("Firma Adı")
        yeni_konu = st.text_input("Konu / Dosya Adı")
        yeni_bolum = st.selectbox("Bölüm", ["Kapatmada", "İncelenmedi", "İncelemede", "Notlar", "Hatırlatmalar"])
        yeni_aciklama = st.text_area("Açıklama")
        submit_btn = st.form_submit_button("Dosya Oluştur")
        
        if submit_btn and yeni_firma:
            yeni_id = max([item.get("id", 0) for item in data], default=0) + 1
            yeni_kayit = {
                "id": yeni_id,
                "SiraNo": len(data) + 1,
                "Firma": yeni_firma,
                "Konu": yeni_konu,
                "Durum": yeni_bolum,
                "Bolum": yeni_bolum,
                "MailTarihi": datetime.now().strftime("%Y-%m-%d"),
                "Aciklama": yeni_aciklama,
                "Gecmis": [{
                    "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Not": "Dosya oluşturuldu."
                }]
            }
            data.append(yeni_kayit)
            verileri_kaydet(data, sha, f"Yeni dosya eklendi: {yeni_firma}")

# Veri Dışa/İçe Aktar
st.sidebar.subheader("💾 Veri Aktarımı & Yedek")
if data:
    df_export = pd.DataFrame(data)
    
    # Excel İndir
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Veriler')
    st.sidebar.download_button(
        label="📊 Excel Olarak İndir",
        data=buffer.getvalue(),
        file_name=f"is_takip_yedek_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # JSON İndir
    json_bytes = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
    st.sidebar.download_button(
        label="📄 JSON Olarak İndir",
        data=json_bytes,
        file_name=f"data_backup_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )

# Dosya Yükleyip Üzerine Yazma
uploaded_file = st.sidebar.file_uploader("📂 Yedek Yükle (JSON/Excel)", type=["json", "xlsx"])
if uploaded_file is not None:
    if st.sidebar.button("⚠️ Yüklenen Veriyi GitHub'a Yaz"):
        try:
            if uploaded_file.name.endswith(".json"):
                yuklenen_veri = json.load(uploaded_file)
            else:
                df_loaded = pd.read_excel(uploaded_file)
                yuklenen_veri = df_loaded.to_dict(orient="records")
            
            verileri_kaydet(yuklenen_veri, sha, "Yedekten veri geri yüklendi.")
        except Exception as e:
            st.sidebar.error(f"Dosya okuma hatası: {e}")

# Metrik Göstergeleri
col1, col2, col3, col4, col5 = st.columns(5)
toplam_dosya = len(data)
kapatmada_sayisi = len([x for x in data if x.get("Bolum") == "Kapatmada"])
incelenmedi_sayisi = len([x for x in data if x.get("Bolum") == "İncelenmedi"])
incelemede_sayisi = len([x for x in data if x.get("Bolum") == "İncelemede"])
notlar_sayisi = len([x for x in data if x.get("Bolum") in ["Notlar", "Hatırlatmalar"]])

col1.metric("Toplam Dosya", toplam_dosya)
col2.metric("Kapatmada", kapatmada_sayisi)
col3.metric("İncelenmedi", incelenmedi_sayisi)
col4.metric("İncelemede", incelemede_sayisi)
col5.metric("Notlar / Hatırlatma", notlar_sayisi)

st.divider()

# Dinamik Bölüm Sıralama ve Görünüm
bolumler = ["Kapatmada", "İncelenmedi", "İncelemede", "Notlar", "Hatırlatmalar"]
cols = st.columns(len(bolumler))

for idx, bolum in enumerate(bolumler):
    with cols[idx]:
        st.subheader(f"📌 {bolum}")
        bolum_verileri = [item for item in data if item.get("Bolum") == bolum]
        
        # Kart Sıralaması (SiraNo'ya göre)
        bolum_verileri = sorted(bolum_verileri, key=lambda x: x.get("SiraNo", 0))
        
        for item_idx, item in enumerate(bolum_verileri):
            with st.container():
                st.markdown(f"**{item.get('Firma', 'İsimsiz Firma')}**")
                st.caption(f"Konu: {item.get('Konu', '-')}")
                
                # Checkbox Durum Takibi
                tamamlandi = st.checkbox("Tamamlandı", value=(item.get("Durum") == "Tamamlandı"), key=f"chk_{item.get('id')}")
                
                # Açıklama Metni
                yeni_aciklama = st.text_area("Açıklama", value=item.get("Aciklama", ""), key=f"txt_{item.get('id')}", height=70)
                
                # Yön ve Sıralama Butonları
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                
                with btn_col1:
                    if st.button("⬅️", key=f"left_{item.get('id')}"):
                        if idx > 0:
                            item["Bolum"] = bolumler[idx - 1]
                            verileri_kaydet(data, sha, f"{item.get('Firma')} solu aktarıldı.")
                            
                with btn_col2:
                    if st.button("➡️", key=f"right_{item.get('id')}"):
                        if idx < len(bolumler) - 1:
                            item["Bolum"] = bolumler[idx + 1]
                            verileri_kaydet(data, sha, f"{item.get('Firma')} sağa aktarıldı.")
                            
                with btn_col3:
                    if st.button("⬆️", key=f"up_{item.get('id')}"):
                        if item_idx > 0:
                            item["SiraNo"] = item_idx - 1
                            bolum_verileri[item_idx - 1]["SiraNo"] = item_idx
                            verileri_kaydet(data, sha, "Sıralama yukarı taşındı.")
                            
                with btn_col4:
                    if st.button("⬇️", key=f"down_{item.get('id')}"):
                        if item_idx < len(bolum_verileri) - 1:
                            item["SiraNo"] = item_idx + 1
                            bolum_verileri[item_idx + 1]["SiraNo"] = item_idx
                            verileri_kaydet(data, sha, "Sıralama aşağı taşındı.")

                # Geçmiş Akışı ve Not Ekleme
                with st.expander("📜 İşlem Geçmişi"):
                    for g_item in item.get("Gecmis", []):
                        st.text(f"• {g_item.get('Tarih')}: {g_item.get('Not')}")
                    
                    yeni_not = st.text_input("Not Ekle", key=f"not_in_{item.get('id')}")
                    if st.button("Notu Kaydet", key=f"not_btn_{item.get('id')}"):
                        if yeni_not:
                            item["Gecmis"].append({
                                "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Not": yeni_not
                            })
                            verileri_kaydet(data, sha, f"{item.get('Firma')} dosyasına not eklendi.")

                # Genel Durumu Kaydet Butonu
                if st.button("Durumu Kaydet", key=f"save_btn_{item.get('id')}"):
                    item["Aciklama"] = yeni_aciklama
                    item["Durum"] = "Tamamlandı" if tamamlandi else item.get("Bolum")
                    verileri_kaydet(data, sha, f"{item.get('Firma')} güncellendi.")
                
                st.divider()
