from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import torch
from PIL import Image
from io import BytesIO
# from diffusers import StableDiffusionUpscalePipeline
from diffusers.pipelines.latent_diffusion.pipeline_latent_diffusion_superresolution import LDMSuperResolutionPipeline
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()
MAX_IMG_SIZE = int(os.getenv("MAX_IMG_SIZE"))

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f'device: {device}')
model_id = "CompVis/ldm-super-resolution-4x-openimages"
# model_id = "stabilityai/stable-diffusion-x4-upscaler"

# Загружаем модель и планировщик
pipeline = LDMSuperResolutionPipeline.from_pretrained(model_id)
pipeline = pipeline.to(device)


class DesktopUpscaler:
    def resize_image(self, image, max_size):
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height

        if original_width > max_size or original_height > max_size:
            if aspect_ratio > 1:
                new_width = max_size
                new_height = int(max_size / aspect_ratio)
            else:
                new_width = int(max_size * aspect_ratio)
                new_height = max_size

            image = image.resize((new_width, new_height), Image.LANCZOS)
    
        return image

    def load_and_resize_image(self, image):        
        image = self.resize_image(image, MAX_IMG_SIZE)
        return image
 
    def upscale_image(self, image, pipeline=pipeline):
        low_res_img = self.load_and_resize_image(image)
        upscaled_image = pipeline(low_res_img, num_inference_steps=50, eta=1).images[0]
        return upscaled_image


@app.post("/upscale/")
async def upscale(file: UploadFile = File(...)):
    image_stream = BytesIO(await file.read())
    image = Image.open(image_stream)

    desktop_upscaler = DesktopUpscaler()
    new_image = desktop_upscaler.upscale_image(image, pipeline)

    byte_arr = BytesIO()
    new_image.save(byte_arr, format='JPEG')
    byte_arr.seek(0)

    return StreamingResponse(byte_arr, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("UPSCALE_PORT")))
