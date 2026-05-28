"""Connector Durumu — Connector status, controls, and run history."""
import time
import streamlit as st

from api_client import api_get, api_post, API_BASE
import httpx

st.set_page_config(page_title="Connector Durumu | Jewelry Trend Engine", page_icon="⚙️", layout="wide")
st.title("⚙️ Connector Durumu")
st.markdown("Veri kaynağı connector'larını izleyin ve yönetin.")

connectors = api_get("/api/v1/connectors")

LEGAL_LABELS = {
    "official_api": ("🟢 Resmi API", "#059669"),
    "public_allowed": ("🔵 Kamuya Açık", "#2563EB"),
    "stub": ("🟡 Stub (API Bekleniyor)", "#D97706"),
    "mock": ("🎭 Demo/Mock", "#7C3AED"),
}

# Auto-poll while any connector is running
any_running = any(c.get("last_run_status") == "running" for c in (connectors or []))
if any_running or st.session_state.get("polling"):
    st.session_state["polling"] = True
    poll_box = st.info("🔄 Arka planda çalışan connector var, durum güncelleniyor...")
    time.sleep(4)
    st.session_state.pop("polling", None)
    st.rerun()
else:
    st.session_state.pop("polling", None)

if connectors:
    for conn in connectors:
        name = conn.get("name", "")
        display = conn.get("display_name", name)
        enabled = conn.get("is_enabled", False)
        legal = conn.get("legal_status", "")
        last_run = conn.get("last_run_at", "Hiç çalışmadı")
        last_status = conn.get("last_run_status", "-")
        last_error = conn.get("last_error")
        cfg = conn.get("config_json") or {}
        last_fetched = cfg.get("last_records_fetched")
        last_saved = cfg.get("last_records_saved")
        last_dur = cfg.get("last_duration_seconds")

        legal_label, legal_color = LEGAL_LABELS.get(legal, (legal, "#6B7280"))

        if last_status == "success":
            status_icon = "🟢"
        elif last_status == "failed":
            status_icon = "🔴"
        elif last_status == "running":
            status_icon = "⏳"
        else:
            status_icon = "⚪"

        with st.expander(f"{status_icon} **{display}** {'✅ Aktif' if enabled else '⛔ Devre Dışı'}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Durum:** {status_icon} `{last_status}`")
                if last_status == "running":
                    st.caption("Arka planda çalışıyor, otomatik yenileniyor...")
                st.markdown(f"**Son Çalışma:** {last_run or 'Hiç'}")
                if last_error:
                    st.error(f"Son Hata: {last_error[:200]}")
            with col2:
                st.markdown(f"**Yasal Durum:** <span style='color:{legal_color}'>{legal_label}</span>", unsafe_allow_html=True)
                st.markdown(f"**Connector Adı:** `{name}`")
                if last_fetched is not None:
                    dur_str = f" ({last_dur:.1f}s)" if last_dur else ""
                    st.markdown(f"**Son Sonuç:** {last_fetched} çekildi, **{last_saved} kaydedildi**{dur_str}")
            with col3:
                if last_status != "running":
                    if st.button("▶️ Şimdi Çalıştır", key=f"run_{name}"):
                        with st.spinner(f"{display} başlatılıyor..."):
                            result = api_post(f"/api/v1/connectors/{name}/run")
                            if result:
                                status = result.get("status", "?")
                                saved = result.get("records_saved", 0)
                                fetched = result.get("records_fetched", 0)
                                dur = result.get("duration_seconds", 0)
                                if status == "success":
                                    st.success(f"✅ {fetched} çekildi, {saved} kaydedildi ({dur:.1f}s)")
                                elif status == "running":
                                    st.session_state["polling"] = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ Hata: {result.get('error', 'Bilinmeyen hata')}")
                else:
                    st.button("⏳ Çalışıyor...", key=f"run_{name}", disabled=True)

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
        has_background = False
        for i, conn in enumerate(enabled_list):
            name = conn.get("name")
            with st.spinner(f"Çalışıyor: {name}..."):
                result = api_post(f"/api/v1/connectors/{name}/run")
                if result:
                    s = result.get("status")
                    if s == "success":
                        st.success(f"✅ {name}: {result.get('records_saved', 0)} kaydedildi")
                    elif s == "running":
                        st.info(f"⏳ {name}: arka planda çalışıyor")
                        has_background = True
                    else:
                        st.error(f"❌ {name}: {result.get('error', 'Hata') if result else 'API hatası'}")
            progress.progress((i + 1) / len(enabled_list))
        if has_background:
            st.session_state["polling"] = True
        st.rerun()
