"""Rakipler — Competitor analysis."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import api_get

st.set_page_config(page_title="Rakipler | Jewelry Trend Engine", page_icon="🏢", layout="wide")
st.title("🏢 Rakipler")
st.markdown("Rakip marka ve ürün analizi.")

# Since competitor data comes via manual upload or Etsy, show products tagged as competitor
products = api_get("/api/v1/products", {"page_size": 100})

if products and products.get("items"):
    items = products["items"]
    st.markdown(f"**{products.get('total', 0):,} takip edilen ürün**")

    # Stats by mock vs real
    mock_count = sum(1 for p in items if p.get("is_mock"))
    real_count = len(items) - mock_count

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Toplam Takip", len(items))
    with col2:
        st.metric("✅ Gerçek Ürün", real_count)
    with col3:
        st.metric("🎭 Demo Ürün", mock_count)

    st.markdown("---")

    # Price distribution
    prices = [p.get("price_usd") for p in items if p.get("price_usd")]
    if prices:
        st.subheader("💰 Fiyat Dağılımı")
        price_df = pd.DataFrame({"Fiyat (USD)": prices})
        st.bar_chart(price_df["Fiyat (USD)"].value_counts(bins=10).sort_index())

    # Mock competitor summary (since competitor table requires manual setup)
    st.markdown("---")
    st.subheader("🗂️ Rakip Ürün Yükleme")
    st.markdown("""
    Rakip ürünleri sisteme eklemek için:
    1. Ürün listesini CSV veya JSON formatında hazırlayın
    2. Aşağıdaki şablonu kullanın
    3. Supabase Storage'a yükleyin veya API üzerinden gönderin
    """)

    template_csv = """title,description,price,currency,source_url,image_url,review_count
Örnek Ürün 1,Altın kaplama yüzük,85,USD,https://example.com/product1,,150
Örnek Ürün 2,Gümüş kolye,45,USD,https://example.com/product2,,320"""

    st.download_button(
        "📥 CSV Şablonunu İndir",
        template_csv.encode("utf-8"),
        "rakip_urun_sablonu.csv",
        "text/csv",
    )
else:
    st.info("Henüz takip edilen rakip ürünü yok.")
    st.markdown("""
    **Rakip ürünleri eklemek için:**
    - Manuel yükleme: CSV/JSON dosyasını hazırlayın
    - Etsy API: `ETSY_API_KEY` yapılandırın
    - Connector Durumu sayfasından manual_upload connector'ı çalıştırın
    """)
