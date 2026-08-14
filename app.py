for d_idx, dosya in enumerate(gosterilecek_dosyalar):
            d_no = dosya.get("Dosya No", "")
            firma = dosya.get("Firma", "")
            ana_aciklama = dosya.get("Aciklama", "")
            islemler = dosya.get("Islemler", [])

            # Durumlar
            bagli_durumu = dosya.get("BagliDosya", False)
            kapatma_red_durumu = dosya.get("KapatmaRed", False)
            tescilde_durumu = dosya.get("TescildeBekleyen", False)
            kapatma_asamasinda_durumu = dosya.get("KapatmaAsamasinda", False)
            yazi_cevabi_durumu = dosya.get("YaziCevabiBekleyen", False)
            incelenmedi_durumu = dosya.get("Incelenmedi", False)
            incelemede_durumu = dosya.get("Incelemede", False)
            mail_atildi_durumu = dosya.get("MailAtildi", False)
            mail_tarihi = dosya.get("MailTarihi", "")

            # İkon Rozetleri
            simgeler = ""
            if bagli_durumu: simgeler += "🔗 "
            if kapatma_red_durumu: simgeler += "🚫 "
            if tescilde_durumu: simgeler += "⏳ "
            if kapatma_asamasinda_durumu: simgeler += "🏁 "
            if yazi_cevabi_durumu: simgeler += "✉️ "
            if incelenmedi_durumu: simgeler += "🔍 "
            if incelemede_durumu: simgeler += "🧐 "
            if mail_atildi_durumu: simgeler += "📧 "

            mail_baslik_eki = f" (📧 {mail_tarihi})" if (mail_atildi_durumu and mail_tarihi) else ""

            # Kart ve Expander Alanı
            with st.container():
                col_del, col_exp = st.columns([1, 11])

                with col_del:
                    confirm_del_key = f"confirm_del_{d_no}_{d_idx}"
                    if confirm_del_key not in st.session_state:
                        st.session_state[confirm_del_key] = False

                    if not st.session_state[confirm_del_key]:
                        if st.button("🗑️", key=f"btn_del_init_{d_no}_{d_idx}", help="Dosyayı Sil"):
                            st.session_state[confirm_del_key] = True
                            st.rerun()
                    else:
                        c_s_evet, c_s_iptal = st.columns(2)
                        with c_s_evet:
                            if st.button("✔️", key=f"confirm_del_yes_{d_no}_{d_idx}", help="Silmeyi Onayla"):
                                kayitlar = [d for d in kayitlar if d.get("Dosya No") != d_no]
                                verileri_kaydet(kayitlar, mevcut_onemli_notlar, mevcut_hatirlatmalar, mevcut_bolum_sirasi, f"{d_no} silindi")
                                st.session_state[confirm_del_key] = False
                                st.toast(f"🗑️ {d_no} silindi.")
                                st.rerun()
                        with c_s_iptal:
                            if st.button("❌", key=f"cancel_del_{d_no}_{d_idx}", help="İptal"):
                                st.session_state[confirm_del_key] = False
                                st.rerun()

                with col_exp:
                    exp_header = f"📂 **Dosya No:** {d_no}\n\n🏢 **Firma:** {firma} {simgeler}({len(islemler)} İşlem){mail_baslik_eki}"
                    exp_container = st.expander(exp_header, expanded=False)

                    with exp_container:
                        # 1. BÖLÜM: DOSYA DURUMU
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

                        # Durumu Kaydet
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

                        if islemler:
                            for isl in reversed(islemler):
                                st.caption(f"🗓️ **{isl.get('Tarih', '')}** — {isl.get('Not', '')}")
                        else:
                            st.caption("*Henüz kaydedilmiş bir işlem yok.*")

                        # Yeni İşlem Ekleme Alanı
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
