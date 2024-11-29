from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger
from config import settings, Settings
from database import db
from domains.base_exception import BaseHTTPException
from routers import user, buyer, farmer
from utils.handlers import base_http_exception_handler


# Create an instance of the FastAPI app
app = FastAPI()

# Configure CORS before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    await db.startup()


@app.on_event("shutdown")
async def shutdown_event():
    await db.shutdown()

app.add_exception_handler(BaseHTTPException, handler=base_http_exception_handler) # type: ignore

# Include routers
app.include_router(user.router)
app.include_router(buyer.router)
app.include_router(farmer.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info("Starting the app")
    logger.info("Settings:", settings)
