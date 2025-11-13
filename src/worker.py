import asyncio
import json
import time
import structlog

from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, Any

from core.config import settings
from core.multi_comfyui_api import MultiComfyUiAPI
from core.redis import redis
from utils.sms import send_sms_download_message
from utils.s3 import upload_fileobj, create_presigned_download, download_file


log = structlog.get_logger()


class Worker:

    def __init__(self, server_list):

        self.api = MultiComfyUiAPI(
            server_list,
            settings.IMAGE_TEMP_FOLDER,
            settings.WORKFLOW_PATH,
            settings.WORKFLOW_NODE_ID_KSAMPLER,
            settings.WORKFLOW_NODE_ID_IMAGE_LOAD,
            settings.WORKFLOW_NODE_ID_TEXT_INPUT
        )
        self.queued_jobs: Dict[str, Dict[str, Any]] = {}
        self.servers_in_use = set()
        self.redis = redis

    def _get_api_for_job(self, workflow_path: Optional[str] = None) -> MultiComfyUiAPI:
        """
        Retorna a instância padrão (ENV WORKFLOW_PATH) ou uma instância com workflow_path customizado.
        """
        if workflow_path:
            return MultiComfyUiAPI(
                self.api.server_address_list,
                self.api.img_temp_folder,
                workflow_path,
                self.api.node_id_ksampler,
                self.api.node_id_image_load,
                self.api.node_id_text_input
            )
        return self.api

    def get_earliest_job(self, queued_jobs: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """
        Retorna o job_id com menor created_at (ISO string).
        """
        min_date = None
        min_job_id = None
        for v in queued_jobs.values():
            date = v.get("created_at") or ""
            if not min_date or date < min_date:
                min_date = date
                min_job_id = v.get("job_id")
        return min_job_id

    async def process_one_job(self, server_address, request_id, input_path, workflow_path: Optional[str]):
        log.info("worker.job_popped", server_address=server_address, request_id=request_id, input_path=input_path)

        attempt = int(await self.redis.hget(f"job:{request_id}", "attempt") or "1")

        # marca como processing
        now = datetime.utcnow().isoformat()
        await self.redis.hset(
            f"job:{request_id}",
            mapping={
                "status": "processing",
                "percent": "0",
                "step": "0",
                "max": "0",
                "node": "",
                "queue_remaining": "-1",
                "proc_start_at": now,
                "server": server_address,
            }
        )

        # obtém imagem de entrada (S3 ou local)
        try:
            log.debug("worker.download_input.start", request_id=request_id, key=input_path)
            body = download_file(input_path)
            if not body:
                raise RuntimeError("empty body from download_file")
            log.debug("worker.download_input.ok", size=len(body))
        except Exception as e:
            err = f"download_input_failed: {e}"
            log.error("worker.download_input.error", request_id=request_id, error=err)
            await self.redis.hset(f"job:{request_id}", mapping={"status": "failed", "error": err})
            return

        bio = BytesIO(body)

        # seleciona API (workflow_path None => padrão do .env)
        api = self._get_api_for_job(workflow_path if workflow_path else None)
        await self.redis.hset(f"job:{request_id}", mapping={"server": server_address})

        # executa geração com timeout duro
        start = time.time()
        try:
            log.info(
                "worker.generate.start",
                server=server_address,
                workflow_path=(workflow_path or settings.WORKFLOW_PATH)
            )
            # roda em thread com timeout — usando upload interno da API
            loop = asyncio.get_running_loop()
            fut = loop.run_in_executor(None, api.generate_image_buffer_from_bytes, server_address, bio)
            out = await asyncio.wait_for(fut, timeout=180)
            log.info("worker.generate.ok")
        except asyncio.TimeoutError:
            err = "comfyui_timeout_while_generating"
            log.error("worker.generate.timeout", request_id=request_id)
            await self.redis.hset(f"job:{request_id}", mapping={"status": "failed", "error": err})
            return
        except Exception as e:
            err = f"generate_error: {e}"
            log.error("worker.generate.error", request_id=request_id, error=err)
            await self.redis.hset(f"job:{request_id}", mapping={"status": "failed", "error": err})
            return

        # volta o ponteiro pra leitura
        try:
            out.seek(0)

            # envia a saída para o armazenamento configurado
            s3_key = upload_fileobj(out, key_prefix=f"output/{request_id}")
            image_url = create_presigned_download(s3_key, expires_in=86400)
            log.info("worker.uploaded_storage", request_id=request_id, key=s3_key)
        except Exception as e:
            err = f"upload_output_failed: {e}"
            log.error("worker.upload.error", request_id=request_id, error=err)
            await self.redis.hset(f"job:{request_id}", mapping={"status": "failed", "error": err})
            return

        duration = time.time() - start
        log.info("worker.job_done", request_id=request_id, duration=duration)

        await self.redis.hset(
            f"job:{request_id}",
            mapping={
                "percent": "100",
                "step": str(max(int(await self.redis.hget(f'job:{request_id}', 'max') or 0), int(await self.redis.hget(f'job:{request_id}', 'step') or 0))),
            }
        )

        # atualiza média móvel
        prev_avg = float(await self.redis.get("avg_processing_time") or duration)
        new_avg = prev_avg * 0.8 + duration * 0.2
        await self.redis.set("avg_processing_time", new_avg)
        log.info("worker.avg_updated", new_avg=new_avg)

        # grava resultado final
        await self.redis.hset(f"job:{request_id}", mapping={"status": "done", "output": image_url})
        log.info("worker.job_finished", request_id=request_id, image_url=image_url)

        # se tiver telefone, manda SMS síncrono
        phone = await self.redis.hget(f"job:{request_id}", "phone")
        if phone:
            download_url = f"{settings.BASE_URL}/download?image_id={request_id}"
            sent = send_sms_download_message(download_url, phone)
            await self.redis.hset(f"job:{request_id}", "sms_status", "sent" if sent else "failed")
            log.info("worker.sms_sent", request_id=request_id, phone=phone, success=sent)
        else:
            log.info("worker.no_phone", request_id=request_id)


    async def check_for_new_jobs(self):
        """
        Move itens da 'submissions_queue' (lista) para hashes 'job:{id}' normalizados.
        Evita serializar None como "None". Usa 'enqueued_at' como timestamp de ordenação.
        """
        while True:
            raw = await self.redis.rpop("submissions_queue")
            if raw is None:
                break

            job = json.loads(raw)
            request_id = job["id"]
            input_path = job["input"]
            workflow_path = job.get("workflow_path")  # pode estar ausente

            now = datetime.utcnow().isoformat()
            job_key = f"job:{request_id}"

            mapping = {
                "status": "queued",
                "input": input_path,
                "attempt": "1",
                "enqueued_at": now,
            }
            if workflow_path:
                mapping["workflow_path"] = workflow_path

            await self.redis.hset(job_key, mapping=mapping)

    async def process_jobs(self):
        """
        Carrega jobs do Redis e popula a fila interna self.queued_jobs,
        lida com retries, timeouts e servidores em uso.
        Robusta a respostas em bytes (quando decode_responses não está ativo).
        """
        def _normalize(val):
            if isinstance(val, bytes):
                try:
                    return val.decode("utf-8")
                except Exception:
                    return str(val)
            return val

        def _normalize_dict(d):
            return { _normalize(k): _normalize(v) for k, v in d.items() }

        matching_statuses = {"processing", "queued", "failed"}
        self.servers_in_use.clear()

        async for key in self.redis.scan_iter("job:*"):
            job_data = await self.redis.hgetall(key)
            # normaliza possiveis bytes
            job_data = _normalize_dict(job_data)
            status = job_data.get("status", "")
            request_id = key.split("job:", 1)[-1]

            log.debug(f"Job ID: {key}")
            for k, v in job_data.items():
                log.debug(f"  {k}: {v}")

            if status not in matching_statuses:
                # se não tem status, não processa
                continue

            if status == "queued":
                if request_id not in self.queued_jobs:
                    enq = job_data.get("enqueued_at", "")
                    input_path = job_data.get("input", "")
                    workflow_path = job_data.get("workflow_path") or None
                    self.queued_jobs[request_id] = {
                        "job_id": request_id,
                        "created_at": enq,           # usado por get_earliest_job
                        "input": input_path,
                        "workflow_path": workflow_path,
                    }

            elif status == "failed":
                attempt = int(job_data.get("attempt", "1")) + 1
                if attempt <= 3:
                    await self.redis.hset(
                        f"job:{request_id}",
                        mapping={"status": "queued", "attempt": str(attempt)}
                    )
                else:
                    await self.redis.hset(f"job:{request_id}", mapping={"status": "error"})

            elif status == "processing":
                server = job_data.get("server", "")
                if server:
                    self.servers_in_use.add(server)
                proc_start_at = job_data.get("proc_start_at", "")
                # se estiver vazio, usa agora para que duration seja zero
                try:
                    dt_proc_start_at = datetime.fromisoformat(proc_start_at) if proc_start_at else datetime.utcnow()
                except Exception:
                    dt_proc_start_at = datetime.utcnow()
                duration = datetime.utcnow() - dt_proc_start_at
                if duration.total_seconds() > 300:
                    await self.redis.hset(
                        f"job:{request_id}",
                        mapping={"status": "failed", "error": "Timeout while processing"},
                    )
            log.debug("job.status", job_id=request_id, status=status)

            log.debug("-" * 40)

    async def activate_queued_jobs(self):
        """
        Escolhe o job mais antigo e ativa em um servidor disponível.
        """
        earliest_job_id = self.get_earliest_job(self.queued_jobs)
        if not earliest_job_id:
            return

        available_servers = await self.api.get_available_server_addresses()

        for available_server in available_servers:
            if available_server in self.servers_in_use:
                continue

            earliest_job_id = self.get_earliest_job(self.queued_jobs)
            if earliest_job_id:
                earliest = self.queued_jobs[earliest_job_id]
                request_id = earliest["job_id"]
                input_path = earliest["input"]
                workflow_path = earliest.get("workflow_path")
                log.info(
                    f"Found job to start (earliest_job_id: '{earliest_job_id}', "
                    f"request_id:'{request_id}', input_path:'{input_path}', workflow_path:'{workflow_path}')"
                )

                if not input_path:
                    log.warning(f"Input path is empty - request_id:'{request_id}'")
                    self.queued_jobs.pop(request_id, None)
                    await self.redis.hset(
                        f"job:{request_id}",
                        mapping={"status": "error", "error": "No input path"}
                    )
                    continue

                log.debug(f"Process Job: {request_id} - {input_path}")
                self.queued_jobs.pop(request_id, None)

                # dispara processamento
                asyncio.create_task(self.process_one_job(available_server, request_id, input_path, workflow_path))
            else:
                break

    async def worker_loop(self):
        """
        Loop infinito que consome jobs da fila 'submissions_queue' no Redis,
        processa cada um sequencialmente, atualiza métricas e envia SMS quando
        o usuário tiver registrado um telefone.
        """
        while True:
            log.debug("sleep")
            await asyncio.sleep(0.5)

            # verifica se tem novos jobs
            log.debug("check_for_new_jobs")
            await self.check_for_new_jobs()

            log.debug("process_jobs")
            await self.process_jobs()

            log.debug("activate_queued_jobs")
            await self.activate_queued_jobs()

            log.debug("=" * 40)


if __name__ == "__main__":
    """
    Inicia o worker_loop em paralelo ao servidor.
    """
    server_list = [
        settings.COMFYUI_API_SERVER1,
        settings.COMFYUI_API_SERVER2,
        settings.COMFYUI_API_SERVER3,
        settings.COMFYUI_API_SERVER4,
    ]
    # filtra vazios
    server_list = [s for s in server_list if s]

    worker = Worker(server_list)
    log.info("worker.startup", servers=server_list)
    asyncio.run(worker.worker_loop())
