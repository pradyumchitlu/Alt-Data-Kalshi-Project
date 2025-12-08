# app.py
from fastapi import FastAPI
from trends.routes import router as trends_router
from kalshi_market.routes import router as kalshi_router

app = FastAPI(title="Data Aggregation Backend")

# mount submodules
app.include_router(trends_router, prefix="/trends", tags=["Google Trends"])
app.include_router(kalshi_router, prefix="/kalshi", tags=["Kalshi Markets"])
