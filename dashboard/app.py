"""
Jewelry Trend Engine — Streamlit Dashboard
Main entry point: Ana Sayfa (Overview)
Deploy to: Streamlit Community Cloud from /dashboard folder.
"""
import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="Jewelry Trend Engine",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API client helper ────────────────────────────────────────────────────────
from api_client import api_get, api_post


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💎 Jewelry Trend Engine")
    st.markdown("---")

    health = api_get("/health")
    if health:
        env = health.get("env", "unknown")
        demo = health.get("demo_mode", False)
        ai_ok = health.get("ai_enabled", False)

        st.markdown(f"**Ortam:** `{env}`")
        if demo:
            st.warning("🎭 Demo Modu")
        else:
            st.success("🟢 Canlı")
        if ai_ok:
            st.markdown("✅ AI aktif")
        else:
            st.markdown("⚠️ AI yapılandırılmamış")
    else:
        st.error("❌ API'ye bağlanılamadı")
        st.markdown(f"API: `{API_BASE}`")

    st.markdown("---")
    st.markdown("""
    **Sayfalar:**
    - 📊 Ana Sayfa
    - 🏆 Fırsatlar
    - 📈 Trendler
    - 🔍 Ürün Keşfi
    - 🏢 Rakipler
    - ⚙️ Connector Durumu
    - 📋 Raporlar
    - ⚙️ Ayarlar
    """)

# ── Main content ─────────────────────────────────────────────────────────────
st.title("📊 Ana Sayfa — Genel Durum")
st.markdown("Mücevher trend motoruna hoş geldiniz. Pazar sinyalleri her 6 saatte güncellenir.")

# ── Overview stats ────────────────────────────────────────────────────────────
stats = api_get("/api/v1/stats/overview")
if stats:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Toplam Ürün", f"{stats.get('total_products', 0):,}")
    with col2:
        st.metric("✅ Gerçek Ürün", f"{stats.get('real_products', 0):,}")
    with col3:
        st.metric("🎭 Demo Ürün", f"{stats.get('mock_products', 0):,}")
    with col4:
        st.metric("🎯 Puanlanan Ürün", f"{stats.get('scored_products', 0):,}")

st.markdown("---")

# ── Top opportunities + Trend summary side by side ────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("🏆 En Yüksek Fırsatlar")
    top_opps = api_get("/api/v1/opportunities/top", {"limit": 5})
    if top_opps:
        for i, opp in enumerate(top_opps, 1):
            score = opp.get("total_score", 0)
            title = opp.get("product_title", "")[:60]
            mock_badge = " 🎭" if opp.get("is_mock") else ""
            bar_width = int(score)
            color = "#7C3AED" if score >= 70 else ("#F59E0B" if score >= 50 else "#9CA3AF")

            st.markdown(f"""
            <div style="margin-bottom:12px; padding:10px; border-left:4px solid {color}; background:#F9FAFB; border-radius:4px;">
              <strong>#{i} {title}{mock_badge}</strong><br>
              <div style="background:#E5E7EB; border-radius:4px; height:8px; margin-top:4px;">
                <div style="width:{bar_width}%; background:{color}; height:8px; border-radius:4px;"></div>
              </div>
              <small>Skor: <strong>{score:.1f}/100</strong></small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Henüz puanlanmış ürün yok. Connector'ları çalıştırın.")

with col_right:
    st.subheader("📈 Trend Özeti")
    trend_summary = api_get("/api/v1/trends/summary")
    if trend_summary:
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            st.metric("⬆️ Yükselen", trend_summary.get("rising", 0))
        with t_col2:
            st.metric("➡️ Sabit", trend_summary.get("stable", 0))
        with t_col3:
            st.metric("⬇️ Düşen", trend_summary.get("declining", 0))

        st.markdown("**En Hızlı Yükselen Anahtar Kelimeler:**")
        keywords = trend_summary.get("top_keywords", [])
        if keywords:
            kw_data = pd.DataFrame(keywords[:8])
            if not kw_data.empty and "keyword" in kw_data.columns:
                kw_data.columns = ["Anahtar Kelime", "Hız Skoru"]
                kw_data["Hız Skoru"] = kw_data["Hız Skoru"].round(1)
                st.dataframe(kw_data, hide_index=True, use_container_width=True)
        else:
            st.info("Trend verisi yükleniyor...")

st.markdown("---")

# ── Connector status overview ─────────────────────────────────────────────────
st.subheader("⚡ Connector Durumu")
connectors = api_get("/api/v1/connectors")
if connectors:
    cols = st.columns(len(connectors))
    for i, conn in enumerate(connectors):
        with cols[i]:
            enabled = conn.get("is_enabled", False)
            last_status = conn.get("last_run_status")
            icon = "🟢" if (enabled and last_status == "success") else ("🟡" if enabled else "⚫")
            st.markdown(f"""
            <div style="text-align:center; padding:8px; border:1px solid #E5E7EB; border-radius:8px;">
              <div style="font-size:1.5em">{icon}</div>
              <div style="font-size:0.75em; font-weight:bold;">{conn.get('display_name', conn.get('name',''))}</div>
              <div style="font-size:0.65em; color:#6B7280;">{conn.get('legal_status','')}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Connector durumu yüklenemedi.")

st.markdown("---")
st.caption("💎 Jewelry Trend Engine — AI destekli mücevher pazar araştırma sistemi")
