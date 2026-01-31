import os
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image(image_path):
    result = cloudinary.uploader.upload(
        image_path,
        resource_type="image",
        folder="news-4-you"
    )
    return result["secure_url"]
