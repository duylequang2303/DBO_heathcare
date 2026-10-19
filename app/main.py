"""
FastAPI main application for DBO Healthcare Menu System
Serves both API endpoints and static frontend files from a single port
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="DBO Healthcare Menu API",
    description="API for generating personalized nutrition menus using IDBO solver",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api import routes, swap

app.include_router(routes.router, prefix="/api", tags=["api"])
app.include_router(swap.router, prefix="/api", tags=["swap"])

# Mount static files (frontend)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from app.api.services import get_food_db
    # Preload food database
    get_food_db()
    print("✓ Food database loaded")
    print("✓ API ready at /api")
    print("✓ Frontend ready at /")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
