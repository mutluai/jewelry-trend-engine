"""
Lokal demo kurulum scripti.
Alembic yerine doğrudan SQLAlchemy kullanır — SQLite ile çalışır.
Kullanım: python setup_local.py
"""
import asyncio
import os
import sys
from pathlib import Path

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    print("✓ .env dosyası yüklendi")
except ImportError:
    pass

# backend klasörünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent / "backend"))

DB_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./local_demo.db")
print(f"✓ Veritabanı: {DB_URL}")


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import NullPool
    import models  # tüm modelleri kaydet

    # 1. Tabloları oluştur
    print("\n1. Tablolar oluşturuluyor...")
    engine = create_async_engine(DB_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        from models.base import Base
        await conn.run_sync(Base.metadata.create_all)
    print("   ✓ Tüm tablolar oluşturuldu")

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 2. Temel verileri ekle
    print("\n2. Temel veriler ekleniyor...")
    import json
    seed_file = Path(__file__).parent / "data" / "seed" / "demo_products.json"
    with open(seed_file) as f:
        seed_data = json.load(f)

    from models.source import Source
    from models.taxonomy import Category, Material, Stone
    from models.config import ConnectorConfig, AppSetting
    from models.trend import TrendSignal
    from sqlalchemy import select

    async with SessionLocal() as db:
        # Sources
        for src in seed_data["sources"]:
            ex = (await db.execute(select(Source).where(Source.name == src["name"]))).scalar_one_or_none()
            if not ex:
                db.add(Source(**src))
        # Connector configs
        for cfg in seed_data["connector_configs"]:
            ex = (await db.execute(select(ConnectorConfig).where(ConnectorConfig.name == cfg["name"]))).scalar_one_or_none()
            if not ex:
                db.add(ConnectorConfig(**cfg))
        # Categories
        for cat in seed_data["categories"]:
            ex = (await db.execute(select(Category).where(Category.slug == cat["slug"]))).scalar_one_or_none()
            if not ex:
                db.add(Category(**cat))
        # Materials
        for mat in seed_data["materials"]:
            ex = (await db.execute(select(Material).where(Material.slug == mat["slug"]))).scalar_one_or_none()
            if not ex:
                db.add(Material(**mat))
        # Stones
        for stone in seed_data["stones"]:
            ex = (await db.execute(select(Stone).where(Stone.slug == stone["slug"]))).scalar_one_or_none()
            if not ex:
                db.add(Stone(**stone))
        # App settings
        for setting in seed_data["app_settings"]:
            ex = (await db.execute(select(AppSetting).where(AppSetting.key == setting["key"]))).scalar_one_or_none()
            if not ex:
                db.add(AppSetting(**setting))
        # Trend signals
        for sig in seed_data["trend_signals"]:
            db.add(TrendSignal(**sig))

        await db.commit()
    print("   ✓ Kategoriler, materyaller, taşlar, ayarlar eklendi")

    # 3. Mock connector ile demo ürünler oluştur
    print("\n3. Demo ürünler oluşturuluyor...")
    from connectors.mock_demo import MockDemoConnector

    # database.py'deki engine'i override et
    import database
    database.engine = engine
    database.AsyncSessionLocal = SessionLocal

    connector = MockDemoConnector(num_products=40)
    result = await connector.run()
    print(f"   ✓ {result.records_saved} demo ürün oluşturuldu")

    # 4. Puanlama
    print("\n4. Ürünler puanlanıyor...")
    from services.scoring import ScoringEngine
    scored = await ScoringEngine.score_new_products(limit=100)
    print(f"   ✓ {scored} ürün puanlandı")

    await engine.dispose()

    print("\n" + "="*50)
    print("✅ Kurulum tamamlandı!")
    print("="*50)
    print("\nŞimdi backend'i başlatmak için:")
    print("  cd backend")
    print("  uvicorn main:app --reload --port 8000")
    print("\nAyrı terminalde dashboard için:")
    print("  pip install streamlit pandas httpx")
    print("  cd dashboard")
    print("  streamlit run app.py")


if __name__ == "__main__":
    asyncio.run(main())
