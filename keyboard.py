from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
start_buttons = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
start_buttons.add(KeyboardButton("Mój profil"), KeyboardButton("Dodać promocję"), KeyboardButton("Wszystkie promocję"))
