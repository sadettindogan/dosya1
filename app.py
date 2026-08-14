with c_s_iptal:
                            if st.button("❌", key=f"cancel_del_{d_no}_{d_idx}", help="İptal"):
                                st.session_state[confirm_del_key] = False
                                st.rerun()

                # Expander İçeriği: Dosya Detayları, Durum Değişikliği ve İşlem Geçmişi
                with exp_container:
                    st.markdown(f"**Açıklama:** {ana_aciklama if ana_aciklama else '_Açıklama yok._'}")
                    
                    # Durum Bayrakları ve Güncelleme Formu
                    st.markdown("---")
                    st.write("##### 📌 Dosya Durumu Güncelle")
                    
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

                    # İşlem Geçmişi ve Yeni İşlem Ekleme
                    st.markdown("---")
                    st.write("##### 📜 İşlem Geçmişi")
                    if islemler:
                        for isl in reversed(islemler):
                            st.caption(f"🗓️ **{isl.get('Tarih', '')}** — {isl.get('Not', '')}")
                    else:
                        st.caption("*Henüz kaydedilmiş bir işlem yok.*")

                    with st.form(key=f"form_islem_ekle_{d_no}_{d_idx}", clear_on_submit=True):
                        yeni_islem_notu = st.text_input("Yeni İşlem Notu", placeholder="Yapılan işlemi giriniz...")
                        submit_islem = st.form_submit_button("➕ İşlem Ekle")
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
