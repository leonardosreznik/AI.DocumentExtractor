from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from bson.errors import InvalidId

from src.main.dependencies import (
    get_image_storage_service,
)
from src.main.services.storage.image_storage import (
    ImageStorageService,
)


images_routes = APIRouter(
    prefix="/images",
    tags=["Images"],
)


@images_routes.get(
    "/{image_id}"
)
def get_image(
    image_id: str,
    image_storage_service: ImageStorageService = Depends(
        get_image_storage_service
    ),
):

    try:

        image = image_storage_service.get(
            image_id
        )

    except InvalidId:

        raise HTTPException(
            status_code=404,
            detail="Imagem não encontrada.",
        )

    except FileNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Imagem não encontrada.",
        )

    headers = {}

    if image.filename:

        headers["Content-Disposition"] = (
            f'inline; filename="{image.filename}"'
        )

    return Response(
        content=image.read(),
        media_type=image.content_type,
        headers=headers,
    )