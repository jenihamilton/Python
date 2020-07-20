import random
import sqlite3
import sys


conn = sqlite3.connect('mybank.s3db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
create_table = """
    CREATE TABLE IF NOT EXISTS mybank (
        id INTEGER PRIMARY KEY NOT NULL,
        number TEXT NOT NULL,
        pin TEXT NOT NULL,
        balance INTEGER DEFAULT 0)"""
cur.execute(create_table)
conn.commit()


class Bank:
    def __init__(self):
        self.tries = 3
        self.user_account = None

    def main_menu(self):
        print(f"1. Create an account\n2. Log into account\n0. Exit")
        option_a = input()
        if option_a == '1':
            self.create_account()
        elif option_a == '2':
            self.login()
        elif option_a == '0':
            print("\nBye!")
            sys.exit()
        else:
            print("\nPlease select a menu option to continue.\n")
            self.main_menu()

    @staticmethod
    def luhn_checksum(num):
        """Return Checksum number for account number using Luhn Algorithm."""
        luhn = [int(n) for n in str(num)[:-1]]
        luhn = [luhn[i] * 2 if i % 2 == 0 else luhn[i] for i in range(len(luhn))]
        luhn = sum([(n - 9) if n > 9 else n for n in luhn])
        checksum = 0 if luhn % 10 == 0 else 10 - (luhn % 10)
        return checksum

    def create_account(self):
        iin = 400000
        customer_number = random.randrange(100000000, 999999999)
        num = f'{iin}{customer_number}0'
        checksum = self.luhn_checksum(num)
        card_number = f'{iin}{customer_number}{checksum}'
        pin = f'{random.randrange(1000, 9999)}'
        cur.execute('INSERT INTO mybank VALUES(?, ?, ?, ?)', (customer_number, card_number, pin, 0))
        conn.commit()
        print(f"\nYour account has been created\nYour account number:\n{card_number}\nYour PIN:\n{pin}\n")
        self.main_menu()

    def login(self):
        for i in range(self.tries):
            tries = 'tries' if self.tries - (i + 1) > 1 else 'try'
            try:
                print("\nEnter your account number: ")
                user_number = input()
                print("Enter your PIN: ")
                user_pin = input()
                if not user_number.isdigit() or not user_pin.isdigit():
                    raise ValueError
            except ValueError:
                print(f"\nPlease enter numbers only. "
                      f"{f'{self.tries - (i + 1)} {tries} left.' if i < self.tries - 1 else ''}")
            else:
                db = cur.execute('SELECT * FROM mybank')
                for entry in db:
                    if entry[1] == user_number and entry[2] == user_pin:
                        print("\nYou have successfully logged in!\n")
                        self.user_account = user_number
                        self.account_menu()
                        break
                else:
                    print(f"\nWrong account number or PIN! "
                          f"{f'{self.tries - (i + 1)} {tries} left.' if i < self.tries - 1 else ''}")
        else:
            print("\nPlease check your account info and try again later. Goodbye.")
            sys.exit()

    def account_menu(self):
        print(f"1. Balance\n2. Add funds\n3. Withdraw funds\n4. Account transfer\n5. Close account\n6. Log out\n"
              f"0. Exit")
        option_b = input()
        if option_b == '1':
            self.check_balance()
        elif option_b == '2':
            self.add_withdraw_funds('add')
        elif option_b == '3':
            self.add_withdraw_funds('withdraw')
        elif option_b == '4':
            self.account_transfer()
        elif option_b == '5':
            self.close_account()
        elif option_b == '6':
            print("\nYou have successfully logged out!\n")
            self.main_menu()
        elif option_b == '0':
            print('\nBye!')
            sys.exit()
        else:
            print("\nPlease select a menu option to continue.\n")
            self.account_menu()

    def check_balance(self):
        cur.execute('SELECT balance FROM mybank WHERE number = ?', (self.user_account,))
        result = cur.fetchone()
        print(f"\nBalance: {result['balance']}\n")
        self.account_menu()

    def add_withdraw_funds(self, action):
        while True:
            try:
                print("\nEnter amount: ")
                amount = int(input())
                break
            except ValueError:
                print("\nPlease enter numbers only.")
        if action == 'add':
            cur.execute('UPDATE mybank SET balance = balance + ? WHERE number = ?', (amount, self.user_account))
            conn.commit()
            print(f"\n{amount} was successfully added to your account.\n")
            self.account_menu()
        elif action == 'withdraw':
            cur.execute('SELECT balance FROM mybank WHERE number = ?', (self.user_account,))
            result = cur.fetchone()
            if int(amount) < result['balance']:
                cur.execute('UPDATE mybank SET balance = balance - ? WHERE number = ?', (amount, self.user_account))
                conn.commit()
                print(f"\n{amount} was successfully withdrawn from your account.\n")
            else:
                print(f"\nInsufficient funds.\n")
            self.account_menu()

    def account_transfer(self):
        while True:
            try:
                print("\nTransfer\nEnter card number: ")
                transfer_account = input()
                if transfer_account == self.user_account:
                    print("\nYou cannot transfer funds to the same account.\n")
                    self.account_menu()
                if len(transfer_account) != 16 or int(transfer_account[-1]) != self.luhn_checksum(transfer_account) or \
                        not transfer_account.isdigit():
                    raise ValueError
                break
            except ValueError:
                print("\nThis is not a valid account number. Please try again.")
        cur.execute('SELECT * FROM mybank WHERE number = ?', (transfer_account,))
        result = cur.fetchone()
        if result is None:
            print("\nThis account does not exist.\n")
            self.account_menu()
        else:
            while True:
                try:
                    print("\nEnter how much you want to transfer: ")
                    transfer_amount = int(input())
                    break
                except ValueError:
                    print("\nPlease enter numbers only.")
            cur.execute('SELECT balance FROM mybank WHERE number = ?', (self.user_account,))
            result = cur.fetchone()
            if transfer_amount > result['balance']:
                print("\nNot enough in account.\n")
                self.account_menu()
            else:
                cur.execute('UPDATE mybank SET balance = balance + ? WHERE number = ?',
                            (transfer_amount, transfer_account))
                cur.execute('UPDATE mybank SET balance = balance - ? WHERE number = ?',
                            (transfer_amount, self.user_account))
                conn.commit()
                print(f"\nSuccess! {transfer_amount} has been transferred to account {transfer_account}.\n")
                self.account_menu()

    def close_account(self):
        print("\nAre you sure? This action cannot be undone. Y/N")
        check = input().upper()
        try:
            if check not in ('Y', 'N'):
                raise ValueError
        except ValueError:
            print("\nPlease enter Y or N to continue.")
            self.close_account()
        else:
            if check == 'N':
                self.account_menu()
            else:
                cur.execute('DELETE FROM mybank WHERE number = ?', (self.user_account,))
                conn.commit()
                print(f"\nAccount {self.user_account} has been closed.\n")
                self.main_menu()


if __name__ == '__main__':
    bank = Bank()
    bank.main_menu()
