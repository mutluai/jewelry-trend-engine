"""
Etsy OAuth 2.0 (PKCE) flow.
1. GET /auth/etsy/start  → redirects to Etsy authorization page
2. GET /auth/etsy/callback?code=...  → exchanges code for tokens, stores in DB settings
"""
import hashlib
import base64
import secrets
import logging
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

ETSY_AUTH_URL = "https://www.etsy.com/oauth/connect"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
SCOPES = "listings_r"

_pkce_store: dict[str, str] = {}  # state → code_verifier (in-memory, single instance)


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/auth/etsy/start")
async def etsy_oauth_start(request: Request):
    settings = get_settings()
    if not settings.etsy_api_key:
        return HTMLResponse("<h2>ETSY_API_KEY ortam değişkeni tanımlı değil.</h2>", status_code=400)

    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/etsy/callback"

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    _pkce_store[state] = verifier

    params = (
        f"?response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope={SCOPES}"
        f"&client_id={settings.etsy_api_key}"
        f"&state={state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    return RedirectResponse(ETSY_AUTH_URL + params)


@router.get("/auth/etsy/callback")
async def etsy_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return HTMLResponse(f"<h2>Etsy yetkilendirme hatası: {error}</h2>", status_code=400)

    verifier = _pkce_store.pop(state, None)
    if not verifier:
        return HTMLResponse("<h2>Geçersiz state — lütfen tekrar deneyin.</h2>", status_code=400)

    settings = get_settings()
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/etsy/callback"

    async with httpx.AsyncClient() as client:
        resp = await client.post(ETSY_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": settings.etsy_api_key,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": verifier,
        })

    if resp.status_code != 200:
        logger.error(f"Etsy token exchange failed: {resp.status_code} {resp.text}")
        return HTMLResponse(f"<h2>Token alınamadı: {resp.text}</h2>", status_code=400)

    tokens = resp.json()
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    # Save tokens to DB settings table
    await _save_tokens(access_token, refresh_token)

    logger.info("Etsy OAuth tokens saved to database")
    return HTMLResponse("""
    <html><body style="font-family:sans-serif;padding:40px;">
    <h2>✅ Etsy bağlantısı başarılı!</h2>
    <p>Access token ve refresh token veritabanına kaydedildi.</p>
    <p>Artık bu sekmeyi kapatabilirsiniz. Etsy connector gerçek verileri çekecek.</p>
    </body></html>
    """)


async def _save_tokens(access_token: str, refresh_token: str):
    from database import get_db_context
    from models import AppSetting
    from sqlalchemy import select

    async with get_db_context() as db:
        for key, value in [("etsy_access_token", access_token), ("etsy_refresh_token", refresh_token)]:
            result = await db.execute(select(AppSetting).where(AppSetting.key == key))
            setting = result.scalar_one_or_none()
            if setting:
                setting.value = value
            else:
                db.add(AppSetting(key=key, value=value, category="connector", description=f"Etsy OAuth {key}"))
        await db.commit()
