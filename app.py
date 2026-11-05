import logging
import random
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import (
    ConnectionError as CurlConnectionError,
    HTTPError as CurlHTTPError,
    RequestException as CurlRequestException,
    Timeout as CurlTimeout,
)
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route


SERVICE_NAME = "star"
ROUTE_PREFIX = f"/{SERVICE_NAME}"
PROXY_URL = None

STARHUB_CDNS = [
    "CO2-BKS400-04.starhubgo.com:443",
    "CO2-BKS400-05.starhubgo.com:443",
    "MH-BKS400-07.starhubgo.com:443",
    # "bks03.starhubgo.com",
    "mh-bks400-06.starhubgo.com",
    "SH-BKS400-11.starhubgo.com:443",
    "RCG-BKS400-06.starhubgo.com:443",
    "sh-bks400-08.starhubgo.com:443",
]


CHANNELS = {
    "FIFAWCCh1": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/FIFAWCCh1/output/manifest.mpd",
    },
    "FIFAWCCh2": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/FIFAWCCh2/output/manifest.mpd",
    },
    "Preview": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Preview/output/manifest.mpd",
    },
    "HubECityHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubECityHD/output/manifest.mpd",
    },
    "CinemaOne": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CinemaOne/output/manifest.mpd",
    },
    "HubSports1HDnew1": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports1HDnew1/output/manifest.mpd",
    },
    "HubSports2HD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports2HD/output/manifest.mpd",
    },
    "HubSports3HDNEW": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports3HDNEW/output/manifest.mpd",
    },
    "HubSports4HDnew": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports4HDnew/output/manifest.mpd",
    },
    "HubSports5HD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports5HD/output/manifest.mpd",
    },
    "HubSports6": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports6/output/manifest.mpd",
    },
    "HubSports7": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports7/output/manifest.mpd",
    },
    "HubSports8": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubSports8/output/manifest.mpd",
    },
    "SPOTVNEW": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/SPOTVNEW/output/manifest.mpd",
    },
    "SPOTV2NEW": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/SPOTV2NEW/output/manifest.mpd",
    },
    "FightSportsHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/FightSportsHD/output/manifest.mpd",
    },
    "beINSportsHD2": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/beINSportsHD2/output/manifest.mpd",
    },
    "BeINSportsHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BeINSportsHD/output/manifest.mpd",
    },
    "beINSports3NEW": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/beINSports3NEW/output/manifest.mpd",
    },
    "beINSports4": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/beINSports4/output/manifest.mpd",
    },
    "beINSports5": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/beINSports5/output/manifest.mpd",
    },
    "HubPremier1": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier1/output/manifest.mpd",
    },
    "HubPremier12": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier12/output/manifest.mpd",
    },
    "HubPremier2_4K": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier2_4K/output/manifest.mpd",
    },
    "HubPremier3": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier3/output/manifest.mpd",
    },
    "HubPremier4": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier4/output/manifest.mpd",
    },
    "HubPremier5": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier5/output/manifest.mpd",
    },
    "HubPremier6": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier6/output/manifest.mpd",
    },
    "HubPremier7": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier7/output/manifest.mpd",
    },
    "HubPremier8": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubPremier8/output/manifest.mpd",
    },
    "CbeebiesHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CbeebiesHD/output/manifest.mpd",
    },
    "NickJr": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/NickJr/output/manifest.mpd",
    },
    "DreamworksHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/DreamworksHD/output/manifest.mpd",
    },
    "NickelodeonHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/NickelodeonHD/output/manifest.mpd",
    },
    "CartoonNetwork": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CartoonNetwork/output/manifest.mpd",
    },
    "BoomerangHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BoomerangHD/output/manifest.mpd",
    },
    "HistoryHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HistoryHD/output/manifest.mpd",
    },
    "CrimeplusInvestigationHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CrimeplusInvestigationHD/output/manifest.mpd",
    },
    "BBCEarthHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BBCEarthHD/output/manifest.mpd",
    },
    "DiscoveryCh": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/DiscoveryCh/output/manifest.mpd",
    },
    "TravelxpHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/TravelxpHD/output/manifest.mpd",
    },
    "BBCLifestyleHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BBCLifestyleHD/output/manifest.mpd",
    },
    "HGTV": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HGTV/output/manifest.mpd",
    },
    "FashionTV": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/FashionTV/output/manifest.mpd",
    },
    "ABCAustralia": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/ABCAustralia/output/manifest.mpd",
    },
    "BlueAntEntertainmentHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BlueAntEntertainmentHD/output/manifest.mpd",
    },
    "AXNHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/AXNHD/output/manifest.mpd",
    },
    "HitsMoviesHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HitsMoviesHD/output/manifest.mpd",
    },
    "LifetimeHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/LifetimeHD/output/manifest.mpd",
    },
    "HITSHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HITSHD/output/manifest.mpd",
    },
    "AnimaxHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/AnimaxHD/output/manifest.mpd",
    },
    "HBOHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HBOHD/output/manifest.mpd",
    },
    "HBOSignatureHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HBOSignatureHD/output/manifest.mpd",
    },
    "HBOFamilyHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HBOFamilyHD/output/manifest.mpd",
    },
    "HBOHitsHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HBOHitsHD/output/manifest.mpd",
    },
    "CinemaxHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CinemaxHD/output/manifest.mpd",
    },
    "BBCWorldNewsHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BBCWorldNewsHD/output/manifest.mpd",
    },
    "Quicktake": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Quicktake/output/manifest.mpd",
    },
    "FNCHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/FNCHD/output/manifest.mpd",
    },
    "SkyNewsHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/SkyNewsHD/output/manifest.mpd",
    },
    "SEAToday": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/SEAToday/output/manifest.mpd",
    },
    "Euronews": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Euronews/output/manifest.mpd",
    },
    "CNBCHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CNBCHD/output/manifest.mpd",
    },
    "BloombergTelevisionHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/BloombergTelevisionHD/output/manifest.mpd",
    },
    "CNNHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CNNHD/output/manifest.mpd",
    },
    "Mediacorp_CNA_DASH": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Mediacorp_CNA_DASH/output/manifest.mpd",
    },
    "CGTN": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CGTN/output/manifest.mpd",
    },
    "France24": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/France24/output/manifest.mpd",
    },
    "CCTV4": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CCTV4/output/manifest.mpd",
    },
    "CTITVHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CTITVHD/output/manifest.mpd",
    },
    "Mediacorp_CH5_DASH": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Mediacorp_CH5_DASH/output/manifest.mpd",
    },
    "Mediacorp_CH8_DASH": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Mediacorp_CH8_DASH/output/manifest.mpd",
    },
    "Mediacorp_CHU_DASH": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/Mediacorp_CHU_DASH/output/manifest.mpd",
    },
    "PCCHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/PCCHD/output/manifest.mpd",
    },
    "PINCHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/PINCHD/output/manifest.mpd",
    },
    "TVBSNews": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/TVBSNews/output/manifest.mpd",
    },
    "NHKWORLDJAPAN": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/NHKWORLDJAPAN/output/manifest.mpd",
    },
    "KBSWorldHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/KBSWorldHD/output/manifest.mpd",
    },
    "ArirangTV": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/ArirangTV/output/manifest.mpd",
    },
    "ONEHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/ONEHD/output/manifest.mpd",
    },
    "HubECityHD825": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubECityHD825/output/manifest.mpd",
    },
    "TVBSAsia": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/TVBSAsia/output/manifest.mpd",
    },
    "DragonTV": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/DragonTV/output/manifest.mpd",
    },
    "ETTVHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/ETTVHD/output/manifest.mpd",
    },
    "TVBJadeHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/TVBJadeHD/output/manifest.mpd",
    },
    "HubVVDramaHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/HubVVDramaHD/output/manifest.mpd",
    },
    "TVBXingHeChannel": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/TVBXingHeChannel/output/manifest.mpd",
    },
    "CelestialMoviesHD": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CelestialMoviesHD/output/manifest.mpd",
    },
    "CCM": {
        "manifest_url": "https://ucdn.starhubgo.com/bpk-tv/CCM/output/manifest.mpd",
    },
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

