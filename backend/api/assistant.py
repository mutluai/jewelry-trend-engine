"""Mağaza Asistanı — AI-powered weekly brief and stock analysis endpoints."""
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ai.client import call_gemini
from database import get_db
from models import OpportunityScore, Product, TrendSignal

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class StokUrun(BaseModel):
    baslik: str
    kategori: str | None = None
    fiyat: float | None = None


class StokAnalizRequest(BaseModel):
    urunler: list[StokUrun]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VELOCITY_LABEL = {
    "high": "yüksek",
    "medium": "orta",
    "low": "düşük",
}

_GEO_FLAG = {
    "TR": "🇹🇷 TR",
    "DE": "🇩🇪 DE",
    "GB": "🇬🇧 GB",
    "US": "🇺🇸 US",
}

SYSTEM_OZET = (
    "Sen deneyimli bir mücevher sektörü danışmanısın. "
    "Teknik terim kullanma, sade Türkçe yaz. "
    "Hedef kitle: teknoloji bilgisi olmayan takı mağazası sahipleri."
)

SYSTEM_STOK = (
    "Sen deneyimli bir mücevher sektörü danışmanısın. "
    "Teknik terim kullanma, sade ve anlaşılır Türkçe yaz. "
    "Hedef kitle: teknoloji bilgisi olmayan takı mağazası sahipleri."
)


def _velocity_label(score: float | None) -> str:
    if score is None:
        return "orta"
    if score >= 70:
        return "yüksek"
    if score >= 40:
        return "orta"
    return "düşük"


def _geo_display(geo: str | None) -> str:
    if not geo:
        return "TR"
    return _GEO_FLAG.get(geo.upper(), geo.upper())


def _safe_parse_json(raw: str) -> dict:
    """Try to parse JSON; strip markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        # Strip ```json ... ``` or ``` ... ```
        lines = text.splitlines()
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                inner.append(line)
        text = "\n".join(inner)
    return json.loads(text)


# ---------------------------------------------------------------------------
# GET /assistant/ozet
# ---------------------------------------------------------------------------


@router.get("/assistant/debug")
async def debug_counts(db: AsyncSession = Depends(get_db)) -> Any:
    """Debug: count records in key tables."""
    total_signals = (await db.execute(select(func.count()).select_from(TrendSignal))).scalar()
    real_signals = (await db.execute(
        select(func.count()).select_from(TrendSignal)
        .where(or_(TrendSignal.is_mock == False, TrendSignal.is_mock.is_(None)))  # noqa: E712
    )).scalar()
    sample = (await db.execute(
        select(TrendSignal.keyword, TrendSignal.geo, TrendSignal.source_name, TrendSignal.is_mock)
        .limit(5)
    )).all()
    return {
        "total_trend_signals": total_signals,
        "real_trend_signals": real_signals,
        "sample": [{"keyword": r[0], "geo": r[1], "source": r[2], "is_mock": r[3]} for r in sample],
    }


@router.get("/assistant/ozet")
async def haftalik_ozet(db: AsyncSession = Depends(get_db)) -> Any:
    """Generate an AI weekly brief from real trend & product data."""

    # 1. Fetch top trend signals (all sources, including demo seed data)
    trend_q = (
        select(TrendSignal)
        .order_by(TrendSignal.velocity_score.desc().nulls_last())
        .limit(15)
    )
    trend_result = await db.execute(trend_q)
    signals: list[TrendSignal] = list(trend_result.scalars().all())

    # 2. Fetch top products by opportunity score
    product_q = (
        select(Product, OpportunityScore)
        .join(OpportunityScore, OpportunityScore.product_id == Product.id)
        .order_by(OpportunityScore.total_score.desc())
        .limit(10)
    )
    product_result = await db.execute(product_q)
    product_rows = product_result.all()

    # 3. Guard: need at least trend signals
    if not signals:
        return {
            "error": (
                "Henüz trend verisi yok. "
                "Connector Durumu sayfasından Google Trends connector'ı çalıştırın."
            )
        }

    # 4. Build data summary for the prompt
    trend_lines: list[str] = []
    for s in signals:
        kw = s.keyword or s.category or s.material or "—"
        vel = _velocity_label(s.velocity_score)
        geo = _geo_display(s.geo)
        direction = s.trend_direction or "bilinmiyor"
        trend_lines.append(
            f"- Anahtar kelime: {kw} | Bölge: {geo} | Yön: {direction} | İvme: {vel}"
        )

    product_lines: list[str] = []
    for row in product_rows:
        product: Product = row[0]
        score: OpportunityScore = row[1]
        price_str = f"{product.price_usd:.0f} USD" if product.price_usd else "fiyat bilinmiyor"
        product_lines.append(
            f"- {product.title} | Fiyat: {price_str} | Fırsat skoru: {score.total_score:.0f}/100"
        )

    trend_block = "\n".join(trend_lines) if trend_lines else "Trend verisi yok."
    product_block = "\n".join(product_lines) if product_lines else "Ürün verisi yok."

    user_prompt = f"""Aşağıda bu haftanın mücevher pazar verisi var.

