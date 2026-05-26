import os
import httpx
import streamlit as st

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


def api_get(path: str, params: dict | None = None) -> dict | list | None:
    try:
        resp = httpx.get(f"{API_BASE}{path}", params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API hatası ({path}): {e}")
        return None


def api_post(path: str, data: dict | None = None) -> dict | None:
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=data or {}, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API hatası ({path}): {e}")
        return None
