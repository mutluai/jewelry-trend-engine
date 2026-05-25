"""Ayarlar — Brand profile, scoring weights, and system settings."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import api_get, api_post
import httpx

st.set_page_config(page_title="Ayarlar | Jewelry Trend Engine", page_icon="⚙️", layout="wide")
st.title("⚙️ Ayarlar")
st.markdown("Marka profili, puanlama ağırlıkları ve sistem yapılandırması.")

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

tab1, tab2, tab3 = st.tabs(["🏷️ Marka Profili", "⚖️ Puanlama Ağırlıkları", "🔧 Sistem"])

# ── Tab 1: Brand Profile ──────────────────────────────────────────────────────
with tab1:
    st.subheader("Marka Profili Ayarları")

    weights = api_get("/api/v1/settings/scoring-weights")
    settings_list = api_get("/api/v1/settings")

    settings_map = {}
    if settings_list:
        settings_map = {s["key"]: s["value"] for s in settings_list if s.get("category") == "brand"}

    with st.form("brand_profile"):
        brand_name = st.text_input("Marka Adı", value=settings_map.get("brand_name", ""))
        brand_market = st.text_input("Hedef Pazar (virgülle ayrılmış)", value=settings_map.get("brand_market", "Turkey,Europe"))
        brand_style = st.text_input("Stil Odağı (virgülle ayrılmış)", value=settings_map.get("brand_style_focus", "minimalist,gold-plated,silver"))
        brand_target = st.text_input("Hedef Müşteri", value=settings_map.get("brand_target_customer", "women 20-40, gift buyers, bridal"))

        col1, col2 = st.columns(2)
        with col1:
            price_min = st.number_input("Min Fiyat (USD)", value=float(settings_map.get("brand_price_min", 25)), min_value=0.0)
        with col2:
            price_max = st.number_input("Max Fiyat (USD)", value=float(settings_map.get("brand_price_max", 250)), min_value=0.0)

        report_lang = st.selectbox("Rapor Dili", ["tr", "en"],
                                    index=0 if settings_map.get("report_language", "tr") == "tr" else 1,
                                    format_func=lambda x: "🇹🇷 Türkçe" if x == "tr" else "🇬🇧 English")

        if st.form_submit_button("💾 Kaydet", type="primary"):
            updates = {
                "brand_name": brand_name,
                "brand_market": brand_market,
                "brand_style_focus": brand_style,
                "brand_target_customer": brand_target,
                "brand_price_min": str(price_min),
                "brand_price_max": str(price_max),
                "report_language": report_lang,
            }
            try:
                for key, value in updates.items():
                    httpx.patch(f"{API_BASE}/api/v1/settings/{key}", json={"value": value}, timeout=10)
                st.success("✅ Marka profili güncellendi")
            except Exception as e:
                st.error(f"Kayıt hatası: {e}")

# ── Tab 2: Scoring Weights ────────────────────────────────────────────────────
with tab2:
    st.subheader("Puanlama Ağırlıkları")
    st.markdown("Fırsat skoru hesaplamada her bileşenin ağırlığını ayarlayın. Toplam 1.0 olmalıdır.")

    weights = api_get("/api/v1/settings/scoring-weights")
    if weights:
        with st.form("scoring_weights"):
            w_trend = st.slider("📈 Trend Hızı", 0.0, 1.0, float(weights.get("trend_velocity", 0.25)), 0.05)
            w_cross = st.slider("🔗 Çoklu Kaynak", 0.0, 1.0, float(weights.get("cross_source", 0.20)), 0.05)
            w_comp = st.slider("🏆 Rekabet Yoğunluğu (ters)", 0.0, 1.0, float(weights.get("competition_density", 0.15)), 0.05)
            w_novelty = st.slider("✨ Yenilik", 0.0, 1.0, float(weights.get("novelty", 0.15)), 0.05)
            w_fit = st.slider("💎 Marka Uyumu", 0.0, 1.0, float(weights.get("brand_fit", 0.15)), 0.05)
            w_review = st.slider("⭐ Değerlendirme Sinyali", 0.0, 1.0, float(weights.get("review_signal", 0.10)), 0.05)

            total_w = round(w_trend + w_cross + w_comp + w_novelty + w_fit + w_review, 2)
            if abs(total_w - 1.0) > 0.05:
                st.warning(f"⚠️ Toplam ağırlık: {total_w:.2f} (ideal: 1.0)")
            else:
                st.success(f"✅ Toplam: {total_w:.2f}")

            if st.form_submit_button("💾 Ağırlıkları Kaydet", type="primary"):
                try:
                    resp = httpx.patch(
                        f"{API_BASE}/api/v1/settings/scoring-weights",
                        json={
                            "trend_velocity": w_trend,
                            "cross_source": w_cross,
                            "competition_density": w_comp,
                            "novelty": w_novelty,
                            "brand_fit": w_fit,
                            "review_signal": w_review,
                        },
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        st.success("✅ Ağırlıklar güncellendi")
                    else:
                        st.error(f"Hata: {resp.text}")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
    else:
        st.info("Ayarlar yüklenemedi. API bağlantısını kontrol edin.")

# ── Tab 3: System ─────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Sistem Bilgisi")

    health = api_get("/health")
    if health:
        st.json(health)

    st.markdown("---")
    st.subheader("📖 Tüm Ayarlar")
    all_settings = api_get("/api/v1/settings")
    if all_settings:
        import pandas as pd
        df = pd.DataFrame(all_settings)
        if not df.empty:
            df = df[["key", "value", "description", "category"]].rename(columns={
                "key": "Anahtar", "value": "Değer", "description": "Açıklama", "category": "Kategori"
            })
            st.dataframe(df, use_container_width=True, hide_index=True)
