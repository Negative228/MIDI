import asyncio
import os
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaDocument
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import fitz

# Настройка логирования
logging.basicConfig(level=logging.INFO)

from model import load_model, Melody_Generator

with open('token.txt', encoding='utf-8') as file:
    TOKEN = file.read()

dp = Dispatcher()

# Настройки по умолчанию
DEFAULT_COMPOSERS = ["Chopin", "Beethoven", "Mozart", "Bach", "Tchaikovsky"]
DEFAULT_TEMPOS = [60, 90, 120, 150]

# Глобальные переменные для хранения состояния пользователя
user_states = {}

def choose_path(style):
    # Здесь реализуйте логику выбора пути к модели на основе стиля
    return f"models/{style}/"  # Пример пути

# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    welcome_text = (
        "🎵 **Добро пожаловать в Music Generation Bot!**\n\n"
        "Я могу генерировать музыку в стиле разных композиторов.\n\n"
        "**Доступные команды:**\n"
        #"/generate - Начать генерацию музыки\n"
        "/composers - Список доступных композиторов\n"
        "/help - Помощь\n\n"
        "Вы также можете использовать команду:\n"
        "`/generate [стиль] [длительность] [темп]`\n"
        "Пример: `/generate Chopin 30 128`"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("composers"))
async def command_composers_handler(message: Message) -> None:
    composers_list = "\n".join([f"• {composer}" for composer in DEFAULT_COMPOSERS])
    text = f"**Доступные композиторы:**\n\n{composers_list}\n\nВыберите композитора в меню /generate"
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    help_text = (
        "**📖 Справка по боту:**\n\n"
        #"1. **/generate** - Запустить процесс генерации музыки с выбором параметров\n"
        "2. **/generate [стиль] [длительность] [темп]** - Быстрая генерация\n"
        "   Пример: `/generate Mozart 45 90`\n"
        "3. **/composers** - Показать список доступных композиторов\n"
        "4. **/start** - Перезапустить бота\n\n"
        "**Длительность указывается в секундах (макс: 120)**"
    )
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("generate"))
async def command_generate_handler(message: Message, command: CommandObject) -> None:
    """
    Обработчик команды /generate
    Поддерживает два режима:
    1. С параметрами: /generate style duration
    2. Интерактивный режим без параметров
    """
    # Если есть аргументы, используем быстрый режим
    if command.args:
        print(command.args)
        try:
            
            args = command.args.split()
            print(args)
            style = args[0] if len(args) > 0 else "Chopin"
            duration = int(args[1]) if len(args) > 1 else 60
            tempo = int(args[2]) if len(args) > 2 else 128
            print(style, duration, tempo)
            # Проверка длительности
            if duration > 300:
                await message.answer("⚠️ Длительность не может превышать 300 секунд")
                return
            elif duration < 10:
                await message.answer("⚠️ Длительность не может быть меньше 10 секунд")
                return
            
            await start_generation(message, style, duration, tempo)
            
        except ValueError:
            await message.answer("❌ Ошибка в формате команды. Пример: `/generate Chopin 60 128`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    else:
        pass ####
        # Интерактивный режим
        user_id = message.from_user.id
        user_states[user_id] = {"step": "choosing_composer"}
        
        text = (
            "🎹 **Выберите композитора:**\n\n"
            "Вы можете выбрать одного из предложенных или использовать команду:\n"
            "`/generate [композитор] [длительность]`"
        )
        await message.answer(text, reply_markup=get_composers_keyboard(), parse_mode=ParseMode.MARKDOWN)


# Функция запуска генерации
async def start_generation(message: Message, style: str, duration: int, tempo: int = None):
    try:
        await message.answer(f"🎵 **Начинаю генерацию...**\n\n"
                           f"• Стиль: {style}\n"
                           f"• Длительность: {duration} сек.\n"
                           f"• Темп: {tempo} BPM\n\n"
                           f"⏳ Пожалуйста, подождите...", parse_mode=ParseMode.MARKDOWN)
        
        # Загрузка модели
        print('*')
        path = choose_path(style)
        print('*')
        midi_name = f'{style}_{duration}_{tempo}'
        print('*')
        #model = load_model(path)
        print(path)
        print(midi_name)
        # Генерация мелодии
        
        notes, melody = Melody_Generator(path, duration=duration, tempo=tempo)
        print('*')
        melody.write('midi', f'{midi_name}.mid')
        melody.write('lily.pdf', midi_name)
        print('*')
        doc = fitz.open(f'{midi_name}.pdf')
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            pix.save(f'{midi_name}.png')
            break
        doc.close()
        print('*')
        #await message.answer_document(FSInputFile(midi_name))
        # Отправка результата
        success_text = (
            f"✅ **Музыка успешно сгенерирована!**\n\n"
            f"**Параметры:**\n"
            f"• Композитор: {style}\n"
            f"• Длительность: {duration} сек.\n"
            f"• Темп: {tempo} BPM\n\n"
            #f"**Результат:**\n{notes[:200]}..." if len(notes) > 200 else notes
        )
        #await message.answer(success_text, parse_mode=ParseMode.MARKDOWN)
        #media_group = MediaGroupBuilder(caption=success_text)
        media = [
            InputMediaDocument(media=FSInputFile(f'{midi_name}.png')),
            InputMediaDocument(media=FSInputFile(f'{midi_name}.pdf')),
            InputMediaDocument(media=FSInputFile(f'{midi_name}.mid'), caption=success_text)
            ]
        await message.answer_media_group(media=media)
        
        for ext in ['', '.mid', '.pdf', '.png']:
            os.remove(f'{midi_name}{ext}')
        
        # Предложение сгенерировать еще
        await message.answer("Хотите сгенерировать еще одну композицию? Используйте /generate")
        
    except Exception as e:
        error_text = (
            f"❌ **Произошла ошибка при генерации:**\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"Попробуйте еще раз с другими параметрами."
        )
        await message.answer(error_text, parse_mode=ParseMode.MARKDOWN)
        
        # Очистка состояния в случае ошибки
        user_id = message.from_user.id
        if user_id in user_states:
            del user_states[user_id]

# Запуск бота
async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
