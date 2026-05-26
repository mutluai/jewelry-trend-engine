"""Fırsatlar — Scored opportunity explorer."""
import streamlit as st
import pandas as pd

from api_client import api_get, api_post

st.set_page_config(page_title="Fırsatlar | Jewelry Trend Engine", page_icon="🏆", layout="wide")
st.title("🏆 Fırsatlar")
st.markdown("AI tarafından puanlanan ürün fırsatları. Yüksek skor = yüksek öncelik.")

# ── Filters ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtreler")
    min_score = st.slider("Minimum Skor", 0, 100, 0)
    max_score = st.slider("Maximum Skor", 0, 100, 100)
    show_mock = st.checkbox("Demo verisini göster", value=True)

# ── Fetch data ────────────────────────────────────────────────────────────────
data = api_get("/api/v1/opportunities", {
    "min_score": min_score,
    "max_score": max_score,
    "page_size": 50,
})

if data and data.get("items"):
    items = data["items"]
    if not show_mock:
        items = [i for i in items if not i.get("is_mock")]

    st.markdown(f"**{len(items)} fırsat bulundu** (toplam: {data.get('total', 0)})")

    # Export button
    if st.button("📥 CSV İndir"):
        rows = []
        for item in items:
            score = item.get("score", {})
            rows.append({
                "Ürün": item.get("product_title"),
                "Skor": score.get("total_score"),
                "Trend Hızı": score.get("trend_velocity_score"),
                "Marka Uyumu": score.get("brand_fit_score"),
                "Yenilik": score.get("novelty_score"),
                "URL": item.get("product_url"),
            })
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("İndir", csv, "firsatlar.csv", "text/csv")

    # ── Cards ─────────────────────────────────────────────────────────────────
    for item in items:
        score_data = item.get("score", {})
        total = score_data.get("total_score", 0)
        title = item.get("product_title", "")
        url = item.get("product_url")
        image = item.get("product_image")
        is_mock = item.get("is_mock", False)

        color = "#059669" if total >= 70 else ("#F59E0B" if total >= 50 else "#6B7280")

        with st.expander(f"{'🎭 ' if is_mock else ''}**{title[:70]}** — Skor: {total:.1f}/100"):
            col1, col2 = st.columns([2, 1])
            with col1:
                # Score breakdown chart
                components = {
                    "Trend Hızı": score_data.get("trend_velocity_score", 0),
                    "Çoklu Kaynak": score_data.get("cross_source_score", 0),
                    "Düşük Rekabet": score_data.get("competition_density_score", 0),
                    "Yenilik": score_data.get("novelty_score", 0),
                    "Marka Uyumu": score_data.get("brand_fit_score", 0),
                    "Değerlendirme": score_data.get("review_signal_score", 0),
                }
                df_comp = pd.DataFrame(list(components.items()), columns=["Bileşen", "Skor"])
                st.bar_chart(df_comp.set_index("Bileşen"))

                if url:
                    st.markdown(f"[🔗 Ürünü Görüntüle]({url})")

            with col2:
                st.metric("Toplam Skor", f"{total:.1f}/100")
                narrative = score_data.get("ai_opportunity_narrative")
                if narrative:
                    st.markdown("**AI Analizi:**")
                    st.markdown(narrative)
                recommendation = score_data.get("ai_recommendation")
                if recommendation:
                    st.success(f"**Öneri:** {recommendation}")
                risk = score_data.get("ai_risk_notes")
                if risk:
                    st.warning(f"**Risk:** {risk}")
else:
    st.info("Henüz puanlanmış fırsat yok. Connector'ları çalıştırın veya demo verisini yükleyin.")
    if st.button("🚀 Mock Connector Çalıştır"):
        result = api_post("/api/v1/connectors/mock_demo/run")
        if result:
            st.success(f"Tamamlandı: {result.get('records_saved', 0)} ürün kaydedildi")
            st.rerun()