=== TREND SİNYALLERİ ===
{trend_block}

=== EN YÜKSEK FIRSATLI ÜRÜNLER ===
{product_block}

Bu verileri analiz et ve aşağıdaki JSON formatında Türkçe yanıt ver:
{{
  "baslik": "Bu haftanın tek cümlelik özeti (mağaza sahibine hitap eden, sade dil)",
  "yukselen_trendler": [
    {{
      "keyword": "anahtar kelime",
      "aciklama": "Bu trendin mağaza sahibi için ne anlama geldiği (1-2 cümle)",
      "geo": "TR/DE/GB veya uygun bölge kodu",
      "ivme": "yüksek/orta/düşük"
    }}
  ],
  "one_cikar": [
    {{
      "baslik": "Ürün veya kategori adı",
      "neden": "Neden şimdi öne çıkarmalı (kısa, net)"
    }}
  ],
  "temin_et": [
    {{
      "kategori": "Temin edilmesi önerilen ürün/kategori",
      "neden": "Neden temin etmeli",
      "aciliyet": "yüksek/orta/düşük"
    }}
  ],
  "genel_tavsiye": "Bu hafta mağaza sahibine tek paragraf genel öneri"
}}

Yalnızca geçerli JSON döndür. Başka hiçbir şey ekleme."""

    # 5. Call Gemini
    try:
        raw, usage = await call_gemini(
            prompt=user_prompt,
            system=SYSTEM_OZET,
            expect_json=True,
        )
        logger.info(
            "Ozet generated — input_tokens=%s output_tokens=%s latency_ms=%s",
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("latency_ms"),
        )
        result = _safe_parse_json(raw)
        return result

    except json.JSONDecodeError as e:
        logger.error("JSON parse error in ozet: %s", e)
        return _fallback_ozet(signals, product_rows)

    except Exception as e:
        logger.error("Gemini call failed in ozet: %s", e, exc_info=True)
        return _fallback_ozet(signals, product_rows)


def _fallback_ozet(
    signals: list[TrendSignal],
    product_rows: list,
) -> dict:
    """Return a rule-based brief when Gemini is unavailable."""
    top_kw = next(
        (s.keyword or s.category or "mücevher" for s in signals if s.keyword or s.category),
        "mücevher",
    )
    top_products = []
    for row in product_rows[:3]:
        p: Product = row[0]
        top_products.append({"baslik": p.title, "neden": "Yüksek fırsat skoru"})

    yukselen = []
    for s in signals[:5]:
        kw = s.keyword or s.category or s.material or "—"
        yukselen.append(
            {
                "keyword": kw,
                "aciklama": f"{kw} kategorisinde talep artışı gözlemleniyor.",
                "geo": s.geo or "TR",
                "ivme": _velocity_label(s.velocity_score),
            }
        )

    temin = []
    for s in signals[:3]:
        cat = s.category or s.keyword or "mücevher"
        temin.append(
            {
                "kategori": cat,
                "neden": "Trend ivmesi yüksek, stok hazırlığı yapılmalı.",
                "aciliyet": _velocity_label(s.velocity_score),
            }
        )

    return {
        "baslik": f"Bu hafta '{top_kw}' öne çıkıyor — stok ve vitrin düzenlemesi önerilir.",
        "yukselen_trendler": yukselen,
        "one_cikar": top_products,
        "temin_et": temin,
        "genel_tavsiye": (
            "Trend verileri güncellendi. AI analizi şu an erişilemiyor, "
            "ancak yukarıdaki veriler doğrudan sistemden alındı. "
            "Birkaç dakika sonra tekrar deneyin."
        ),
    }


# ---------------------------------------------------------------------------
# POST /assistant/stok-analiz
# ---------------------------------------------------------------------------


@router.post("/assistant/stok-analiz")
async def stok_analiz(
    request: StokAnalizRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze user's product list against current rising trends."""

    if not request.urunler:
        raise HTTPException(status_code=422, detail="En az bir ürün girin.")

    # 1. Fetch rising trends (real data only)
    trend_q = (
        select(TrendSignal)
        .where(
            TrendSignal.trend_direction == "rising",
            TrendSignal.is_mock == False,  # noqa: E712
        )
        .order_by(TrendSignal.velocity_score.desc().nulls_last())
        .limit(10)
    )
    trend_result = await db.execute(trend_q)
    signals: list[TrendSignal] = list(trend_result.scalars().all())

    # 2. Build trend context string
    if signals:
        trend_lines = []
        for s in signals:
            kw = s.keyword or s.category or s.material or "—"
            vel = _velocity_label(s.velocity_score)
            geo = _geo_display(s.geo)
            trend_lines.append(f"- {kw} | Bölge: {geo} | İvme: {vel}")
        trend_context = "\n".join(trend_lines)
    else:
        trend_context = "Şu an yükselen trend sinyali bulunmuyor."

    # 3. Build product list string
    product_lines = []
    for u in request.urunler:
        parts = [u.baslik]
        if u.kategori:
            parts.append(f"kategori: {u.kategori}")
        if u.fiyat:
            parts.append(f"fiyat: {u.fiyat:.0f} TL")
        product_lines.append("- " + " | ".join(parts))
    product_context = "\n".join(product_lines)

    user_prompt = f"""Aşağıda bir mağaza sahibinin ürün listesi ve mevcut pazar trendleri var.

=== MAĞAZA ÜRÜNLERİ ===
{product_context}

=== ŞU AN YÜKSELENTRENDler ===
{trend_context}

Her ürünü pazar trendlerine göre değerlendir ve aşağıdaki JSON formatında yanıt ver:
{{
  "analizler": [
    {{
      "baslik": "ürün adı (aynen kullan)",
      "durum": "öne_çıkar/bekle/kaldır",
      "skor": 0-100 arası tam sayı,
      "aciklama": "Bu ürünün mevcut trend ile uyumu hakkında 1-2 cümle (sade Türkçe)",
      "tavsiye": "Mağaza sahibine bu ürün için somut bir öneri (1 cümle)"
    }}
  ],
  "genel": "Tüm ürün listesi için genel bir değerlendirme ve bu hafta ne yapılmalı (1 paragraf)"
}}

Durum seçimi kuralları:
- öne_çıkar: Ürün mevcut trendlerle örtüşüyor, vitrine al, sosyal medyada paylaş
- bekle: Ürün şimdilik orta düzeyde, stokta tut ama aktif tanıtım yapma
- kaldır: Ürün düşen veya ilgisiz trendde, indirime çek veya kaldır

Yalnızca geçerli JSON döndür. Her ürün için bir analiz girişi olsun."""

    # 4. Call Gemini
    try:
        raw, usage = await call_gemini(
            prompt=user_prompt,
            system=SYSTEM_STOK,
            expect_json=True,
        )
        logger.info(
            "Stok analiz generated — input_tokens=%s output_tokens=%s latency_ms=%s",
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("latency_ms"),
        )
        result = _safe_parse_json(raw)

        # Validate expected keys exist; fill defaults if partial
        analizler = result.get("analizler", [])
        if not isinstance(analizler, list):
            analizler = []

        # Ensure every submitted product has an entry (fill gaps gracefully)
        submitted_titles = {u.baslik for u in request.urunler}
        returned_titles = {a.get("baslik", "") for a in analizler}
        missing = submitted_titles - returned_titles
        for title in missing:
            analizler.append(
                {
                    "baslik": title,
                    "durum": "bekle",
                    "skor": 50,
                    "aciklama": "Bu ürün için analiz alınamadı.",
                    "tavsiye": "Daha sonra tekrar deneyin.",
                }
            )

        return {
            "analizler": analizler,
            "genel": result.get("genel", "Analiz tamamlandı."),
        }

    except json.JSONDecodeError as e:
        logger.error("JSON parse error in stok-analiz: %s", e)
        return _fallback_stok(request.urunler, signals)

    except Exception as e:
        logger.error("Gemini call failed in stok-analiz: %s", e, exc_info=True)
        return _fallback_stok(request.urunler, signals)


