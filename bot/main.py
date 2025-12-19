import asyncio
import os
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaDocument
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import logging
import fitz

logging.basicConfig(level=logging.INFO)

from model import load_model, Melody_Generator

with open('token.txt', encoding='utf-8') as file:
    TOKEN = file.read()

dp = Dispatcher()

DEFAULT_COMPOSERS = os.listdir('models/')
DEFAULT_DURATIONS = [15, 30, 45, 60, 90, 120]
DEFAULT_TEMPOS = [60, 80, 100, 120, 140, 160]


user_states = {}

def choose_path(style):

    return f"models/{style}/" 

def get_main_menu_keyboard():
    """Создает главное меню с кнопками"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎵 Сгенерировать музыку", callback_data="main_generate")
    builder.button(text="🎹 Список стилей", callback_data="main_composers")
    builder.button(text="❓ Помощь", callback_data="main_help")
    
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_menu_keyboard():
    """Создает кнопку для возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в меню", callback_data="back_to_main_menu")
    return builder.as_markup()

def get_composers_keyboard(with_back_to_main=True):
    """Создает клавиатуру для выбора композитора"""
    builder = InlineKeyboardBuilder()
    
    for composer in DEFAULT_COMPOSERS:
        builder.button(text=composer, callback_data=f"composer_{composer}")
    
    if with_back_to_main:
        builder.button(text="🔙 Назад в меню", callback_data="back_to_main_menu")
    
    builder.adjust(2)  # 2 кнопки в строке
    return builder.as_markup()

def get_durations_keyboard():
    """Создает клавиатуру для выбора длительности"""
    builder = InlineKeyboardBuilder()
    
    for duration in DEFAULT_DURATIONS:
        builder.button(text=f"{duration} сек", callback_data=f"duration_{duration}")
    
    builder.button(text="Ввести вручную", callback_data="duration_custom")
    builder.button(text="🔙 Назад", callback_data="back_to_composers")
    
    builder.adjust(2)
    return builder.as_markup()

def get_tempos_keyboard():
    """Создает клавиатуру для выбора темпа"""
    builder = InlineKeyboardBuilder()
    
    for tempo in DEFAULT_TEMPOS:
        builder.button(text=f"{tempo} BPM", callback_data=f"tempo_{tempo}")
    
    builder.button(text="Ввести вручную", callback_data="tempo_custom")
    builder.button(text="🔙 Назад", callback_data="back_to_durations")
    
    builder.adjust(2)
    return builder.as_markup()

