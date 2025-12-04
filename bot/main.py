import asyncio
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from model import load_model, Melody_Generator

with open('token.txt', encoding='utf-8') as file:
    TOKEN = file.read()

dp = Dispatcher()

# Глобальная переменная для хранения модели (опционально, для кэширования)
model_instance = None


# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer("Hello! I'm a music generation bot. Use /generate to create music.")


@dp.message(Command("generate"))
async def command_generate_handler(message: Message, command: CommandObject) -> None:
    """
    Команда с параметрами: /generate [style] [duration]
    Пример: /generate jazz 30
    """
    try:
        await message.answer("🎵 Starting melody generation... This may take a moment.")

        args = command.args.split() if command.args else []
        style = args[0] if len(args) > 0 else "Chopin"
        duration = args[1] if len(args) > 1 else "60"
        
        await message.answer("📥 Loading model...")
        path = choose_path(style)
        model = load_model(path)
        
        # Генерируем мелодию
        await message.answer("🎹 Generating melody...")
        result = Melody_Generator(model)
        
        # Отправляем результат
        await message.answer(f"✅ Melody generated successfully!\n\nResult: {result}")
        
    except Exception as e:
        # Обработка ошибок
        error_message = f"❌ Error during generation: {str(e)}"
        await message.answer(error_message, parse_mode=ParseMode.HTML)


# Run the bot
async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
