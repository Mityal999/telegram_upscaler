from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ContentTypes, InputMediaPhoto

from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO

import tempfile
import os


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
UPSCALE_IP = os.getenv("UPSCALE_IP")
UPSCALE_PORT = os.getenv("UPSCALE_PORT")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне изображение, и я его обработаю.")


@dp.message_handler(content_types=ContentTypes.PHOTO)
async def handle_docs_photo(message: types.Message):
    await message.reply("Произвожу апскейл...")

    highest_quality_photo = message.photo[-1]

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_info = await bot.get_file(highest_quality_photo.file_id)
            file_path = os.path.join(temp_dir, file_info.file_path.split('/')[-1])
            await bot.download_file(file_info.file_path, file_path)

            url = f'http://{UPSCALE_IP}:{UPSCALE_PORT}/upscale/'

            with open(file_path, 'rb') as img_file:
                # Обертка файла в словарь для соответствия формату multipart/form-data
                files = {'file': img_file}
                response = requests.post(url, files=files)

            if response.status_code == 200:
                processed_image = response.content

                image_stream = BytesIO(processed_image)
                image_stream.seek(0)
                pil_image = Image.open(image_stream)

                # Преобразование объекта Image обратно в файловый объект для отправки
                with BytesIO() as output:
                    pil_image.save(output, format='JPEG')
                    output.seek(0)
                    await message.reply_photo(output, caption="Вот обработанное изображение:")
            else:
                await message.reply("Произошла ошибка при обработке изображения.")
                
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)