# JSON VE SADECE ÖZET EXCEL İNDİRME / YEDEKLEME
    st.subheader("📊 Veri İndir ve Yedekle")

    if kayitlar:
        # Dosya No verisini parçalayarak 4 sütunlu özet liste oluşturma
        ozet_excel_listesi = []
        for d in kayitlar:
            tam_dosya_no = str(d.get("Dosya No", "")).strip()
            parcalar = tam_dosya_no.split()
            
            # "2024 D1 414" gibi standart 3 parçalı yapı kontrolü
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
        
        # İstediğiniz Özet Rapor İndir Butonu
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
