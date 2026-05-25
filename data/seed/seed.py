"""
Seed script — populates the database with demo data for testing.
Run with: python data/seed/seed.py

Requires DATABASE_URL env var to be set.
Creates: brand, sources, connector_configs, categories, materials, stones,
         trend_signals, app_settings, and runs mock connector for demo products.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, text
from sqlalchemy.pool import NullPool


async def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Set it in .env or export it before running this script")
        sys.exit(1)

    print(f"Connecting to database...")
    engine = create_async_engine(db_url, poolclass=NullPool, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    seed_file = Path(__file__).parent / "demo_products.json"
    with open(seed_file) as f:
        seed_data = json.load(f)

    async with SessionLocal() as db:
        print("Seeding database...")

        # Import models here after sys.path is set
        from models.brand import Brand
        from models.source import Source
        from models.taxonomy import Category, Material, Stone
        from models.config import ConnectorConfig, AppSetting
        from models.trend import TrendSignal

        # 1. Brand
        existing_brand = (await db.execute(select(Brand).where(Brand.slug == "demo-brand"))).scalar_one_or_none()
        if not existing_brand:
            brand_data = seed_data["brand"]
            brand = Brand(**brand_data)
            db.add(brand)
            await db.flush()
            print(f"  ✓ Brand: {brand.name}")
        else:
            print(f"  → Brand already exists, skipping")

        # 2. Sources
        for src in seed_data["sources"]:
            existing = (await db.execute(select(Source).where(Source.name == src["name"]))).scalar_one_or_none()
            if not existing:
                db.add(Source(**src))
                print(f"  ✓ Source: {src['name']}")

        # 3. Connector configs
        for cfg in seed_data["connector_configs"]:
            existing = (await db.execute(select(ConnectorConfig).where(ConnectorConfig.name == cfg["name"]))).scalar_one_or_none()
            if not existing:
                db.add(ConnectorConfig(**cfg))
                print(f"  ✓ Connector config: {cfg['name']}")

        # 4. Categories
        for cat in seed_data["categories"]:
            existing = (await db.execute(select(Category).where(Category.slug == cat["slug"]))).scalar_one_or_none()
            if not existing:
                db.add(Category(**cat))
                print(f"  ✓ Category: {cat['name']}")

        # 5. Materials
        for mat in seed_data["materials"]:
            existing = (await db.execute(select(Material).where(Material.slug == mat["slug"]))).scalar_one_or_none()
            if not existing:
                db.add(Material(**mat))
                print(f"  ✓ Material: {mat['name']}")

        # 6. Stones
        for stone in seed_data["stones"]:
            existing = (await db.execute(select(Stone).where(Stone.slug == stone["slug"]))).scalar_one_or_none()
            if not existing:
                db.add(Stone(**stone))
                print(f"  ✓ Stone: {stone['name']}")

        # 7. App settings
        for setting in seed_data["app_settings"]:
            existing = (await db.execute(select(AppSetting).where(AppSetting.key == setting["key"]))).scalar_one_or_none()
            if not existing:
                db.add(AppSetting(**setting))
        print(f"  ✓ App settings: {len(seed_data['app_settings'])} entries")

        # 8. Trend signals (mock)
        for sig in seed_data["trend_signals"]:
            db.add(TrendSignal(**sig))
        print(f"  ✓ Trend signals: {len(seed_data['trend_signals'])} demo signals")

        await db.commit()

    # 9. Run mock connector to populate products
    print("\nRunning mock connector to generate demo products...")
    from connectors.mock_demo import MockDemoConnector
    connector = MockDemoConnector(num_products=40)
    result = await connector.run()
    print(f"  ✓ Mock products: {result.records_saved} saved ({result.records_fetched} fetched)")

    # 10. Score all products
    print("\nScoring demo products...")
    from services.scoring import ScoringEngine
    scored = await ScoringEngine.score_new_products(limit=100)
    print(f"  ✓ Scored: {scored} products")

    await engine.dispose()
    print("\n✅ Seed complete! Database is ready for demo mode.")
    print("\nNext steps:")
    print("  1. Start backend: cd backend && uvicorn main:app --reload")
    print("  2. Start dashboard: cd dashboard && streamlit run app.py")


if __name__ == "__main__":
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
    except ImportError:
        pass

    asyncio.run(main())
