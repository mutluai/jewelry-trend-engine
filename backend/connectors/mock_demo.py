"""
MOCK/DEMO CONNECTOR
Generates realistic synthetic jewelry product data for testing and demo mode.
Makes NO external requests. All data is clearly labeled is_mock=True.
"""
import random
from datetime import datetime, timezone
from .base import BaseConnector, RawData, ProductData


MOCK_TITLES = [
    "Minimalist Gold Ring", "Pearl Drop Earrings", "Layered Chain Necklace",
    "Emerald Statement Ring", "Dainty Silver Anklet", "Rose Gold Bangle Set",
    "Diamond Stud Earrings", "Boho Turquoise Bracelet", "Vintage Cameo Brooch",
    "Evil Eye Pendant Necklace", "Moonstone Ring", "Cubic Zirconia Tennis Bracelet",
    "Hammered Gold Hoops", "Twisted Wire Ring", "Birthstone Charm Bracelet",
    "Amethyst Drop Earrings", "Gold Filled Chain Bracelet", "Sterling Silver Ring Stack",
    "Delicate Lotus Necklace", "Geometric Drop Earrings", "Opal Ring",
    "Gold Plated Cuff Bracelet", "Crystal Choker Necklace", "Infinity Symbol Ring",
    "Sapphire Cocktail Ring", "Leaf Motif Earrings", "Charm Locket Necklace",
    "Beaded Stackable Bracelets", "Pavé Diamond Band", "Freshwater Pearl Bracelet",
    "Labradorite Pendant", "Garnet Cluster Ring", "Hoop Earrings Gold",
    "Snake Chain Necklace", "Agate Slice Earrings", "Clover Charm Ring",
    "Alexandrite Color Change Ring", "Bar Necklace Personalized", "Butterfly Studs",
    "Seed Pearl Vintage Necklace",
]

CATEGORIES = ["rings", "necklaces", "bracelets", "earrings", "anklets"]
MATERIALS = ["gold-plated", "sterling silver", "rose gold", "gold filled", "brass"]
STONES = ["diamond", "emerald", "sapphire", "ruby", "pearl", "turquoise", "opal",
          "amethyst", "garnet", "moonstone", "labradorite", "cubic zirconia"]
STYLES = ["minimalist", "vintage", "boho", "classic", "statement", "dainty", "geometric"]
THEMES = ["nature", "celestial", "love", "spiritual", "art deco", "floral", "ocean"]
GEOS = ["TR", "DE", "GB", "FR", "NL", "PL"]


class MockDemoConnector(BaseConnector):
    name = "mock_demo"
    display_name = "Mock / Demo Connector"
    legal_status = "mock"
    rate_limit_seconds = 0.0
    enabled = True

    def __init__(self, num_products: int = 30):
        super().__init__()
        self.num_products = num_products

    async def fetch(self) -> list[RawData]:
        items = []
        for i in range(self.num_products):
            title = random.choice(MOCK_TITLES)
            material = random.choice(MATERIALS)
            stone = random.choice(STONES) if random.random() > 0.3 else None
            price_usd = round(random.uniform(15, 280), 2)

            description_parts = [
                f"Beautiful {title.lower()} crafted in {material}.",
                f"Features {stone} stone." if stone else "Simple and elegant design.",
                f"Style: {random.choice(STYLES)}.",
                f"Perfect for everyday wear or special occasions.",
                f"Gift box included."
            ]

            items.append(RawData(
                external_id=f"MOCK-{i:04d}",
                title=f"{title} — {material.title()}",
                description=" ".join(description_parts),
                source_url=None,
                image_url=None,
                price=price_usd,
                currency="USD",
                price_usd=price_usd,
                review_count=random.randint(0, 2500),
                review_rating=round(random.uniform(3.5, 5.0), 1) if random.random() > 0.2 else None,
                sales_count=random.randint(0, 5000),
                favorites_count=random.randint(0, 1500),
                raw_payload={
                    "material": material,
                    "stone": stone,
                    "style": random.choice(STYLES),
                    "category": random.choice(CATEGORIES),
                    "theme": random.choice(THEMES),
                    "geo": random.choice(GEOS),
                    "is_mock": True,
                },
            ))
        return items

    async def normalize(self, raw: RawData) -> ProductData:
        payload = raw.raw_payload
        return ProductData(
            title=raw.title,
            description=raw.description,
            source_url=raw.source_url,
            image_url=raw.image_url,
            price=raw.price,
            currency=raw.currency,
            price_usd=raw.price_usd,
            review_count=raw.review_count,
            review_rating=raw.review_rating,
            sales_count=raw.sales_count,
            favorites_count=raw.favorites_count,
            external_id=raw.external_id,
            target_gender="women",
            price_tier=self.infer_price_tier(raw.price_usd),
            theme=payload.get("theme"),
            is_mock=True,
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
        )