def get_confirmation_keyboard():
    """Создает клавиатуру для подтверждения параметров"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Начать генерацию", callback_data="confirm_generate")
    builder.button(text="🔄 Изменить стиль", callback_data="change_composer")
    builder.button(text="🔄 Изменить длительность", callback_data="change_duration")
    builder.button(text="🔄 Изменить темп", callback_data="change_tempo")
    builder.button(text="❌ Отменить", callback_data="cancel_generate")
    
    builder.adjust(1)  # По одной кнопке в строке
    return builder.as_markup()

# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    welcome_text = (
        "🎵 **Добро пожаловать в Music Generation Bot!**\n\n"
        "Я могу генерировать музыку в разных стилях.\n\n"
        "**Выберите действие:**"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu_keyboard())

# Обработчики главного меню
@dp.callback_query(F.data == "main_generate")
async def main_menu_generate(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {
        "step": "choosing_composer",
        "composer": None,
        "duration": None,
        "tempo": None
    }
    
    text = (
        "🎹 **Выберите стиль:**\n\n"
        "Выберите один из предложенных стилей для генерации музыки:"
    )
    await callback.message.edit_text(
        text, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=get_composers_keyboard(with_back_to_main=True)  # Теперь есть кнопка "Назад в меню"
    )
    await callback.answer()

@dp.callback_query(F.data == "main_composers")
async def main_menu_composers(callback: CallbackQuery):
    composers_list = "\n".join([f"• {composer}" for composer in DEFAULT_COMPOSERS])
    text = f"**🎹 Доступные стили:**\n\n{composers_list}\n\nВыберите стиль для генерации музыки в его стиле:"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_composers_keyboard(with_back_to_main=True)
    )
    await callback.answer()

@dp.callback_query(F.data == "main_help")
async def main_menu_help(callback: CallbackQuery):
    help_text = (
        "**📖 Справка по боту:**\n\n"
        "**Основные команды:**\n"
        "• `/generate` - Начать генерацию музыки\n"
        "• `/composers` - Показать список стилей\n"
        "• `/help` - Показать эту справку\n"
        "• `/start` - Перезапустить бота\n\n"
        "**Быстрая генерация:**\n"
        "Можно использовать команду:\n"
        "`/generate [стиль] [длительность] [темп]`\n"
        "Пример: `/generate Mozart 45 90`\n\n"
        "**Ограничения:**\n"
        "• Длительность: от 10 до 300 секунд\n"
        "• Темп: от 20 до 300 BPM"
    )
    
    await callback.message.edit_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Очищаем состояние пользователя при возврате в главное меню
    if user_id in user_states:
        del user_states[user_id]
    
    welcome_text = (
        "🎵 **Главное меню**\n\n"
        "Выберите действие:"
    )
    await callback.message.edit_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@dp.message(Command("composers"))
async def command_composers_handler(message: Message) -> None:
    composers_list = "\n".join([f"• {composer}" for composer in DEFAULT_COMPOSERS])
    text = f"**🎹 Доступные стили:**\n\n{composers_list}\n\nВыберите стиль для генерации музыки в его стиле:"
    
    await message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_composers_keyboard(with_back_to_main=True)
    )

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    help_text = (
        "**📖 Справка по боту:**\n\n"
        "**Основные команды:**\n"
        "• `/generate` - Начать генерацию музыки\n"
        "• `/composers` - Показать список стилей\n"
        "• `/help` - Показать эту справку\n"
        "• `/start` - Перезапустить бота\n\n"
        "**Быстрая генерация:**\n"
        "Можно использовать команду:\n"
        "`/generate [стиль] [длительность] [темп]`\n"
        "Пример: `/generate Mozart 45 90`\n\n"
        "**Ограничения:**\n"
        "• Длительность: от 10 до 300 секунд\n"
        "• Темп: от 20 до 300 BPM"
    )
    
    await message.answer(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_to_menu_keyboard()
    )

@dp.message(Command("generate"))
async def command_generate_handler(message: Message, command: CommandObject) -> None:
    """
    Обработчик команды /generate
    Поддерживает два режима:
    1. С параметрами: /generate style duration tempo
    2. Интерактивный режим без параметров
    """
    # Если есть аргументы, используем быстрый режим
    if command.args:
        try:
            args = command.args.split()
            style = args[0].strip() if len(args) > 0 else "Chopin"
            duration = int(args[1]) if len(args) > 1 else 60
            tempo = int(args[2]) if len(args) > 2 else 128
            if style not in DEFAULT_COMPOSERS:
                await message.answer("⚠️ Не удалось найти этот стиль")
                return
            
            if duration > 300:
                await message.answer("⚠️ Длительность не может превышать 300 секунд")
                return
            elif duration < 10:
                await message.answer("⚠️ Длительность не может быть меньше 10 секунд")
                return

            if tempo < 0:
                await message.answer("⚠️ Темп не может быть отрицательным")
                return
            elif tempo < 20:
                await message.answer("⚠️ Темп слишком медленный")
                return
            
            await start_generation(message, style, duration, tempo)
            
        except ValueError:
            await message.answer("❌ Ошибка в формате команды. Пример: `/generate Chopin 60 128`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    else:
        # Интерактивный режим - перенаправляем в главное меню
        user_id = message.from_user.id
        user_states[user_id] = {
            "step": "choosing_composer",
            "composer": None,
            "duration": None,
            "tempo": None
        }
        
        text = (
            "🎹 **Выберите стиль:**\n\n"
            "Выберите один из предложенных стилуй для генерации музыки:"
        )
        await message.answer(
            text, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=get_composers_keyboard(with_back_to_main=True)  # Теперь есть кнопка "Назад в меню"
        )

# Обработчики callback-запросов для генерации
@dp.callback_query(F.data.startswith("composer_"))
async def process_composer_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    composer = callback.data.split("_")[1]
    
    # Сохраняем выбор композитора
    if user_id not in user_states:
        user_states[user_id] = {}
    
    user_states[user_id]["composer"] = composer
    user_states[user_id]["step"] = "choosing_duration"
    
    await callback.message.edit_text(
        f"🎹 **Выбран стиль:** {composer}\n\n"
        f"⏱️ **Теперь выберите длительность композиции:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_durations_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "duration_custom")
async def process_custom_duration(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "entering_custom_duration"
    
    await callback.message.edit_text(
        "⏱️ **Введите длительность композиции в секундах:**\n\n"
        "Минимум: 10 сек\n"
        "Максимум: 300 сек",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("duration_"))
async def process_duration_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "duration_custom":
        return
    
    duration = int(callback.data.split("_")[1])

    # Сохраняем выбор длительности
    user_states[user_id]["duration"] = duration
    user_states[user_id]["step"] = "choosing_tempo"
    
    await callback.message.edit_text(
        f"🎹 **Стиль:** {user_states[user_id]['composer']}\n"
        f"⏱️ **Длительность:** {duration} сек\n\n"
        f"🎵 **Теперь выберите темп (BPM):**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_tempos_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "tempo_custom")
async def process_custom_tempo(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "entering_custom_tempo"
    
    await callback.message.edit_text(
        "🎵 **Введите темп (BPM):**\n\n"
        "Обычные значения: от 40 до 200 BPM\n"
        "Примеры:\n"
        "• Медленно (Largo): 40-60 BPM\n"
        "• Умеренно (Andante): 76-108 BPM\n"
        "• Быстро (Allegro): 120-168 BPM",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("tempo_"))
async def process_tempo_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "tempo_custom":
        return
    
    tempo = int(callback.data.split("_")[1])
    # Сохраняем выбор темпа
    user_states[user_id]["tempo"] = tempo
    user_states[user_id]["step"] = "confirmation"
    
    composer = user_states[user_id]["composer"]
    duration = user_states[user_id]["duration"]
    
    confirmation_text = (
        f"✅ **Параметры генерации:**\n\n"
        f"🎹 **Стиль:** {composer}\n"
        f"⏱️ **Длительность:** {duration} секунд\n"
        f"🎵 **Темп:** {tempo} BPM\n\n"
        f"Проверьте параметры и нажмите 'Начать генерацию'"
    )
    
    await callback.message.edit_text(
        confirmation_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_confirmation_keyboard()
    )
    await callback.answer()

# Обработчики кнопок назад
@dp.callback_query(F.data == "back_to_composers")
async def back_to_composers(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in user_states:
        user_states[user_id]["step"] = "choosing_composer"
    
    text = "🎹 **Выберите стиль:**"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_composers_keyboard(with_back_to_main=True)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_durations")
async def back_to_durations(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "choosing_duration"
    
    composer = user_states[user_id]["composer"]
    text = f"🎹 **Стиль:** {composer}\n\n⏱️ **Выберите длительность:**"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_durations_keyboard()
    )
    await callback.answer()

# Обработчики изменения параметров
@dp.callback_query(F.data == "change_composer")
async def change_composer(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "choosing_composer"
    
    await callback.message.edit_text(
        "🎹 **Выберите стиль:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_composers_keyboard(with_back_to_main=True)
    )
    await callback.answer()

@dp.callback_query(F.data == "change_duration")
async def change_duration(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "choosing_duration"
    
    composer = user_states[user_id]["composer"]
    await callback.message.edit_text(
        f"🎹 **Стиль:** {composer}\n\n⏱️ **Выберите длительность:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_durations_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "change_tempo")
async def change_tempo(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id]["step"] = "choosing_tempo"
    
    composer = user_states[user_id]["composer"]
    duration = user_states[user_id]["duration"]
    
    await callback.message.edit_text(
        f"🎹 **Стиль:** {composer}\n"
        f"⏱️ **Длительность:** {duration} сек\n\n"
        f"🎵 **Выберите темп:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_tempos_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_generate")
async def cancel_generation(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Очищаем состояние пользователя
    if user_id in user_states:
        del user_states[user_id]
    
    welcome_text = (
        "❌ **Генерация отменена.**\n\n"
        "🎵 **Главное меню**\n\n"
        "Выберите действие:"
    )
    await callback.message.edit_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "confirm_generate")
async def confirm_generation(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_states:
        await callback.answer("❌ Сессия устарела. Начните заново с /generate", show_alert=True)
        return
    
    composer = user_states[user_id].get("composer")
    duration = user_states[user_id].get("duration")
    tempo = user_states[user_id].get("tempo")
    
    if not all([composer, duration, tempo]):
        await callback.answer("❌ Не все параметры выбраны!", show_alert=True)
        return
    
    # Очищаем состояние перед генерацией
    del user_states[user_id]
    
    await callback.message.edit_text(
        f"🎵 **Начинаю генерацию...**\n\n"
        f"• Стиль: {composer}\n"
        f"• Длительность: {duration} сек.\n"
        f"• Темп: {tempo} BPM\n\n"
        f"⏳ Пожалуйста, подождите...",
        parse_mode=ParseMode.MARKDOWN)
    # Запускаем генерацию
    await callback.answer()
    await start_generation(callback.message, composer, duration, tempo)

# Обработка ручного ввода длительности и темпа
@dp.message(F.text)
async def handle_text_input(message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    current_step = user_states[user_id].get("step", "")
    
    try:
        # Обработка ручного ввода длительности
        if current_step == "entering_custom_duration":
            try:
                duration = int(message.text.strip())
                
                if duration < 10:
                    await message.answer("⚠️ Длительность не может быть меньше 10 секунд")
                    return
                elif duration > 300:
                    await message.answer("⚠️ Длительность не может превышать 300 секунд")
                    return
                
                user_states[user_id]["duration"] = duration
                user_states[user_id]["step"] = "choosing_tempo"
                
                composer = user_states[user_id]["composer"]
                
                await message.answer(
                    f"🎹 **Стиль:** {composer}\n"
                    f"⏱️ **Длительность:** {duration} сек\n\n"
                    f"🎵 **Теперь выберите темп (BPM):**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_tempos_keyboard()
                )
                
            except ValueError:
                await message.answer("❌ Пожалуйста, введите число (например: 60)")
        
        # Обработка ручного ввода темпа
        elif current_step == "entering_custom_tempo":
            try:
                tempo = int(message.text.strip())
                
                if tempo < 20:
                    await message.answer("⚠️ Темп слишком медленный. Минимум: 20 BPM")
                    return
                elif tempo > 300:
                    await message.answer("⚠️ Темп слишком быстрый. Максимум: 300 BPM")
                    return
                
                user_states[user_id]["tempo"] = tempo
                user_states[user_id]["step"] = "confirmation"
                
                composer = user_states[user_id]["composer"]
                duration = user_states[user_id]["duration"]
                
                confirmation_text = (
                    f"✅ **Параметры генерации:**\n\n"
                    f"🎹 **Стиль:** {composer}\n"
                    f"⏱️ **Длительность:** {duration} секунд\n"
                    f"🎵 **Темп:** {tempo} BPM\n\n"
                    f"Проверьте параметры и нажмите 'Начать генерацию'"
                )
                
                await message.answer(
                    confirmation_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_confirmation_keyboard()
                )
                
            except ValueError:
                await message.answer("❌ Пожалуйста, введите число (например: 120)")
    
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

# Функция запуска генерации (остается без изменений)
async def start_generation(message: Message, style: str, duration: int, tempo: int = None):
    try:
        path = choose_path(style)
        midi_name = f'{style}_{duration}_{tempo}'
        notes, melody = Melody_Generator(path, duration=duration, tempo=tempo)
        melody.write('midi', f'{midi_name}.mid')
        melody.write('lily.pdf', midi_name)
        doc = fitz.open(f'{midi_name}.pdf')
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            pix.save(f'{midi_name}.png')
            break
        doc.close()
        
        success_text = (
            f"✅ **Музыка успешно сгенерирована!**\n\n"
            f"**Параметры:**\n"
            f"• Стиль: {style}\n"
            f"• Длительность: {duration} сек.\n"
            f"• Темп: {tempo} BPM\n\n"
            )
        media = [
            InputMediaDocument(media=FSInputFile(f'{midi_name}.png')),
            InputMediaDocument(media=FSInputFile(f'{midi_name}.pdf')),
            InputMediaDocument(media=FSInputFile(f'{midi_name}.mid'), caption=success_text)
            ]
        await message.answer_media_group(media=media)
        
        for ext in ['', '.mid', '.pdf', '.png']:
            os.remove(f'{midi_name}{ext}')
        
        # Предлагаем вернуться в главное меню
        await message.answer(
            "🎵 **Хотите сгенерировать еще одну композицию?**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        error_text = (
            f"❌ **Произошла ошибка при генерации:**\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"Попробуйте еще раз с другими параметрами."
        )
        await message.answer(
            error_text, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        
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