UPSTREAM_HEADERS = {}
MAX_RESOLVE_ATTEMPTS = 3
STARHUB_UPSTREAM_TIMEOUT = 20.0
# StarHub's CDN performs TLS fingerprinting, so impersonate a real browser.
UPSTREAM_IMPERSONATE = "chrome"


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_public_error_message(exc):
    if isinstance(exc, HTTPException):
        if exc.status_code >= 500:
            return "Internal server error"
        return str(exc.detail or "Request failed")
    if isinstance(exc, CurlTimeout):
        return "Upstream request timed out"
    if isinstance(exc, CurlConnectionError):
        return "Upstream connection failed"
    if isinstance(exc, CurlRequestException):
        response = getattr(exc, "response", None)
        status_code = response.status_code if response is not None else 502
        if status_code == 404:
            return "Channel not found"
        if status_code == 403:
            return "Upstream access denied"
        if 400 <= status_code < 500:
            return "Upstream request failed"
        return "Upstream service error"
    return "Internal server error"


def build_stream_response(success, status_code, message, **extra):
    payload = {
        "success": bool(success),
        "status_code": int(status_code),
        "message": str(message or "").strip(),
        "service": "starhub-manifest-proxy",
    }
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    return payload


def detect_stream_type(url: str) -> str:
    value = str(url or "").strip().lower().split("?", 1)[0]
    if value.endswith(".mpd"):
        return "dash"
    if value.endswith(".m3u8"):
        return "hls"
    return ""


