import sqlite3


class Database:
    def __init__(self):
        self.con = sqlite3.connect('CashLogger.db', check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS CashLogger ("
                    "id INTEGER PRIMARY KEY,"
                    " user TEXT UNIQUE NOT NULL,"
                    " balance INTEGER CHECK (typeof(balance) = 'integer'))")
        self.con.commit()

    def execute(self, query, *args):
        self.cur.execute(query, args)
        self.con.commit()
        return self.cur.fetchall()

    def get_tables(self):
        return self.execute("SELECT name FROM sqlite_master")

    def get_all_users(self):
        all_users = self.execute("SELECT user FROM CashLogger")
        user_names = [item[0] for item in all_users]
        print(type(user_names))
        return user_names

    def create_user(self, user, balance):
        self.execute("INSERT INTO CashLogger (user, balance) VALUES (?, ?)",
                         user, int(balance))

    def deposit_user_balance(self, user, balance):
        self.execute("UPDATE CashLogger SET balance = balance + ? WHERE user = ?",
                         int(balance), user)
        cur_balance = self.execute("SELECT balance FROM CashLogger WHERE user = ? ", user)
        cur_balance = [item[0] for item in cur_balance]
        return cur_balance[0]

    def purchase_all_users(self, price):
        self.execute("UPDATE CashLogger SET balance = balance - ?",
                         price)

    def del_user(self, user):
        self.execute("DELETE FROM CashLogger WHERE user = ?",user)

    def get_all_balances(self):
        balances = self.execute("SELECT user, balance FROM CashLogger")
        return balances
