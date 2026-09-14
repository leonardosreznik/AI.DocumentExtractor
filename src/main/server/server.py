from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.main.routes.health import health_routes
from src.main.routes.documents import documents_routes

app = FastAPI(
    title="AI Document Extractor",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=False
)

app.include_router(health_routes)
app.include_router(documents_routes)