def rewrite_stream_url_with_random_cdn(url: str) -> str:
    normalized = str(url or "").strip()
    if not normalized:
        return ""
    parsed = urlparse(normalized)
    if not parsed.scheme or not parsed.netloc:
        return normalized
    selected_cdn = random.choice(STARHUB_CDNS)
    return parsed._replace(netloc=selected_cdn).geturl()


def has_tokenized_url(url):
    normalized = str(url or "").strip()
    return "/bpk-token/" in normalized and "bkm-query" in normalized


def extract_bpk_token(url):
    normalized = str(url or "").strip()
    if not normalized:
        return ""

    parsed = urlparse(normalized)
    parts = [part for part in parsed.path.split("/") if part]
    try:
        token_index = parts.index("bpk-token") + 1
    except ValueError:
        token_index = -1
    if 0 <= token_index < len(parts):
        return parts[token_index]
    return ""


def extract_tokenized_stream_url(response):
    candidates = [str(getattr(response, "url", "") or "").strip()]
    for item in getattr(response, "history", []) or []:
        candidates.append(str(getattr(item, "url", "") or "").strip())
        location = (
            item.headers.get("location") or item.headers.get("Location") or ""
        ).strip()
        if location:
            candidates.append(location)
    final_location = (
        response.headers.get("location") or response.headers.get("Location") or ""
    ).strip()
    if final_location:
        candidates.append(final_location)

    for candidate in candidates:
        if candidate and has_tokenized_url(candidate):
            return candidate
    return ""


async def resolve_stream_url(channel_key):
    return await resolve_stream_url_with_proxy(channel_key, PROXY_URL)


