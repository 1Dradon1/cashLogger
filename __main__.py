from telebot import TeleBot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import prettytable as pt
from sqlite import Database

# Инициализация базы данных и бота
db = Database()
token = "7292719491:AAELv55ohhCN_IXnLzgRqP3SkjxUBjs383w"
bot = TeleBot(token)

# Глобальные переменные
AUTHORIZED_IDS = [540708864, 383063470]
user_state = {}

# Функция проверки авторизации
def is_authorized(message):
    if message.from_user.id not in AUTHORIZED_IDS:
        bot.send_message(message.chat.id, 'Ошибся адресом, дружок')
        print(message.from_user.id)
        return False
    return True

# Обработчик команды /start
@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    if not is_authorized(message):
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Show balances"))
    markup.row(KeyboardButton("Deposit"), KeyboardButton("Pay all"))
    markup.row(KeyboardButton("New user"), KeyboardButton("Remove user"))
    bot.send_message(message.chat.id, "Чем займемся сегодня?", reply_markup=markup)

# Обработчик кнопки "Deposit"
@bot.message_handler(func=lambda message: message.text == "Deposit")
def deposit_handler(message):
    if not is_authorized(message):
        return

    user_state.clear()
    users_markup = InlineKeyboardMarkup(row_width=2)
    all_users = db.get_all_users()

    for i in range(0, len(all_users), 2):
        buttons = [
            InlineKeyboardButton(user, callback_data=f"deposit_{user}")
            for user in all_users[i:i+2]
        ]
        users_markup.row(*buttons)

    bot.send_message(message.chat.id, "Выберите пользователя для депозита:", reply_markup=users_markup)

# Обработчик выбора пользователя для депозита
@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def select_user_for_deposit(call):
    user = call.data[len("deposit_"):]
    user_state[call.from_user.id] = {"action": "deposit", "user": user}
    bot.send_message(call.message.chat.id, "Введите сумму для депозита:")

# Обработчик ввода суммы депозита
@bot.message_handler(func=lambda message: user_state.get(message.chat.id, {}).get("action") == "deposit")
def process_deposit_amount(message):
    try:
        amount = int(message.text)
        user = user_state[message.chat.id]["user"]
        current_balance = db.deposit_user_balance(user, amount)

        bot.send_message(
            message.chat.id,
            f"Депозит {amount} рублей успешно зачислен пользователю {user}. Текущий баланс: {current_balance} руб."
        )
        user_state.pop(message.chat.id, None)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")

# Обработчик кнопки "Pay all"
@bot.message_handler(func=lambda message: message.text == "Pay all")
def handle_pay_all(message):
    if not is_authorized(message):
        return

    db.purchase_all_users(50)
    bot.send_message(message.chat.id, "Со всех пользователей списано 50 рублей.")

# Обработчик кнопки "Show balances"
@bot.message_handler(func=lambda message: message.text == "Show balances")
def show_balances(message):
    if not is_authorized(message):
        return

    table = pt.PrettyTable(["User", "Balance", "Duration"])
    table.align = "l"
    for user, balance in db.get_all_balances():
        table.add_row([user, balance, balance / 50])

    bot.send_message(message.chat.id, f"<pre>{table}</pre>", parse_mode="HTML")

# Обработчик кнопки "New user"
@bot.message_handler(func=lambda message: message.text == "New user")
def handle_new_user(message):
    if not is_authorized(message):
        return

    bot.send_message(message.chat.id, "Введите <user_name> <balance(optional)>")
    bot.register_next_step_handler(message, create_user)

# Создание нового пользователя
def create_user(message):
    try:
        parts = message.text.split()
        name = parts[0]
        balance = int(parts[1]) if len(parts) > 1 else 0

        db.create_user(name, balance)
        bot.send_message(message.chat.id, f"Пользователь '{name}' успешно создан.")
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Ошибка ввода. Попробуйте снова.")

# Обработчик кнопки "Remove user"
@bot.message_handler(func=lambda message: message.text == "Remove user")
def handle_remove_user(message):
    if not is_authorized(message):
        return

    bot.send_message(message.chat.id, "Введите имя пользователя для удаления:")
    bot.register_next_step_handler(message, remove_user)

# Удаление пользователя
def remove_user(message):
    user_name = message.text.strip()
    db.del_user(user_name)
    bot.send_message(message.chat.id, f"Пользователь '{user_name}' удален.")

# Основной цикл бота
while True:
    try:
        bot.polling()
    except Exception as e:
        print(e)
