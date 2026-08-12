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

# Sıkılaştırılmış ve dikey boşlukları azaltan CSS
st.markdown("""
<style>
    /* Expander ve form elemanları arasındaki gereksiz iç boşlukları daraltma */
    div[data-testid="stExpander"] div[role="region"] {
        padding-top: 0.2rem !important;
        padding-bottom: 0.5rem !important;
    }
    .element-container {
        margin-bottom: -0.2rem !important;
    }
    hr {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
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

def verileri_getir():
    try:
        file_content = repo.get_contents(FILE_PATH)
        data = json.loads(file_content.decoded_content.decode('utf-8'))
        
        yeni_format_data = []
        if isinstance(data, list):
            for item in data:
                if "Aciklama" not in item:
                    item["Aciklama"] = ""
                if "Islemler" not in item:
                    item["Islemler"] = []
                if "BagliDosya" not in item:
                    item["BagliDosya"] = False
                if "KapatmaRed" not in item:
                    item["KapatmaRed"] = False
                if "TescildeBekleyen" not in item:
                    item["TescildeBekleyen"] = False
                if "KapatmaAsamasinda" not in item:
                    item["KapatmaAsamasinda"] = False
                if "YaziCevabiBekleyen" not in item:
                    item["YaziCevabiBekleyen"] = False
                if "Incelenmedi" not in item:
                    item["Incelenmedi"] = False
                if "MailAtildi" not in item:
                    item["MailAtildi"] = False
                if "MailTarihi" not in item:
                    item["MailTarihi"] = ""
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

# TOPLAM VE DURUM SAYILARI GÖSTERGELERİ (8 SÜTUNLU PANORAMA)
toplam_dosya_sayisi = len(kayitlar)
bagli_dosya_sayisi = sum(1 for d in kayitlar if d.get("BagliDosya", False))
kapatma_red_sayisi = sum(1 for d in kayitlar if d.get("KapatmaRed", False))
tescilde_bekleyen_sayisi = sum(1 for d in kayitlar if d.get("TescildeBekleyen", False))
kapatma_asamasinda_sayisi = sum(1 for d in kayitlar if d.get("KapatmaAsamasinda", False))
yazi_cevabi_bekleyen_sayisi = sum(1 for d in kayitlar if d.get("YaziCevabiBekleyen", False))
incelenmedi_sayisi = sum(1 for d in kayitlar if d.get("Incelenmedi", False))
mail_atildi_sayisi = sum(1 for d in kayitlar if d.get("MailAtildi", False))

col_m1, col_m2, col_m3, col_m4, col_m5, col_m6, col_m7, col_m8 = st.columns(8)
with col_m1:
    st.metric(label="📊 Toplam", value=f"{toplam_dosya_sayisi}")
with col_m2:
    st.metric(label="🔗 Bağlı", value=f"{bagli_dosya_sayisi}")
with col_m3:
    st.metric(label="🚫 Kapatma Red", value=f"{kapatma_red_sayisi}")
with col_m4:
    st.metric(label="⏳ Tescilde", value=f"{tescilde_bekleyen_sayisi}")
with col_m5:
    st.metric(label="🏁 Kapatmada", value=f"{kapatma_asamasinda_sayisi}")
with col_m6:
    st.metric(label="✉️ Yazı Cevabı", value=f"{yazi_cevabi_bekleyen_sayisi}")
with col_m7:
    st.metric(label="🔍 İncelenmedi", value=f"{incelenmedi_sayisi}")
with col_m8:
    st.metric(label="📧 Mail Atıldı", value=f"{mail_atildi_sayisi}")

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
                mail_atildi_durumu = dosya.get("MailAtildi", False)
                mail_tarihi_val = dosya.get("MailTarihi", "")
                
                edit_key = f"edit_aciklama_{d_no}_{d_idx}"
                confirm_del_key = f"confirm_del_single_{d_no}_{d_idx}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                if confirm_del_key not in st.session_state:
                    st.session_state[confirm_del_key] = False

                # TEMİZ DURUM SİMGELERİ
                simgeler = ""
                if bagli_durumu: simgeler += "🔗 "
                if kapatma_red_durumu: simgeler += "🚫 "
                if tescilde_durumu: simgeler += "⏳ "
                if kapatma_asamasinda_durumu: simgeler += "🏁 "
                if yazi_cevabi_durumu: simgeler += "✉️ "
                if incelenmedi_durumu: simgeler += "🔍 "

                mail_baslik_eki = ""
                if mail_atildi_durumu:
                    if mail_tarihi_val:
                        mail_baslik_eki = f" 📧 ({mail_tarihi_val} mail atıldı)"
                    else:
                        mail_baslik_eki = " 📧 (mail atıldı)"

                col_exp, col_dosya_sil = st.columns([92, 8], vertical_alignment="center")
                
                with col_exp:
                    exp_header = f"📂 **Dosya No:** {d_no} | 🏢 **Firma:** {firma} {simgeler}({len(islemler)} İşlem){mail_baslik_eki}"
                    exp_container = st.expander(exp_header, expanded=False)
                
                # KÜÇÜK SİL BUTONU VE EMİN MİSİNİZ ONAYI
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
                                verileri_kaydet(kayitlar, f"{d_no} nolu dosya silindi")
                                st.session_state[confirm_del_key] = False
                                st.success(f"'{d_no}' silindi!")
                                st.rerun()
                        with c_s_iptal:
                            if st.button("❌", key=f"no_del_{d_no}_{d_idx}", help="İptal"):
                                st.session_state[confirm_del_key] = False
                                st.rerun()

                with exp_container:
                    # --- DOSYA DURUMU VE KUTUCUKLARI ---
                    st.markdown("**📌 Dosya Durumu**")
                    col_b1, col_b2, col_b3, col_b4, col_b5, col_b6, col_b7 = st.columns(7)
                    
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
                        ch_mail = st.checkbox("📧 Mail Atıldı", value=mail_atildi_durumu, key=f"chk_mail_{d_no}_{d_idx}")

                    # Mail Tarihi alanı
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

                    # DURUM DEĞİŞİKLİKLERİNİ KAYDETME BUTONU
                    c_status_save, _ = st.columns([2, 5])
                    with c_status_save:
                        if st.button("💾 Durumu Kaydet", key=f"btn_save_status_{d_no}_{d_idx}", use_container_width=True):
                            dosya["BagliDosya"] = ch_bagli
                            dosya["KapatmaRed"] = ch_red
                            dosya["TescildeBekleyen"] = ch_tescild
                            dosya["KapatmaAsamasinda"] = ch_kapatma
                            dosya["YaziCevabiBekleyen"] = ch_yazi
                            dosya["Incelenmedi"] = ch_incel
                            dosya["MailAtildi"] = ch_mail
                            dosya["MailTarihi"] = guncel_mail_tarihi.strip() if ch_mail else ""
                            
                            verileri_kaydet(kayitlar, f"{d_no} dosya durumu güncellendi")
                            st.toast(f"✅ '{d_no}' dosyasının durumu başarıyla kaydedildi!")
                            st.rerun()

                    st.markdown("---")

                    # --- DOSYA DURUM DETAYI ---
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
                                verileri_kaydet(kayitlar, f"{d_no} dosyasının durum detayı güncellendi")
                                st.session_state[edit_key] = False
                                st.toast("✅ Durum detayı güncellendi!")
                                st.rerun()
                                
                            if cancel_aciklama:
                                st.session_state[edit_key] = False
                                st.rerun()

                    # --- YENİ İŞLEM EKLEME BÖLÜMÜ ---
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
                                st.toast("✅ İşlem başarıyla eklendi!")
                                st.rerun()
                            else:
                                st.warning("İşlem açıklaması boş olamaz.")

                    # --- GEÇMİŞ İŞLEMLER BÖLÜMÜ ---
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
                                    verileri_kaydet(kayitlar, f"{d_no} dosyasından işlem silindi")
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
    
    # 1. TEKLİ DOSYA EKLEME SEKMESİ
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
                mail_atildi_input = st.checkbox("📧 Firmaya Mail Atıldı")
                
            mail_tarihi_input = st.text_input("Mail Tarihi (Opsiyonel)", value=datetime.now().strftime("%d.%m.%Y"), placeholder="GG.AA.YYYY")

            submit_yeni = st.form_submit_button("📂 Dosya Oluştur / Güncelle", use_container_width=True)

            if submit_yeni:
                if dosya_no.strip() != "":
                    clean_dosya = dosya_no.strip()
                    clean_firma = firma.strip() if firma.strip() != "" else "-"
                    clean_aciklama = islem.strip()
                    turkey_tz = pytz.timezone("Europe/Istanbul")
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
                        mevcut["MailAtildi"] = mail_atildi_input
                        mevcut["MailTarihi"] = mail_tarihi_input.strip() if mail_atildi_input else ""
                        verileri_kaydet(kayitlar, f"{clean_dosya} dosyasının bilgileri güncellendi")
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
                            "MailAtildi": mail_atildi_input,
                            "MailTarihi": mail_tarihi_input.strip() if mail_atildi_input else "",
                            "OlusturmaTarihi": simdi,
                            "Islemler": []
                        }
                        kayitlar.append(yeni_dosya)
                        verileri_kaydet(kayitlar, f"Yeni dosya eklendi: {clean_dosya}")
                        st.toast(f"✅ '{clean_dosya}' oluşturuldu!")
                    st.rerun()
                else:
                    st.warning("Lütfen Dosya No alanını doldurun.")

    # 2. EXCEL'DEN TOPLU VERİ YAPIŞTIRMA SEKMESİ
    with tab_excel:
        st.caption("Excel'deki **5 Sütunluk** veriyi buraya yapıştırabilirsiniz:")
        st.caption("`DIIBNO1` | `DIIBNO2` | `DIIBNO3` | `Firma Unvanı` | `Durum Detayı`")
        
        with st.form("excel_paste_form", clear_on_submit=True):
            pasted_data = st.text_area("Excel Verisini Yapıştırın", placeholder="2025\tD1\t5400\tISIK CELIK SAN.VE TIC.A.S.\tİnceleme yapılıyor.", height=120)
            submit_excel = st.form_submit_button("⚡ Toplu Verileri Kaydet", use_container_width=True)
            
            if submit_excel:
                if pasted_data.strip() != "":
                    turkey_tz = pytz.timezone("Europe/Istanbul")
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
                                        "MailAtildi": False,
                                        "MailTarihi": "",
                                        "OlusturmaTarihi": simdi,
                                        "Islemler": []
                                    })
                                eklenen_sayi += 1
                                
                    if eklenen_sayi > 0:
                        verileri_kaydet(kayitlar, f"Excel'den {eklenen_sayi} adet kayıt eklendi")
                        st.toast(f"✅ Toplam {eklenen_sayi} adet dosya kaydı işlendi!")
                        st.rerun()
                    else:
                        st.warning("Geçerli formatta veri bulunamadı.")
                else:
                    st.warning("Yapıştırılan alan boş olamaz.")

    # 3. EXCEL BİREBİR UYUMLU RAPOR OLUŞTURMA SEKMESİ
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
    
    # --- TÜM DOSYALARI SİLME ---
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
                verileri_kaydet([], "Tüm dosyalar veritabanından silindi")
                st.session_state.confirm_delete_all = False
                if "rapor_cikti" in st.session_state:
                    st.session_state["rapor_cikti"] = ""
                st.toast("✅ Tüm dosyalar silindi!")
                st.rerun()
                
        with col_hayir:
            if st.button("❌ İptal Et", use_container_width=True):
                st.session_state.confirm_delete_all = False
                st.rerun()
