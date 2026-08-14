# Expander İçeriği: Dosya Detayları, Durum Değişikliği ve İşlem Geçmişi
                with exp_container:
                    # 1. BÖLÜM: DOSYA DURUMU (Ana Açıklama)
                    st.write("##### 1. Dosya Durumu")
                    st.markdown(f"**Açıklama:** {ana_aciklama if ana_aciklama else '_Açıklama yok._'}")
                    
                    st.markdown("---")
                    
                    # 2. BÖLÜM: DOSYA DURUM DETAYI
                    st.write("##### 2. Dosya Durum Detayı")
                    
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

                    st.markdown("---")
                    
                    # 3. BÖLÜM: DOSYADA BUGÜNE KADAR YAPILAN İŞLEMLER
                    st.write("##### 3. Dosyada Bugüne Kadar Yapılan İşlemler")
                    
                    # Geçmiş İşlemler Listesi
                    if islemler:
                        for isl in reversed(islemler):
                            st.caption(f"🗓️ **{isl.get('Tarih', '')}** — {isl.get('Not', '')}")
                    else:
                        st.caption("*Henüz kaydedilmiş bir işlem yok.*")

                    # Yeni İşlem Ekle Formu (Bölüm 3'ün İçinde)
                    st.markdown("###### ➕ Yeni İşlem Ekle")
                    with st.form(key=f"form_islem_ekle_{d_no}_{d_idx}", clear_on_submit=True):
                        yeni_islem_notu = st.text_input("İşlem Notu", placeholder=f"{d_no} nolu dosyaya yapılan işlemi giriniz...", label_visibility="collapsed")
                        submit_islem = st.form_submit_button("💾 İşlemi Kaydet")
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
