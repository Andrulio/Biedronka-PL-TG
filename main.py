import sqlite3
from barcode import EAN13 as i
from barcode.writer import ImageWriter
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils import executor
from datetime import datetime
from config import dp, bot
from keyboard import *
from states import *

conn = sqlite3.connect('database.db')
print("Connected with SQLite")
cur = conn.cursor()
cur.execute(f"""CREATE TABLE IF NOT EXISTS users(
userid INT PRIMARY KEY,
username TEXT,
card_number TEXT,
promotions INT
)""")
conn.commit()
cur.execute(f"""CREATE TABLE IF NOT EXISTS promotions(
userid INT,
promotion TEXT,
date TEXT
)""")
conn.commit()


def barcode_setup(text, name, username):
    my_ean = i(text, writer=ImageWriter())
    my_ean.save(f'cards/{name}')
    cur.execute(f"""INSERT INTO users(userid, username ,card_number, promotions) 
       VALUES('{name}', '{username}' ,'{text}', {0});""")
    conn.commit()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cur.execute("SELECT userid FROM users WHERE userid = ?", (message.chat.id,))
    result = cur.fetchone()
    if result:
        await bot.send_message(message.chat.id, "Hej! Czas zobaczyć nowe promocję!", reply_markup=start_buttons)
    else:
        await bot.send_message(message.chat.id, "<b>Hejka!</b> \n\n"
                                                "<b>Wpisz numer karty Biedronki (bez spacji)</b>\n"
                                                "<b>Na przykład</b>\n"
                                                "<code>9300819362238</code>", parse_mode='HTML')
        await card.number.set()


@dp.message_handler(Text(equals="Mój profil"))
async def profile(message: types.Message):
    cur.execute("SELECT * FROM users WHERE userid = ?", (message.chat.id,))
    result = cur.fetchall()
    photo = open(f'cards/{message.chat.id}.png', 'rb')
    await bot.send_photo(chat_id=message.chat.id, photo=photo,
                         caption=f"🆔 <code>{message.chat.id}</code>\n"
                                 f"<b>Karta Biedronki:</b> <code>{result[0][2]}</code>\n"
                                 f"<b>Dodanych promocji:</b> <code>{result[0][3]}</code>",
                         parse_mode='HTML')


@dp.message_handler(Text(equals="Dodać promocję"))
async def promo_add(message: types.Message):
    photo = open('example.jpg', 'rb')
    await bot.send_photo(chat_id=message.chat.id,
                         photo=photo,
                         caption="<b>Aby dodać promocję wyślij mi takiego typu screenshota produktu z Biedronki</b>",
                         parse_mode='HTML')


@dp.message_handler(content_types=['photo'])
async def test(message: types.Message):
    file_info = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
    file_path = file_info.file_path
    await bot.download_file(file_path, f"received/{datetime.date(datetime.now())}/{message.chat.id}.png")
    await bot.send_message(message.chat.id, "<b>Wpisz nazwę produktu </b>", parse_mode='HTML')
    await addPromo.name.set()


@dp.message_handler(state=addPromo.name)
async def add_promo(message: types.Message, state: FSMContext):
    name = message.text
    await state.finish()
    print(datetime.date(datetime.now()))
    cur.execute(f"""INSERT INTO promotions(userid, promotion, date) 
           VALUES('{message.chat.id}', '{name}', '{datetime.date(datetime.now())}');""")
    conn.commit()

    await bot.send_message(message.chat.id, "<b>Dodałem twoją promocję!😚</b>", parse_mode='HTML')


@dp.message_handler(state=card.number)
async def set_card(message: types.Message, state: FSMContext):
    await state.finish()
    barcode_setup(text=message.text, name=message.chat.id, username=message.chat.username)
    card_number = open(f"cards/{message.chat.id}.png", "rb")
    await bot.send_photo(chat_id=message.chat.id, photo=card_number, caption="To jest twoja karta biedronki!",
                         reply_markup=start_buttons)


@dp.message_handler(Text(equals="Wszystkie promocję"))
async def all_promo(message: types.Message):
    all_btns = InlineKeyboardMarkup(row_width=1)
    for i in cur.execute("""SELECT * FROM promotions""").fetchall():
        if i[2] == str(datetime.date(datetime.now())):
            all_btns.add(InlineKeyboardButton(text=i[1], callback_data=f"promo:{i[0]}"))
    await bot.send_message(message.chat.id, "Wybierz promocję do oglądania", reply_markup=all_btns)


@dp.callback_query_handler(text_contains='promo')
async def show_promo(call: CallbackQuery, state: FSMContext):
    await call.answer()
    id = call.data.split(":")[1]
    photo = open(f"received/{datetime.date(datetime.now())}/{id}.png", 'rb')
    await bot.send_photo(chat_id=call.message.chat.id,
                         photo=photo)

    card = open(f"cards/{id}.png", 'rb')
    btns = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Wykorzystałem ✅"), KeyboardButton("◀️Powrót"))
    await bot.send_photo(chat_id=call.message.chat.id,
                         photo=card,
                         caption="<b>Aby skorzystać z tej promocji, zeskanuj ten kod kreskowy</b>",
                         parse_mode='HTML', reply_markup=btns)
    await use_promo.use.set()
    await state.update_data(use=id)


@dp.message_handler(state=use_promo.use)
async def use1(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    if message.text == "◀️Powrót":
        await bot.send_message(message.chat.id, "Powrót", reply_markup=start_buttons)
    else:
        id = data['use']
        cur.execute("DELETE FROM promotions WHERE userid = ?", (id,))
        conn.commit()
        cur.execute("SELECT username FROM users WHERE userid = ?", (id,))

        await bot.send_message(message.chat.id, f"@{cur.fetchone()[0]} automatycznie dostał podziękowanie 🥹",
                               reply_markup=start_buttons)
        await bot.send_message(id, f"<b>Masz podziękowanie od </b>@{message.chat.username}🫶", parse_mode="HTML")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
