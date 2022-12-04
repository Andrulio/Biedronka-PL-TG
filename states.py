from aiogram.dispatcher.filters.state import StatesGroup, State

class card(StatesGroup):
    number = State()

class addPromo(StatesGroup):
    name = State()
    photo = State()

class use_promo(StatesGroup):
    use = State()