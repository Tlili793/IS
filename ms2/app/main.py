import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
import py_eureka_client.eureka_client as eureka_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EUREKA_SERVER_URL = os.getenv("EUREKA_SERVER_URL", "http://localhost:8761/eureka")
APP_NAME = os.getenv("EUREKA_APP_NAME", "MS2")
INSTANCE_HOST = os.getenv("EUREKA_INSTANCE_HOST", "localhost")
PORT = int(os.getenv("PORT", "8002"))


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


app = FastAPI(title="Agriculture MS2", lifespan=lifespan)


@app.get("/hello")
async def hello():
    return {"service": "ms2", "message": "Hello from MS2"}


@app.get("/health")
async def health():
    return {"status": "UP"}
