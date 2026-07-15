import cloudinary
import cloudinary.uploader
import os

from app.core.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)

def upload_image_and_cleanup(file_path: str) -> str | None:
    try:
        response = cloudinary.uploader.upload(file_path)
        return response.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
