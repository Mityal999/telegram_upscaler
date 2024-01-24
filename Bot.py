from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ContentTypes, InputMediaPhoto
# from aiogram_media_group import media_group_handler
# from aiogram_media_group.filters import MediaGroupFilter
from typing import List

from dotenv import load_dotenv

import tempfile
import os

from PIL import Image
from diffusers import LDMSuperResolutionPipeline
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "CompVis/ldm-super-resolution-4x-openimages"

# load model and scheduler
pipeline = LDMSuperResolutionPipeline.from_pretrained(model_id)
pipeline = pipeline.to(device)

from PIL import Image


def resize_image(image, max_size):
    width, height = image.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        image = image.resize((new_width, new_height), Image.ANTIALIAS)
    return image


def load_and_resize_image(file_path):
    # Загрузка изображения
    image = Image.open(file_path).convert("RGB")

    # Проверка и изменение размера, если необходимо
    max_size = 512
    image = resize_image(image, max_size)

    # Сохранение измененного изображения (если требуется)
    # image.save(new_file_path)

    return image

# Mock func
def upscale_image(image_path, pipline = pipline):
    low_res_img = load_and_resize_image(image_path)
    upscaled_image = pipeline(low_res_img, num_inference_steps=100, eta=1).images[0]
    path_split = image_path.split('.')
    path_split[-2] = path_split[-2]+'_upscaled'
    new_path = '.'.join(path_split)
    upscaled_image.save(new_path)
    return new_path

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне изображение, и я его обработаю.")



# # Обработчик альбомов
# @dp.message_handler(MediaGroupFilter(is_media_group=True), content_types=types.ContentType.PHOTO)
# @media_group_handler
# async def album_handler(messages: List[types.Message]):
#     processed_photos = []
#     for message in messages:
#         highest_quality_photo = message.photo[-1]
#         file_info = await bot.get_file(highest_quality_photo.file_id)
#         file_path = await bot.download_file(file_info.file_path)
#         processed_image_path = upscale_image(file_path)
#         processed_photos.append(InputMediaPhoto(open(processed_image_path, 'rb')))

#     await bot.send_media_group(messages[0].chat.id, processed_photos)

        

# Обработчик отдельных фотографий
@dp.message_handler(content_types=ContentTypes.PHOTO)
async def handle_docs_photo(message: types.Message):
    highest_quality_photo = message.photo[-1]

    with tempfile.TemporaryDirectory() as temp_dir:
        
        file_info = await bot.get_file(highest_quality_photo.file_id)
        file_path = os.path.join(temp_dir, file_info.file_path.split('/')[-1])
        await bot.download_file(file_info.file_path, file_path)

        processed_image_path = upscale_image(file_path)

        with open(processed_image_path, 'rb') as photo:
            await message.reply_photo(photo, caption="Вот обработанное изображение:")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