def _fallback_stok(urunler: list[StokUrun], signals: list[TrendSignal]) -> dict:
    """Return a rule-based analysis when Gemini is unavailable."""
    rising_keywords: set[str] = set()
    for s in signals:
        for field in (s.keyword, s.category, s.material, s.style):
            if field:
                rising_keywords.add(field.lower())

    analizler = []
    for u in urunler:
        title_lower = u.baslik.lower()
        match = any(kw in title_lower for kw in rising_keywords)
        durum = "öne_çıkar" if match else "bekle"
        skor = 75 if match else 45
        aciklama = (
            "Bu ürün yükselen trendlerle örtüşüyor."
            if match
            else "Bu ürün için belirgin bir trend sinyali yok."
        )
        tavsiye = (
            "Vitrine alın ve sosyal medyada tanıtın."
            if match
            else "Stokta tutun, gelecek hafta tekrar değerlendirin."
        )
        analizler.append(
            {
                "baslik": u.baslik,
                "durum": durum,
                "skor": skor,
                "aciklama": aciklama,
                "tavsiye": tavsiye,
            }
        )

    return {
        "analizler": analizler,
        "genel": (
            "AI analizi şu an erişilemiyor. Sonuçlar trend anahtar kelimeleri "
            "ile basit eşleştirme yapılarak oluşturuldu. "
            "Daha ayrıntılı analiz için birkaç dakika sonra tekrar deneyin."
        ),
    }
