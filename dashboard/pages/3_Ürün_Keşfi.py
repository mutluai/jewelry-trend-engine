"""Ürün Keşfi — Full product database explorer."""
import streamlit as st
import pandas as pd

from api_client import api_get

st.set_page_config(page_title="Ürün Keşfi | Jewelry Trend Engine", page_icon="🔍", layout="wide")
st.title("🔍 Ürün Keşfi")
st.markdown("Tüm takip edilen ürünleri arayın, filtreleyin ve keşfedin.")

with st.sidebar:
    st.header("Filtreler")
    search = st.text_input("🔍 Ara", placeholder="ürün adı, açıklama...")
    status_filter = st.multiselect("Durum", ["raw", "analyzed", "scored"], default=["scored"])
    show_mock = st.checkbox("Demo ürünleri göster", value=True)
    page = st.number_input("Sayfa", min_value=1, value=1)
    page_size = st.select_slider("Sayfa boyutu", options=[10, 20, 50, 100], value=20)

params: dict = {"page": page, "page_size": page_size}
if search:
    params["search"] = search
if show_mock is False:
    params["is_mock"] = False

data = api_get("/api/v1/products", params)

if data:
    st.markdown(f"**{data.get('total', 0):,} ürün** | Sayfa {data.get('page', 1)}")

    items = data.get("items", [])
    if items:
        rows = []
        for p in items:
            rows.append({
                "Başlık": p.get("title", "")[:80],
                "Fiyat (USD)": f"${p.get('price_usd', 0) or 0:.0f}" if p.get("price_usd") else "-",
                "Değerlendirme": f"⭐ {p.get('review_rating', 0) or 0:.1f} ({p.get('review_count', 0):,})",
                "Kategori": (p.get("ai_attributes") or {}).get("category", "-"),
                "Materyal": (p.get("ai_attributes") or {}).get("material", "-"),
                "Stil": (p.get("ai_attributes") or {}).get("style", "-"),
                "Durum": p.get("status", ""),
                "Demo": "🎭" if p.get("is_mock") else "✅",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = pd.DataFrame(items).to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV İndir", csv, "urunler.csv", "text/csv")

        # ── Detail expander ───────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Ürün Detayı")
        selected_idx = st.number_input("Ürün indeksi (0-{})".format(len(items)-1), 0, len(items)-1, 0)
        if 0 <= selected_idx < len(items):
            p = items[selected_idx]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### {p.get('title')}")
                if p.get("source_url"):
                    st.markdown(f"[🔗 Orijinal Bağlantı]({p['source_url']})")
                st.markdown(f"**Fiyat:** ${p.get('price_usd') or 0:.2f}")
                st.markdown(f"**Değerlendirme:** {p.get('review_rating') or '-'} ({p.get('review_count', 0):,} yorum)")
                st.markdown(f"**Favori:** {p.get('favorites_count', 0):,}")
                st.markdown(f"**Durum:** `{p.get('status')}`")
                if p.get("description"):
                    st.markdown("**Açıklama:**")
                    st.markdown(p["description"][:500])
            with col2:
                if p.get("image_url"):
                    st.image(p["image_url"], width=300)
                ai_attrs = p.get("ai_attributes")
                if ai_attrs:
                    st.markdown("**🤖 AI Nitelikleri:**")
                    for k, v in ai_attrs.items():
                        if v and k != "confidence":
                            st.markdown(f"- **{k}:** {v}")
    else:
        st.info("Bu kriterlere uyan ürün bulunamadı.")
else:
    st.error("Ürünler yüklenemedi. API bağlantısını kontrol edin.")