async def resolve_stream_url_with_proxy(channel_key, upstream_proxy):
    manifest_url = CHANNELS[channel_key]["manifest_url"]
    logger.info(
        "Resolving StarHub stream | channel_key=%s | manifest_url=%s | proxy=%s",
        channel_key,
        manifest_url,
        upstream_proxy or "DIRECT",
    )

    async with AsyncSession(
        proxy=upstream_proxy or None,
        allow_redirects=True,
        timeout=STARHUB_UPSTREAM_TIMEOUT,
        verify=True,
        impersonate=UPSTREAM_IMPERSONATE,
    ) as client:
        response = await client.get(
            manifest_url,
        )

    tokenized_url = extract_tokenized_stream_url(response)
    logger.info(
        "StarHub upstream response | channel_key=%s | status=%s | response_url=%s | tokenized_url=%s",
        channel_key,
        response.status_code,
        response.url,
        tokenized_url,
    )

    if response.status_code >= 400:
        response.raise_for_status()

    if not tokenized_url:
        raise RuntimeError("Upstream response did not yield tokenized stream URL")

    rewritten_location = rewrite_stream_url_with_random_cdn(tokenized_url)
    logger.info(
        "Resolved StarHub stream | channel_key=%s | stream_url=%s | rewritten_stream_url=%s | bpk_token=%s",
        channel_key,
        tokenized_url,
        rewritten_location,
        extract_bpk_token(rewritten_location or tokenized_url),
    )
    return rewritten_location or tokenized_url


class StarHubManifestProxy:
    async def resolve_manifest_url(self, channel_id, upstream_proxy=PROXY_URL):
        target_channel_id = str(channel_id or "").strip()
        if not target_channel_id:
            raise HTTPException(status_code=400, detail="Missing channel_id")
        if target_channel_id not in CHANNELS:
            raise HTTPException(status_code=404, detail="Unknown channel")
        stream_url = await resolve_stream_url_with_proxy(target_channel_id, upstream_proxy)
        logger.info(
            "Manifest resolved | channel_id=%s | proxy=%s",
            target_channel_id,
            upstream_proxy or "DIRECT",
        )
        return stream_url


proxy = StarHubManifestProxy()


async def root(_request: Request):
    return JSONResponse(
        build_stream_response(
            success=True,
            status_code=200,
            message="starhub-manifest-proxy ready",
            endpoints={
                "get_stream": f"{ROUTE_PREFIX}/get-stream?channel_id=beINSports5",
                "manifest_redirect": "/FIFAWCCh1/index.mpd",
            },
        ),
        headers=CORS_HEADERS,
    )


async def get_stream(request: Request):
    if request.method == "OPTIONS":
        return Response("", headers=CORS_HEADERS)

    channel_id = (
        request.query_params.get("channel_id")
        or request.query_params.get("channel_key")
        or ""
    ).strip()
    if not channel_id:
        return JSONResponse(
            build_stream_response(
                success=False, status_code=400, message="Missing channel_id query param"
            ),
            status_code=400,
            headers=CORS_HEADERS,
        )

    try:
        last_http_error = None
        stream_url = ""

        for attempt in range(1, MAX_RESOLVE_ATTEMPTS + 1):
            try:
                stream_url = await proxy.resolve_manifest_url(channel_id, upstream_proxy=PROXY_URL)
                break
            except CurlHTTPError as exc:
                last_http_error = exc
                response = getattr(exc, "response", None)
                status_code = response.status_code if response is not None else 0
                if status_code == 403 and attempt < MAX_RESOLVE_ATTEMPTS:
                    logger.warning(
                        "StarHub resolve retry triggered | channel_id=%s | status=%s | attempt=%d/%d",
                        channel_id,
                        status_code,
                        attempt,
                        MAX_RESOLVE_ATTEMPTS,
                    )
                    continue
                raise

        if not stream_url and last_http_error is not None:
            raise last_http_error

        return JSONResponse(
            build_stream_response(
                success=True,
                status_code=200,
                message="Stream resolved",
                channel_id=channel_id,
                stream_url=stream_url,
                stream_keys="",
                event_name="",
                source_name="StarHub",
                stream_type=detect_stream_type(stream_url),
                redir_url=stream_url,
            ),
            headers=CORS_HEADERS,
        )
    except HTTPException as exc:
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=exc.status_code,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=exc.status_code,
            headers=CORS_HEADERS,
        )
    except CurlHTTPError as exc:
        response = getattr(exc, "response", None)
        status_code = response.status_code if response is not None else 502
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=status_code,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=status_code,
            headers=CORS_HEADERS,
        )
    except Exception as exc:
        logger.exception("Unhandled get_stream failure | channel_id=%s", channel_id)
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=500,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=500,
            headers=CORS_HEADERS,
        )


