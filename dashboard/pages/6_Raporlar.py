"""Raporlar — Generated reports list, preview, and trigger."""
import streamlit as st

from api_client import api_get, api_post

st.set_page_config(page_title="Raporlar | Jewelry Trend Engine", page_icon="📋", layout="wide")
st.title("📋 Raporlar")
st.markdown("AI tarafından oluşturulan Türkçe pazar raporları.")

# ── Generate new report ───────────────────────────────────────────────────────
st.subheader("📝 Yeni Rapor Oluştur")
col1, col2, col3 = st.columns(3)
with col1:
    report_type = st.selectbox("Rapor Türü", [
        ("daily", "📅 Günlük Özet"),
        ("weekly", "📊 Haftalık Trend Raporu"),
        ("opportunity", "🏆 Fırsat Listesi"),
    ], format_func=lambda x: x[1])
with col2:
    send_email = st.checkbox("E-posta Gönder", value=True)
    send_slack = st.checkbox("Slack Gönder", value=True)
with col3:
    st.markdown("&nbsp;")
    if st.button("🚀 Rapor Oluştur", type="primary"):
        with st.spinner("Rapor oluşturuluyor... (AI analizi yapılıyor)"):
            result = api_post("/api/v1/reports/generate", {
                "report_type": report_type[0],
                "send_email": send_email,
                "send_slack": send_slack,
            })
            if result:
                st.success(f"✅ Rapor kuyruğa alındı: `{report_type[0]}`")
                st.info("Rapor arka planda oluşturuluyor. Birkaç dakika sonra listede görünecek.")
            else:
                st.error("Rapor oluşturulamadı.")

st.markdown("---")

# ── Report list ───────────────────────────────────────────────────────────────
st.subheader("📋 Oluşturulan Raporlar")
data = api_get("/api/v1/reports")

TYPE_LABELS = {
    "daily": "📅 Günlük",
    "weekly": "📊 Haftalık",
    "opportunity": "🏆 Fırsat",
    "competitor": "🏢 Rakip",
}

if data and data.get("items"):
    reports = data["items"]
    st.markdown(f"**{len(reports)} rapor bulundu**")

    for report in reports:
        rtype = report.get("report_type", "")
        title = report.get("title", "")
        created = report.get("created_at", "")[:10]
        lang = report.get("language", "tr")
        products_count = report.get("product_count", 0)
        tokens = report.get("ai_tokens_used", 0)
        email_sent = report.get("email_sent", False)
        slack_sent = report.get("slack_sent", False)
        storage_url = report.get("storage_url")

        label = TYPE_LABELS.get(rtype, rtype)

        with st.expander(f"{label} **{title}** — {created}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Dil:** {lang.upper()}")
                st.markdown(f"**Ürün Sayısı:** {products_count:,}")
                st.markdown(f"**AI Token:** {tokens:,}")
            with col2:
                st.markdown(f"**E-posta:** {'✅' if email_sent else '⛔'}")
                st.markdown(f"**Slack:** {'✅' if slack_sent else '⛔'}")
                if storage_url:
                    st.markdown(f"[📄 Raporu İndir]({storage_url})")
else:
    st.info("Henüz oluşturulmuş rapor yok. Yukarıdaki butonu kullanarak rapor oluşturun.")
    st.markdown("""
    **Demo modunda rapor oluşturmak için:**
    1. `ANTHROPIC_API_KEY` ortam değişkenini ayarlayın
    2. Yukarıdaki "Rapor Oluştur" butonuna tıklayın
    3. API yapılandırılmamışsa rapor içeriği boş gelecektir
    """)
