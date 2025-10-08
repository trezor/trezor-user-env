import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import uuid
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("async_bridge_proxy")
TREZORD_HOST = "http://0.0.0.0:21325"
HEADERS = {
	"Origin": "https://user-env.trezor.io",
}
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()
# Middleware to add CORS headers to all responses
class CORSMiddlewareAll(BaseHTTPMiddleware):
	async def dispatch(self, request, call_next):
		response = await call_next(request)
		origin = request.headers.get("origin", "*")
		response.headers["Access-Control-Allow-Origin"] = origin
		response.headers["Access-Control-Allow-Credentials"] = "true"
		return response

app.add_middleware(CORSMiddlewareAll)

# Track in-flight upstream tasks per session id to allow cancelling previous read when a new call arrives
inflight_tasks: dict[str, asyncio.Task] = {}
inflight_lock = asyncio.Lock()


def _prepare_response_headers(resp: httpx.Response, request: Request, remove_content_length: bool = False) -> dict:
	"""Return a headers dict for returning to the client.

	- Copies upstream headers
	- Removes Transfer-Encoding always
	- Optionally removes Content-Length (for chunked/streaming responses)
	- Ensures CORS headers are set from the incoming request
	"""
	headers = dict(resp.headers)
	headers.pop("transfer-encoding", None)
	if remove_content_length:
		headers.pop("content-length", None)
	headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
	headers["Access-Control-Allow-Credentials"] = "true"
	return headers

@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
async def proxy_all(request: Request, path: str):
	if request.method == "OPTIONS":
		headers = {
			"Access-Control-Allow-Origin": request.headers.get("origin", "*"),
			"Access-Control-Allow-Methods": "GET, POST, OPTIONS",
			"Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
			"Access-Control-Allow-Credentials": "true",
			"Access-Control-Max-Age": "86400",
		}
		return Response(status_code=200, headers=headers)
	elif request.method == "GET":
		return await proxy_stream(request, "GET", path)
	elif request.method == "POST":
		return await proxy_stream(request, "POST", path)

async def proxy_stream(request: Request, method: str, path: str):
	url = f"{TREZORD_HOST}/{path}"
	headers = dict(request.headers)
	headers.pop("Origin", None)
	headers.pop("origin", None)
	headers["Origin"] = request.headers.get("origin", "https://user-env.trezor.io")
	headers.pop("host", None)
	if method != "OPTIONS":
		# Per-request id to trace cancellations across logs
		req_id = uuid.uuid4().hex[:8]
		logger.info(f"[{req_id}] Proxy received {method} request for path: /{path}")
	client = httpx.AsyncClient(timeout=None)
	try:
		req_args = dict(
			url=url,
			headers=headers,
		)
		if method == "POST":
			body = await request.body()
			logger.info(f"POST body length: {len(body)}")
			req_args["content"] = body
		logger.info(f"Forwarding {method} to upstream: {url}")

		# For /read and /call: race the upstream request against client disconnect to propagate aborts.
		is_read_or_call = path.startswith("read/") or path.startswith("call/")
		if is_read_or_call:
			# try to extract session id from path (read/<id> or call/<id>)
			session_id = None
			parts = path.split("/", 1)
			if len(parts) > 1 and parts[1].isdigit():
				session_id = parts[1]
			# cancel prior inflight task for same session if present
			if session_id is not None:
				async with inflight_lock:
					old = inflight_tasks.get(session_id)
					if old is not None and not old.done():
						logger.info(f"[{req_id}] Cancelling prior inflight task for session {session_id}")
						old.cancel()
						# leave removal to that task's finally
			# Start the upstream request as a cancellable task on a short-lived client without keep-alive to avoid connection reuse
			transport = httpx.AsyncHTTPTransport(retries=0)
			async with httpx.AsyncClient(timeout=None, transport=transport) as per_req_client:
				req_coro = per_req_client.request(method, url, headers=headers, content=req_args.get("content"))
				req_task = asyncio.create_task(req_coro)
				# register inflight
				if session_id is not None:
					async with inflight_lock:
						inflight_tasks[session_id] = req_task
				# Background monitor to cancel upstream immediately on client disconnect
				async def _monitor_disconnect():
					try:
						disconnected = await request.is_disconnected()
						if disconnected and not req_task.done():
							logger.info(f"[{req_id}] Detected client disconnect; cancelling upstream request")
							req_task.cancel()
					except asyncio.CancelledError:
						return
				monitor_task = asyncio.create_task(_monitor_disconnect())
				try:
					# Poll the upstream task with short timeouts and check client disconnect in between polls.
					# This avoids treating a completed request-body or immediate coroutine state as a client disconnect.
					while True:
						try:
							resp = await asyncio.wait_for(asyncio.shield(req_task), timeout=0.25)
							# upstream finished
							break
						except asyncio.TimeoutError:
							# timeout expired; check if client disconnected
							if await request.is_disconnected():
								logger.info("Client disconnected before upstream response; cancelling upstream request")
								req_task.cancel()
								try:
									await req_task
								except asyncio.CancelledError:
									pass
								return Response(status_code=499)
					# Upstream completed first, get response
					req_result = req_task.result()
					resp = req_result
					# cancel monitor task since upstream finished
					if not monitor_task.done():
						monitor_task.cancel()
					logger.info(f"Upstream responded with status: {resp.status_code}")
					logger.info(f"Upstream headers: {dict(resp.headers)}")
					content = resp.content
					# Use centralized header preparation helper
					response_headers = _prepare_response_headers(resp, request, remove_content_length=False)
					return Response(content, status_code=resp.status_code, headers=response_headers)
				finally:
					# cleanup tasks
					if not req_task.done():
						req_task.cancel()
					if not monitor_task.done():
						monitor_task.cancel()
					# remove inflight registration
					if session_id is not None:
						async with inflight_lock:
							cur = inflight_tasks.get(session_id)
							if cur is req_task:
								del inflight_tasks[session_id]
		elif path == "listen":
			# For /listen, use non-streaming (read full response and yield)
			resp = await client.request(method, url, headers=headers, content=req_args.get("content"))
			logger.info(f"Upstream responded with status: {resp.status_code}")
			logger.info(f"Upstream headers: {dict(resp.headers)}")
			content = resp.content
			response_headers = _prepare_response_headers(resp, request, remove_content_length=False)
			return Response(content, status_code=resp.status_code, headers=response_headers)
		else:
			resp = await client.request(method, url, headers=headers, content=req_args.get("content"))
			logger.info(f"Upstream responded with status: {resp.status_code}")
			logger.info(f"Upstream headers: {dict(resp.headers)}")
			content = resp.content
			response_headers = _prepare_response_headers(resp, request, remove_content_length=False)
			return Response(content, status_code=resp.status_code, headers=response_headers)
	except httpx.RequestError as e:
		logger.error(f"Error proxying request: {e}")
		return JSONResponse({"error": str(e)}, status_code=502)
	finally:
		await client.aclose()

if __name__ == "__main__":
	# No reload, no workers, single process only
	uvicorn.run("async_bridge_proxy_server:app", host="0.0.0.0", port=21326)
