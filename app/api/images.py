# POST/images
import os
import uuid
import requests
from fastapi import HTTPException, APIRouter
from app.core.openai_client import client
from app.core.schemas import ImageIn

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/")
async def generate_image(payload: ImageIn):
    """Generate image using gpt-image-1"""

    try:
        # OpenAI Images API - optimized
        response = await client.images.generate(
            model="gpt-image-1",
            prompt=payload.prompt,
            n=1,
            size=payload.size,
            quality="standard",
            style="natural",
            background="transparent" if payload.transparent else "white"
        )

        # Download image
        download_url = response.data[0].url
        img_response = requests.get(download_url)
        img_response.raise_for_status()

        # Save image
        img_id = str(uuid.uuid4())
        filename = f"image_{img_id}.png"
        filepath = f"storage/{filename}"

        os.makedirs("storage", exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(img_response.content)

        return {
            "image_id": str(uuid.uuid4()),
            "filename": f"/static/{filename}",
            "prompt": payload.prompt,
            "size": payload.size,
        }
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download image: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating image: {str(e)}"
        )