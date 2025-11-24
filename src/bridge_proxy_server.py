import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("async_bridge_proxy")
TREZORD_HOST = "http://0.0.0.0:21325"
PORT = 21326

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track in-flight upstream tasks per session id to allow cancelling previous read when a new call arrives
inflight_tasks: dict[str, asyncio.Task] = {}
inflight_lock = asyncio.Lock()


def _prepare_response_headers(
    resp: httpx.Response, request: Request, remove_content_length: bool = False
) -> dict:
    """Return a headers dict for returning to the client.

    - Copies upstream headers
    - Removes Transfer-Encoding always
    - Optionally removes Content-Length (for chunked/streaming responses)
    """
    headers = dict(resp.headers)
    headers.pop("transfer-encoding", None)
    if remove_content_length:
        headers.pop("content-length", None)
    return headers


def _prepare_upstream_headers(request: Request) -> dict:
    """Prepare headers for forwarding to upstream, replacing Origin and removing host."""
    # Build headers dict, excluding 'host' and case-insensitive 'origin'
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in ("host", "origin")
    }
    # Set Origin header from request or use default
    headers["Origin"] = request.headers.get("origin", "https://user-env.trezor.io")
    return headers


def _create_response_from_upstream(resp: httpx.Response, request: Request) -> Response:
    """Create a Response object from an upstream httpx.Response with proper logging."""
    logger.info(f"Upstream responded with status: {resp.status_code}")
    logger.info(f"Upstream headers: {dict(resp.headers)}")
    headers = _prepare_response_headers(resp, request, remove_content_length=False)
    return Response(resp.content, status_code=resp.status_code, headers=headers)


async def _cancel_previous_session_task(session_id: str | None, req_id: str):
    """Cancel any previous in-flight task for the given session."""
    if session_id is not None:
        async with inflight_lock:
            old = inflight_tasks.get(session_id)
            if old is not None:
                logger.info(
                    f"[{req_id}] Cancelling prior inflight task for session {session_id}"
                )
                old.cancel()


@asynccontextmanager
async def _manage_session_task(session_id: str | None, task: asyncio.Task):
    """Context manager to register and cleanup inflight session tasks."""
    if session_id is not None:
        async with inflight_lock:
            inflight_tasks[session_id] = task
    try:
        yield
    finally:
        task.cancel()
        if session_id is not None:
            async with inflight_lock:
                if inflight_tasks.get(session_id) is task:
                    del inflight_tasks[session_id]


async def _proxy_request(
    request: Request, path: str, session_id: str | None = None
) -> Response:
    """Proxy a request with optional session tracking."""
    url = f"{TREZORD_HOST}/{path}"
    headers = _prepare_upstream_headers(request)
    req_id = uuid.uuid4().hex[:8]
    logger.info(f"[{req_id}] Proxy received {request.method} request for path: /{path}")

    body = await request.body() if request.method == "POST" else None
    if body:
        logger.info(f"POST body length: {len(body)}")
    logger.info(f"Forwarding {request.method} to upstream: {url}")

    try:
        # Session-tracked requests (read/call): race against client disconnect
        if session_id is not None:
            await _cancel_previous_session_task(session_id, req_id)

            # Use short-lived client without keep-alive for cancellable requests
            transport = httpx.AsyncHTTPTransport(retries=0)
            async with httpx.AsyncClient(timeout=None, transport=transport) as client:
                req_task = asyncio.create_task(
                    client.request(request.method, url, headers=headers, content=body)
                )

                async with _manage_session_task(session_id, req_task):
                    # Poll with short timeouts and check client disconnect between polls
                    while True:
                        try:
                            resp = await asyncio.wait_for(
                                asyncio.shield(req_task), timeout=0.25
                            )
                            break  # upstream finished
                        except asyncio.TimeoutError:
                            if await request.is_disconnected():
                                logger.info(
                                    "Client disconnected before upstream response; cancelling upstream request"
                                )
                                try:
                                    await req_task
                                except asyncio.CancelledError:
                                    pass
                                return Response(status_code=499)

                    return _create_response_from_upstream(resp, request)
        # Simple requests: no session tracking
        else:
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.request(
                    request.method, url, headers=headers, content=body
                )
                return _create_response_from_upstream(resp, request)
    except httpx.RequestError as e:
        logger.error(f"Error proxying request: {e}")
        return JSONResponse({"error": str(e)}, status_code=502)


@app.api_route("/read/{session_id}", methods=["GET", "POST"])
async def proxy_read(request: Request, session_id: str):
    """Proxy /read requests with session tracking."""
    return await _proxy_request(request, f"read/{session_id}", session_id=session_id)


@app.api_route("/call/{session_id}", methods=["GET", "POST"])
async def proxy_call(request: Request, session_id: str):
    """Proxy /call requests with session tracking."""
    return await _proxy_request(request, f"call/{session_id}", session_id=session_id)


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_all(request: Request, path: str):
    """Proxy all other requests."""
    return await _proxy_request(request, path)


if __name__ == "__main__":
    # No reload, no workers, single process only
    uvicorn.run("bridge_proxy_server:app", host="0.0.0.0", port=PORT)
