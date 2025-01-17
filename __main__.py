from telebot import TeleBot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import prettytable as pt

from sqlite import Database

db = Database()
token = "7292719491:AAELv55ohhCN_IXnLzgRqP3SkjxUBjs383w"
bot = TeleBot(token)
ids = [540708864, 383063470]
user_state = {}

@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    global ids
    if auth(message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Show balances"))
        markup.row(KeyboardButton("Deposit"), KeyboardButton("Pay all"))
        markup.row(KeyboardButton("New user"), KeyboardButton("Remove user"))
        bot.send_message(message.chat.id, "Чем займемся сегодня?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Deposit")
def message_reply(message):
    if auth(message):
        user_state.clear()
        users = InlineKeyboardMarkup(row_width=2)
        all_users = db.get_all_users()
        while all_users:
            user = all_users.pop()
            if all_users:
                user2 = all_users.pop()
                users.row(
                    InlineKeyboardButton(user, callback_data=f"deposit_{user}"),
                    InlineKeyboardButton(user2, callback_data=f"deposit_{user2}")
                )
            else:
                users.row(
                    InlineKeyboardButton(user, callback_data=f"deposit_{user}"),
                )


        bot.send_message(message.chat.id, "Выберите пользователя для депозита:", reply_markup=users)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def select_user_for_deposit(call):
    user = call.data[8:]
    user_state[call.from_user.id] = {"action": "deposit", "user": user}
    bot.send_message(call.message.chat.id, "Введите сумму для депозита:")



@bot.message_handler(
    func=lambda message: message.chat.id in user_state and user_state[message.chat.id]["action"] == "deposit")
def process_deposit_amount(message):
    try:
        amount = int(message.text)
        user = user_state[message.chat.id]["user"]
        current_balance = db.deposit_user_balance(user, amount)

        bot.send_message(message.chat.id,
                         f"Депозит {amount} рублей успешно зачислен пользователю {user}. Текущий баланс: {current_balance} руб.")

        user_state.pop(message.chat.id, None)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")

@bot.message_handler(func=lambda message: message.text == "Pay all")
def handle_pay(message):
    db.purchase_all_users(50)
    bot.send_message(message.chat.id, "Со всех пользователей списано 50 рублей.")

@bot.message_handler(func=lambda message: message.text == "Show balances")
def get_user_balances(message):
    table = pt.PrettyTable(['User', 'Balance', 'Duration'])
    table.align['User'] = 'l'
    table.align['Balance'] = 'r'
    table.align['Duration'] = 'r'
    for symbol, price in db.get_all_balances():
        table.add_row([symbol, price, price/50])
    bot.send_message(message.chat.id, f"<pre>{table}</pre>", parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "New user")
def handle_create_user(message):
    bot.send_message(message.chat.id, "введи <user_name> <balance(optional)>")
    try:
        bot.register_next_step_handler(message, create_user)
    except Exception as e:
        bot.send_message(message.chat.id, "ой, что то пошло не так")

def create_user(message):
    if " " in message.text:
        name, balance = message.text.split(" ")
    else:
        name = message.text.strip()
        balance = 0
    db.create_user(name, balance)
    bot.send_message(message.chat.id, f"Пользователь '{name}' успешно создан.")

@bot.message_handler(func=lambda message: message.text == "Remove user")
def handle_remove_user(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton(""))
    bot.send_message(message.chat.id, "введи <user_name>")
    try:
        bot.register_next_step_handler(message, del_user)
    except Exception as e:
        bot.send_message(message.chat.id, "ой, что то пошло не так")

def del_user(message):
    db.del_user(str(message.text.strip()))

def auth(message):
    global ids
    if message.from_user.id not in ids:
        bot.send_message(message.chat.id, 'Ошибся адресом, дружок')
        print(message.from_user.id)
        return False
    else:
        return True

while True:
    try:
        bot.polling()
    except Exception as e:
        print(e)
        continue




