from enum import unique
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

mongodb_client = AsyncIOMotorClient(
    os.environ.get("PSTP-MONGO-HOST"), int(os.environ.get("PSTP-MONGO-PORT"))
).PayService_TP


async def create_index():
    await mongodb_client.orders.create_index("orderId", unique=True)
    await mongodb_client.orders_completed.create_index("orderId", unique=True)


async def insert_order_data(data):
    return await mongodb_client.orders.insert_one(data)


async def get_order_data(data):
    return await mongodb_client.orders.find_one(data)


async def insert_paid_data(data):
    return await mongodb_client.orders_completed.insert_one(data)


async def get_paid_data(data):
    return await mongodb_client.orders_completed.find_one(data)
