"""Mağaza Asistanı — Haftalık özet ve stok analizi."""
import streamlit as st
from api_client import api_get, api_post

st.set_page_config(
    page_title="Mağaza Asistanı | Jewelry Trend Engine",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Mağaza Asistanı")
st.markdown("Trendleri takip et, stoğunu analiz et, doğru ürünleri öne çıkar.")

tab1, tab2 = st.tabs(["📊 Haftalık Özet", "📦 Stoğumu Analiz Et"])

# ── Tab 1: Haftalık Özet ──────────────────────────────────────────────────────
with tab1:
    st.markdown("#### Bu haftanın pazar durumu — sade, anlaşılır, aksiyona hazır.")

    if st.button("🔄 Bu Haftanın Özetini Al", type="primary"):
        with st.spinner("AI analiz yapıyor..."):
            ozet = api_get("/api/v1/assistant/ozet")

        if not ozet:
            st.error("Özet alınamadı. API bağlantısını kontrol edin.")
        elif "error" in ozet:
            st.info(f"ℹ️ {ozet['error']}")
        else:
            # Başlık
            st.markdown(f"""
            <div style="background:#7C3AED;color:white;padding:20px 24px;border-radius:12px;margin-bottom:24px;">
              <div style="font-size:1.4em;font-weight:bold;">📌 {ozet.get('baslik','')}</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            # Yükselen Trendler
            with col1:
                st.markdown("### 📈 Yükselen Trendler")
                for t in ozet.get("yukselen_trendler", []):
                    ivme = t.get("ivme", "orta")
                    arrow = "⬆️" if ivme == "yüksek" else ("➡️" if ivme == "orta" else "⬇️")
                    geo = t.get("geo", "")
                    flag = "🇹🇷" if "TR" in geo else ("🇩🇪" if "DE" in geo else ("🇬🇧" if "GB" in geo else "🌍"))
                    color = "#059669" if ivme == "yüksek" else ("#D97706" if ivme == "orta" else "#DC2626")
                    st.markdown(f"""
                    <div style="border-left:4px solid {color};padding:10px 14px;margin-bottom:10px;background:#F9FAFB;border-radius:4px;">
                      <strong>{arrow} {t.get('keyword','')}</strong> {flag}<br>
                      <span style="font-size:0.9em;color:#374151;">{t.get('aciklama','')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Öne Çıkar
            with col2:
                st.markdown("### ✨ Öne Çıkarılacak Ürünler")
                for p in ozet.get("one_cikar", []):
                    st.markdown(f"""
                    <div style="border-left:4px solid #7C3AED;padding:10px 14px;margin-bottom:10px;background:#F5F3FF;border-radius:4px;">
                      <strong>⭐ {p.get('baslik','')}</strong><br>
                      <span style="font-size:0.9em;color:#374151;">{p.get('neden','')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Temin Et
            with col3:
                st.markdown("### 🛒 Bu Hafta Temin Et")
                for t in ozet.get("temin_et", []):
                    aciliyet = t.get("aciliyet", "orta")
                    color = "#DC2626" if aciliyet == "yüksek" else ("#D97706" if aciliyet == "orta" else "#6B7280")
                    urgency_label = "🔴 Acil" if aciliyet == "yüksek" else ("🟡 Orta" if aciliyet == "orta" else "🟢 Düşük")
                    st.markdown(f"""
                    <div style="border-left:4px solid {color};padding:10px 14px;margin-bottom:10px;background:#FFF7ED;border-radius:4px;">
                      <strong>🛒 {t.get('kategori','')}</strong> <small>{urgency_label}</small><br>
                      <span style="font-size:0.9em;color:#374151;">{t.get('neden','')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Genel Tavsiye
            genel = ozet.get("genel_tavsiye", "")
            if genel:
                st.markdown("---")
                st.success(f"💡 **Bu Haftanın Tavsiyesi:** {genel}")

# ── Tab 2: Stok Analizi ───────────────────────────────────────────────────────
with tab2:
    st.markdown("#### Ürünlerinizi girin, AI hangileri öne çıkmalı söylesin.")
    st.markdown("Her satıra bir ürün yazın. İsterseniz fiyat da ekleyebilirsiniz.")

    ornek = "Altın yüzük - 850 TL\nGümüş kolye - 450 TL\nİnci küpe seti - 1200 TL\nBileklik - 320 TL\nTaşlı broş - 650 TL"
    urun_metni = st.text_area(
        "Ürün listesi",
        placeholder=ornek,
        height=200,
    )

    if st.button("🔍 Stoğumu Analiz Et", type="primary"):
        satirlar = [s.strip() for s in urun_metni.strip().splitlines() if s.strip()]
        if not satirlar:
            st.warning("Lütfen en az bir ürün girin.")
        else:
            urunler = []
            for satir in satirlar:
                parts = satir.split("-")
                baslik = parts[0].strip()
                fiyat = None
                if len(parts) > 1:
                    fiyat_str = parts[-1].strip().replace("TL", "").replace("₺", "").replace(",", ".").strip()
                    try:
                        fiyat = float(fiyat_str)
                    except ValueError:
                        pass
                urunler.append({"baslik": baslik, "fiyat": fiyat})

            with st.spinner(f"{len(urunler)} ürün analiz ediliyor..."):
                sonuc = api_post("/api/v1/assistant/stok-analiz", {"urunler": urunler})

            if not sonuc:
                st.error("Analiz alınamadı.")
            else:
                analizler = sonuc.get("analizler", [])
                genel = sonuc.get("genel", "")

                one_cikacak = [a for a in analizler if a.get("durum") == "öne_çıkar"]
                bekleyecek   = [a for a in analizler if a.get("durum") == "bekle"]
                kaldirilacak = [a for a in analizler if a.get("durum") == "kaldır"]

                if one_cikacak:
                    st.markdown("### ⭐ Öne Çıkar")
                    for a in one_cikacak:
                        st.markdown(f"""
                        <div style="border:2px solid #059669;padding:14px;margin-bottom:10px;border-radius:8px;background:#F0FDF4;">
                          <strong>⭐ {a.get('baslik','')}</strong><br>
                          <span style="color:#374151;">{a.get('aciklama','')}</span><br>
                          <span style="color:#059669;font-weight:bold;">👉 {a.get('tavsiye','')}</span>
                        </div>
                        """, unsafe_allow_html=True)

                if bekleyecek:
                    st.markdown("### ⏳ Beklet")
                    for a in bekleyecek:
                        st.markdown(f"""
                        <div style="border:2px solid #D97706;padding:14px;margin-bottom:10px;border-radius:8px;background:#FFFBEB;">
                          <strong>⏳ {a.get('baslik','')}</strong><br>
                          <span style="color:#374151;">{a.get('aciklama','')}</span><br>
                          <span style="color:#D97706;">👉 {a.get('tavsiye','')}</span>
                        </div>
                        """, unsafe_allow_html=True)

                if kaldirilacak:
                    st.markdown("### 📦 İndirime Al / Kaldır")
                    for a in kaldirilacak:
                        st.markdown(f"""
                        <div style="border:2px solid #DC2626;padding:14px;margin-bottom:10px;border-radius:8px;background:#FEF2F2;">
                          <strong>📦 {a.get('baslik','')}</strong><br>
                          <span style="color:#374151;">{a.get('aciklama','')}</span><br>
                          <span style="color:#DC2626;">👉 {a.get('tavsiye','')}</span>
                        </div>
                        """, unsafe_allow_html=True)

                if genel:
                    st.markdown("---")
                    st.info(f"📋 **Genel Değerlendirme:** {genel}")
