from fastapi import APIRouter


health_routes = APIRouter(
    tags=["Health"]
)


@health_routes.get("/health")
def health():
    return {
        "status": "ok"
    }