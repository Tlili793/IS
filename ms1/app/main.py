import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
import py_eureka_client.eureka_client as eureka_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EUREKA_SERVER_URL = os.getenv("EUREKA_SERVER_URL", "http://localhost:8761/eureka")
APP_NAME = os.getenv("EUREKA_APP_NAME", "MS1")
INSTANCE_HOST = os.getenv("EUREKA_INSTANCE_HOST", "localhost")
PORT = int(os.getenv("PORT", "8001"))
MS2_APP_NAME = os.getenv("MS2_APP_NAME", "MS2")
MS2_MAX_ATTEMPTS = int(os.getenv("MS2_MAX_ATTEMPTS", "15"))


def on_eureka_error(error_type: str, error: Exception) -> None:
    logger.warning("Eureka %s error: %s", error_type, error)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await eureka_client.init_async(
            eureka_server=EUREKA_SERVER_URL,
            app_name=APP_NAME,
            instance_host=INSTANCE_HOST,
            instance_port=PORT,
            home_page_url=f"http://{INSTANCE_HOST}:{PORT}/",
            status_page_url=f"http://{INSTANCE_HOST}:{PORT}/health",
            health_check_url=f"http://{INSTANCE_HOST}:{PORT}/health",
            renewal_interval_in_secs=10,
            on_error=on_eureka_error,
        )
        logger.info("Registered %s with Eureka at %s", APP_NAME, EUREKA_SERVER_URL)
    except Exception:
        logger.exception("Could not initialize Eureka registration")

    yield

    try:
        await eureka_client.stop_async()
    except Exception:
        logger.exception("Could not stop Eureka client")


app = FastAPI(title="Agriculture MS1", lifespan=lifespan)


async def call_ms2() -> dict:
    last_error: Exception | None = None

    for attempt in range(1, MS2_MAX_ATTEMPTS + 1):
        try:
            response = await eureka_client.do_service_async(
                MS2_APP_NAME,
                "/hello",
                return_type="json",
                timeout=3,
            )
            if isinstance(response, dict):
                return response
            return {"service": "ms2", "message": str(response)}
        except Exception as error:
            last_error = error
            logger.warning(
                "Call to %s failed (attempt %s/%s): %s",
                MS2_APP_NAME,
                attempt,
                MS2_MAX_ATTEMPTS,
                error,
            )
            if attempt < MS2_MAX_ATTEMPTS:
                await asyncio.sleep(min(0.5 * attempt, 2.0))

    raise HTTPException(
        status_code=503,
        detail="MS2 is not available through Eureka",
    ) from last_error


@app.get("/hello")
async def hello():
    ms2_response = await call_ms2()
    ms2_message = ms2_response.get("message", "Hello from MS2")

    return {
        "service": "ms1",
        "message": "Hello from MS1",
        "ms2": ms2_message,
        "result": f"Hello from MS1 -> {ms2_message}",
    }


@app.get("/health")
async def health():
    return {"status": "UP"}
