from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger
from config import settings, Settings
from database import db
from domains.base_exception import BaseHTTPException
from models import User, Buyer, Farmer
from routers import user, buyer, farmer
from sqladmin import Admin, ModelView
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


admin = Admin(app, db.engine)

class UserAdmin(ModelView, model=User):
    column_list = [User.uuid, User.email, User.role, User.created_at]

class BuyerAdmin(ModelView, model=Buyer):
    column_list = [Buyer.uuid, Buyer.delivery_address, Buyer.user_uuid]

class FarmerAdmin(ModelView, model=Farmer):
    column_list = [Farmer.uuid, Farmer.government_issued_id, Farmer.farm_address]

admin.add_view(UserAdmin)
admin.add_view(BuyerAdmin)
admin.add_view(FarmerAdmin)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info("Starting the app")
    logger.info("Settings:", settings)
