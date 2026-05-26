"""Connector Durumu — Connector status, controls, and run history."""
import streamlit as st

from api_client import api_get, api_post
import httpx

st.set_page_config(page_title="Connector Durumu | Jewelry Trend Engine", page_icon="⚙️", layout="wide")
st.title("⚙️ Connector Durumu")
st.markdown("Veri kaynağı connector'larını izleyin ve yönetin.")

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

connectors = api_get("/api/v1/connectors")

LEGAL_LABELS = {
    "official_api": ("🟢 Resmi API", "#059669"),
    "public_allowed": ("🔵 Kamuya Açık", "#2563EB"),
    "stub": ("🟡 Stub (API Bekleniyor)", "#D97706"),
    "mock": ("🎭 Demo/Mock", "#7C3AED"),
}

if connectors:
    for conn in connectors:
        name = conn.get("name", "")
        display = conn.get("display_name", name)
        enabled = conn.get("is_enabled", False)
        legal = conn.get("legal_status", "")
        last_run = conn.get("last_run_at", "Hiç çalışmadı")
        last_status = conn.get("last_run_status", "-")
        last_error = conn.get("last_error")

        legal_label, legal_color = LEGAL_LABELS.get(legal, (legal, "#6B7280"))
        status_icon = "🟢" if last_status == "success" else ("🔴" if last_status == "failed" else "⚪")

        with st.expander(f"{status_icon} **{display}** {'✅ Aktif' if enabled else '⛔ Devre Dışı'}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Durum:** {status_icon} `{last_status}`")
                st.markdown(f"**Son Çalışma:** {last_run or 'Hiç'}")
                if last_error:
                    st.error(f"Son Hata: {last_error[:200]}")
            with col2:
                st.markdown(f"**Yasal Durum:** <span style='color:{legal_color}'>{legal_label}</span>", unsafe_allow_html=True)
                st.markdown(f"**Connector Adı:** `{name}`")
            with col3:
                if st.button(f"▶️ Şimdi Çalıştır", key=f"run_{name}"):
                    with st.spinner(f"{display} çalışıyor..."):
                        result = api_post(f"/api/v1/connectors/{name}/run")
                        if result:
                            status = result.get("status", "?")
                            saved = result.get("records_saved", 0)
                            fetched = result.get("records_fetched", 0)
                            dur = result.get("duration_seconds", 0)
                            if status == "success":
                                st.success(f"✅ {fetched} çekildi, {saved} kaydedildi ({dur:.1f}s)")
                            else:
                                st.error(f"❌ Hata: {result.get('error', 'Bilinmeyen hata')}")

                toggle_label = "⛔ Devre Dışı Bırak" if enabled else "✅ Etkinleştir"
                if st.button(toggle_label, key=f"toggle_{name}"):
                    try:
                        resp = httpx.patch(f"{API_BASE}/api/v1/connectors/{name}/toggle", timeout=10)
                        if resp.status_code == 200:
                            new_state = resp.json().get("is_enabled")
                            st.success(f"{'Etkinleştirildi' if new_state else 'Devre dışı bırakıldı'}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
else:
    st.warning("Connector listesi yüklenemedi.")

st.markdown("---")
st.subheader("🚀 Tüm Connector'ları Çalıştır")
if st.button("▶️ Tüm Aktif Connector'ları Çalıştır", type="primary"):
    if connectors:
        enabled_list = [c for c in connectors if c.get("is_enabled")]
        progress = st.progress(0)
        for i, conn in enumerate(enabled_list):
            name = conn.get("name")
            with st.spinner(f"Çalışıyor: {name}..."):
                result = api_post(f"/api/v1/connectors/{name}/run")
                if result and result.get("status") == "success":
                    st.success(f"✅ {name}: {result.get('records_saved', 0)} kaydedildi")
                else:
                    st.error(f"❌ {name}: {result.get('error', 'Hata') if result else 'API hatası'}")
            progress.progress((i + 1) / len(enabled_list))
        st.success("🎉 Tüm connector'lar çalıştırıldı!")
