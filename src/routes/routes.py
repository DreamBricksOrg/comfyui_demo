import structlog
import uuid
import os
import json
import asyncio
import websockets
import aiohttp

from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.config import settings
from core.redis import redis
from core.paths import DIST_DIR, WORKFLOWS_DIR
from utils.sms import format_to_e164, send_sms_download_message
from utils.s3 import upload_fileobj


router = APIRouter()
templates = Jinja2Templates(directory="src/static/templates")
log = structlog.get_logger()

class HealthResponse(BaseModel):
    status: str
    details: dict = {}

async def enqueue_job(rid: str, input_key: str, workflow_path: Optional[str] = None):
    """
    Empilha um job na fila 'submissions_queue'.
    Não serializa workflow_path=None como string "None".
    """
    payload = {"id": rid, "input": input_key}
    if workflow_path:
        payload["workflow_path"] = workflow_path
    await redis.lpush("submissions_queue", json.dumps(payload))


async def send_sms_task(request_id: str, image_url: str, phone: str):
    sent = await asyncio.to_thread(send_sms_download_message, image_url, phone)
    log.info("notify.immediate_sms", request_id=request_id, phone=phone, success=sent)
    await redis.hset(f"job:{request_id}", "sms_status", "sent" if sent else "failed")


@router.get("/")
async def read_index():
    return FileResponse(os.path.join(DIST_DIR, "index.html"))


@router.get("/alive")
async def alive():
    return HealthResponse(status="ok", details={"time": asyncio.get_event_loop().time()})


@router.get("/alive/comfyui")
async def comfyui_health():
    server_list = [
        settings.COMFYUI_API_SERVER1,
        settings.COMFYUI_API_SERVER2,
        settings.COMFYUI_API_SERVER3,
        settings.COMFYUI_API_SERVER4,
    ]
    server_list = [s for s in server_list if s]

    results = {}
    for server in server_list:
        ws_url = server.rstrip('/').replace("http://", "ws://").replace("https://", "wss://") + f"/ws?clientId={uuid.uuid4().hex}"
        try:
            async with websockets.connect(ws_url, ping_interval=10, ping_timeout=5) as ws:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg)
                except asyncio.TimeoutError:
                    data = None
                results[server] = {"status": "ok", "first_message": data}
        except Exception as e:
            results[server] = {"status": "error", "error": str(e)}

    # determina o overall status
    if all(r["status"] == "ok" for r in results.values()):
        overall = "ok"
    elif any(r["status"] == "ok" for r in results.values()):
        overall = "partial"
    else:
        overall = "error"

    return {"status": overall, "details": results}


@router.get("/image/{path:path}")
async def serve_image(path: str):
    file_path = os.path.join(settings.STATIC_DIR, path)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path)


@router.post("/api/upload")
async def upload(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
):
    if not image.filename:
        raise HTTPException(400, "Nome de arquivo inválido")

    rid = str(uuid.uuid4())
    key = f"job:{rid}"

    content = await image.read()
    bio = BytesIO(content)
    input_key = upload_fileobj(bio, key_prefix=f"input/{rid}")

    now = datetime.utcnow().isoformat()
    await redis.hset(key, mapping={
        "status": "queued",
        "input": input_key,
        "output": "",
        "attempt": "1",
        "enqueued_at": now
    })

    background_tasks.add_task(enqueue_job, rid, input_key)

    pos = await redis.llen("submissions_queue")
    avg = float(await redis.get("avg_processing_time") or 80)
    eta = int(pos) * avg

    return JSONResponse({
        "status": "QUEUED",
        "request_id": rid,
        "position_in_queue": pos,
        "estimated_wait_seconds": eta
    })


@router.get("/api/result")
async def get_result(request_id: str = Query(...)):
    key = f"job:{request_id}"
    exists = await redis.exists(key)
    if not exists:
        raise HTTPException(status_code=404, detail="Request ID não encontrado")

    data = await redis.hgetall(key)
    status = data.get("status")

    if status == "processing":
        return JSONResponse({"status": "processing"})

    if status == "error":
        return JSONResponse({"status": "error", "error": data.get("error")})

    if status == "done":
        image_url = data.get("output")
        if not image_url:
            raise HTTPException(status_code=500, detail="Imagem processada mas arquivo não encontrado")
        return JSONResponse({"status": "done", "image_url": image_url})

    # se ainda não marcou como "processing"/"done"/"error", considera em fila
    return JSONResponse({"status": "queued"})


@router.post("/api/notify")
async def register_notification(
    request_id: str = Form(...),
    phone: str = Form(...),
):
    key = f"job:{request_id}"
    if not await redis.exists(key):
        raise HTTPException(404, "Request ID não encontrado")

    formatted = format_to_e164(phone)
    await redis.hset(key, "phone", formatted)

    return JSONResponse({"status": "PHONE_REGISTERED"})


@router.get("/api/test", response_class=HTMLResponse)
async def test_form(request: Request):
    workflows = [f.name for f in WORKFLOWS_DIR.iterdir() if f.suffix == ".json"]
    return templates.TemplateResponse("test_workflow.html", {"request": request, "workflows": workflows})


@router.post("/api/test")
async def test_submit(
    background_tasks: BackgroundTasks,
    workflow: str = Form(...),
    image: UploadFile = File(...),
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="Imagem inválida")

    rid = str(uuid.uuid4())
    key = f"job:{rid}"

    content = await image.read()
    bio = BytesIO(content)
    input_key = upload_fileobj(bio, key_prefix=f"input/{rid}")
    workflow_path = f"src/workflows/{workflow}"

    now = datetime.utcnow().isoformat()
    await redis.hset(key, mapping={
        "status": "queued",
        "input": input_key,
        "output": "",
        "attempt": "1",
        "enqueued_at": now,
        "workflow_path": workflow_path
    })

    background_tasks.add_task(enqueue_job, rid, input_key, workflow_path=workflow_path)

    pos = await redis.llen("submissions_queue")
    avg = float(await redis.get("avg_processing_time") or 80)
    eta = int(pos) * avg

    return {
        "request_id": rid,
        "position": pos,
        "eta": eta
    }


@router.get("/api/test-image", response_class=HTMLResponse)
async def render_test_image(request: Request):
    return templates.TemplateResponse("test_image.html", {"request": request})

@router.get("/api/jobs/{request_id}/progress")
async def job_progress(request_id: str):
    key = f"job:{request_id}"
    data = await redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="job not found")

    def as_int(v, default=0):
        try:
            return int(v)
        except Exception:
            return default

    return {
        "job": request_id,
        "status": data.get("status", "unknown"),
        "percent": as_int(data.get("percent", "0")),
        "step": as_int(data.get("progress_value", "0")),
        "max": as_int(data.get("progress_max", "0")),
        "node": data.get("node", "") or "",
        "queue_remaining": as_int(data.get("queue_remaining", "-1")),
        "server": data.get("server", "") or "",
        "error": data.get("error", "") or "",
        "proc_start_at": data.get("proc_start_at", "") or "",
        "enqueued_at": data.get("enqueued_at", "") or "",
    }
