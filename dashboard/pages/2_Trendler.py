"""Trendler — Trend signals timeline and analysis."""
import streamlit as st
import pandas as pd

from api_client import api_get

st.set_page_config(page_title="Trendler | Jewelry Trend Engine", page_icon="📈", layout="wide")
st.title("📈 Trendler")
st.markdown("Pazar trend sinyalleri ve anahtar kelime analizi.")

with st.sidebar:
    st.header("Filtreler")
    direction_filter = st.selectbox("Yön", ["Tümü", "rising", "declining", "stable"],
                                     format_func=lambda x: {"Tümü": "Tümü", "rising": "⬆️ Yükselen", "declining": "⬇️ Düşen", "stable": "➡️ Sabit"}.get(x, x))
    source_filter = st.selectbox("Kaynak", ["Tümü", "google_trends", "mock_demo"])

# Fetch trends
params = {"page_size": 100}
if direction_filter != "Tümü":
    params["direction"] = direction_filter
if source_filter != "Tümü":
    params["source"] = source_filter

data = api_get("/api/v1/trends", params)
summary = api_get("/api/v1/trends/summary")

# Summary metrics
if summary:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("⬆️ Yükselen Sinyal", summary.get("rising", 0))
    with c2:
        st.metric("➡️ Sabit Sinyal", summary.get("stable", 0))
    with c3:
        st.metric("⬇️ Düşen Sinyal", summary.get("declining", 0))
    with c4:
        total = (summary.get("rising", 0) + summary.get("stable", 0) + summary.get("declining", 0))
        st.metric("📊 Toplam Sinyal", total)

st.markdown("---")

if data and data.get("items"):
    items = data["items"]
    df = pd.DataFrame(items)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔑 Anahtar Kelime Hız Skorları")
        if "keyword" in df.columns and "velocity_score" in df.columns:
            kw_df = df[df["keyword"].notna()].groupby("keyword")["velocity_score"].mean().reset_index()
            kw_df.columns = ["Anahtar Kelime", "Ortalama Hız"]
            kw_df = kw_df.sort_values("Ortalama Hız", ascending=False).head(15)
            st.bar_chart(kw_df.set_index("Anahtar Kelime"))
        else:
            st.info("Anahtar kelime verisi yok")

    with col_right:
        st.subheader("📊 Trend Yönü Dağılımı")
        if "trend_direction" in df.columns:
            direction_counts = df["trend_direction"].value_counts().reset_index()
            direction_counts.columns = ["Yön", "Sayı"]
            direction_map = {"rising": "⬆️ Yükselen", "declining": "⬇️ Düşen", "stable": "➡️ Sabit"}
            direction_counts["Yön"] = direction_counts["Yön"].map(direction_map).fillna(direction_counts["Yön"])
            st.bar_chart(direction_counts.set_index("Yön"))

    st.markdown("---")
    st.subheader("📋 Trend Sinyalleri Tablosu")

    display_cols = ["keyword", "trend_direction", "velocity_score", "interest_value", "geo", "source_name"]
    available_cols = [c for c in display_cols if c in df.columns]

    if available_cols:
        display_df = df[available_cols].copy()
        rename_map = {
            "keyword": "Anahtar Kelime",
            "trend_direction": "Yön",
            "velocity_score": "Hız Skoru",
            "interest_value": "İlgi Değeri",
            "geo": "Bölge",
            "source_name": "Kaynak",
        }
        display_df = display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns})
        display_df = display_df.fillna("-")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV İndir", csv, "trendler.csv", "text/csv")
else:
    st.info("Trend sinyali yok. Google Trends veya Mock connector'ı çalıştırın.")
