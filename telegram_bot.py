from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.filters import Command
import asyncio

# Токен вашего бота
BOT_TOKEN = "8052100126:AAGBcSGUcQxYWqiDXt4Cy5WQjy0fkKpLIyo"
# Ваш Telegram ID
ADMIN_ID = 358781428

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Основное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚙ Оценка"), KeyboardButton(text="⚡ Подбор авто")]
    ],
    resize_keyboard=True
)

# Хранилище данных клиента
client_data = {}

@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Добро пожаловать! Это Бот по оценке и подбору авто. Выберите действие:", reply_markup=main_menu)

@router.message(lambda message: message.text == "⚙ Оценка")
async def evaluation(message: Message):
    await message.answer(
        "Для оценки автомобиля скиньте следующие документы и фотографии:\n"
        "1. CMR, Инвойс, Тайтл/Бриф\n"
        "2. Паспорт (последняя и предпоследняя страница, регистрация)\n"
        "3. Фото (Шильдик с VIN номером, повреждения автомобиля)\n"
        "4. Ваши контакты (телефон/имя пользователя телеграм)\n\n"
         
        "После того как загрузите данные по списку выше, напишите 'Готово'."
    )
    # Инициализация сессии оценки
    client_data[message.from_user.id] = {"type": "evaluation", "messages": []}

@router.message(lambda message: message.from_user.id in client_data and client_data[message.from_user.id].get("type") == "evaluation")
async def receive_evaluation_data(message: Message):
    if message.text and message.text.lower() == "готово":
        # Сбор и отправка накопленных сообщений и медиафайлов админу
        if "messages" in client_data[message.from_user.id]:
            for item in client_data[message.from_user.id]["messages"]:
                if "type" in item and item["type"] == "text":
                    await bot.send_message(ADMIN_ID, item["content"])
                elif "type" in item and item["type"] == "media":
                    if item["media_type"] == "photo":
                        await bot.send_photo(ADMIN_ID, item["content"], caption=item.get("caption", ""))
                    elif item["media_type"] == "document":
                        await bot.send_document(ADMIN_ID, item["content"], caption=item.get("caption", ""))
        await message.answer("Спасибо! Ваша заявка отправлена.")
        client_data.pop(message.from_user.id, None)  # Очищаем данные пользователя
    else:
        # Обработка текста, фотографий и документов
        content_type = message.content_type
        if content_type == ContentType.TEXT:
            client_data[message.from_user.id].setdefault("messages", []).append({"type": "text", "content": message.text})
        elif content_type == ContentType.PHOTO:
            photo_id = message.photo[-1].file_id  # Получаем file_id последнего фото
            caption = message.caption if message.caption else ""  # Сохранение подписи, если она есть
            client_data[message.from_user.id].setdefault("messages", []).append({"type": "media", "media_type": "photo", "content": photo_id, "caption": caption})
        elif content_type == ContentType.DOCUMENT:
            document_id = message.document.file_id  # Получаем file_id документа
            caption = message.caption if message.caption else ""  # Сохранение подписи, если она есть
            client_data[message.from_user.id].setdefault("messages", []).append({"type": "media", "media_type": "document", "content": document_id, "caption": caption})
# Уточняющие вопросы для подбора авто
country_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="США"), KeyboardButton(text="Канада")],
        [KeyboardButton(text="Корея"), KeyboardButton(text="Китай")],
        [KeyboardButton(text="Германия")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(lambda message: message.text == "⚡ Подбор авто")
async def car_selection(message: Message):
    client_data[message.from_user.id] = {"type": "car_selection", "info": {}}
    await message.answer("Введите год выпуска автомобиля:")

@router.message(lambda message: message.from_user.id in client_data and client_data[message.from_user.id]["type"] == "car_selection")
async def handle_car_selection(message: Message):
    user_info = client_data[message.from_user.id]["info"]
    if "year" not in user_info:
        user_info["year"] = message.text
        await message.answer("Введите марку автомобиля:")
    elif "brand" not in user_info:
        user_info["brand"] = message.text
        await message.answer("Введите модель автомобиля:")
    elif "model" not in user_info:
        user_info["model"] = message.text
        await message.answer("Введите цвет автомобиля:")
    elif "color" not in user_info:
        user_info["color"] = message.text
        await message.answer("Выберите страну происхождения автомобиля:", reply_markup=country_menu)
    elif "country" not in user_info:
        user_info["country"] = message.text
        await message.answer("Введите ваши контакты (телефон/имя пользователя телеграм):")
    elif "contacts" not in user_info:
        user_info["contacts"] = message.text
        summary = (
            f"Запрос на подбор авто:\n"
            f"Год выпуска: {user_info['year']}\n"
            f"Марка: {user_info['brand']}\n"
            f"Модель: {user_info['model']}\n"
            f"Цвет: {user_info['color']}\n"
            f"Контакты: {user_info['contacts']}\n"
            f"Страна: {user_info['country']}"
        )
        # Отправка данных админу
        await bot.send_message(ADMIN_ID, summary)
        await message.answer("Спасибо! Ваша заявка отправлена.", reply_markup=main_menu)
        client_data.pop(message.from_user.id, None)  # Очищаем данные пользователя

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())