async def resolve_channel_stream(channel_id: str) -> str:
    """Resolve a channel with the same retry behavior as the JSON endpoint."""
    last_http_error = None
    stream_url = ""

    for attempt in range(1, MAX_RESOLVE_ATTEMPTS + 1):
        try:
            stream_url = await proxy.resolve_manifest_url(
                channel_id,
                upstream_proxy=PROXY_URL,
            )
            break
        except CurlHTTPError as exc:
            last_http_error = exc
            response = getattr(exc, "response", None)
            status_code = response.status_code if response is not None else 0
            if status_code == 403 and attempt < MAX_RESOLVE_ATTEMPTS:
                logger.warning(
                    "StarHub redirect retry triggered | channel_id=%s | status=%s | attempt=%d/%d",
                    channel_id,
                    status_code,
                    attempt,
                    MAX_RESOLVE_ATTEMPTS,
                )
                continue
            raise

    if not stream_url and last_http_error is not None:
        raise last_http_error
    return stream_url


async def channel_manifest_redirect(request: Request):
    """Resolve a channel's current MPD and redirect the client to it."""
    if request.method == "OPTIONS":
        return Response("", headers=CORS_HEADERS)
    channel_id = str(request.path_params.get("channel_id") or "").strip()

    try:
        stream_url = await resolve_channel_stream(channel_id)
        if detect_stream_type(stream_url) != "dash":
            raise HTTPException(status_code=502, detail="Resolved stream is not an MPD")

        # Upstream stream URLs contain short-lived tokens and must not be cached.
        return RedirectResponse(
            stream_url,
            status_code=307,
            headers={**CORS_HEADERS, "Cache-Control": "no-store"},
        )
    except HTTPException as exc:
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=exc.status_code,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=exc.status_code,
            headers=CORS_HEADERS,
        )
    except CurlHTTPError as exc:
        response = getattr(exc, "response", None)
        status_code = response.status_code if response is not None else 502
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=status_code,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=status_code,
            headers=CORS_HEADERS,
        )
    except Exception as exc:
        logger.exception(
            "Unhandled channel manifest redirect failure | channel_id=%s",
            channel_id,
        )
        return JSONResponse(
            build_stream_response(
                success=False,
                status_code=500,
                message=build_public_error_message(exc),
                channel_id=channel_id,
            ),
            status_code=500,
            headers=CORS_HEADERS,
        )


@asynccontextmanager
async def lifespan(_app: Starlette):
    logger.info("Starting starhub-manifest-proxy")
    logger.info("Configured proxy | proxy=%s", PROXY_URL)
    yield
    logger.info("Stopped starhub-manifest-proxy")


group_routes = [
    Route("/get-stream", get_stream, methods=["GET", "OPTIONS"]),
    Route("/{channel_id}/index.mpd", channel_manifest_redirect, methods=["GET"]),
]

routes = [
    Route("/bpk-tv/{channel_id}/output/manifest.mpd", channel_manifest_redirect, methods=["GET", "OPTIONS"]),
    Route("/", root, methods=["GET"]),
    Route("/{channel_id}/index.mpd", channel_manifest_redirect, methods=["GET"]),
    Mount(ROUTE_PREFIX, routes=group_routes),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, lifespan=lifespan, middleware=middleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7861)
