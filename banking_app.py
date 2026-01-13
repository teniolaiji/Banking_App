import sqlite3
import random
import re
import hashlib
from getpass import getpass
from datetime import datetime
import time


DB_FILE = "banking.db"


def set_up():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            account_number TEXT NOT NULL UNIQUE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );
        """)


def generate_unique_account_number():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

    while True:
        account_number = ''.join(str(random.randint(0, 9)) for _ in range(8))

        cursor.execute(
            "SELECT 1 FROM clients WHERE account_number = ?",
            (account_number,)
        )

        if cursor.fetchone() is None:
            return account_number


def sign_up():
    print("-------------------------------SIGN UP-------------------------------")
    while True:
        full_name = input("Enter your full name: ").strip()
        if not full_name:
            print("Full name field is required")
            continue
        if len(full_name) < 4:
            print("Full name is too short")
            continue
        if len(full_name) > 255:
            print("Full name is too long")
            continue
        if not re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)*", full_name):
            print("Full name can only contain letters and spaces")
            continue
        break

    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username field is required")
            continue
        if len(username) < 3:
            print("username is too short")
            continue
        if len(username) > 20:
            print("username is too long")
            continue
        if not re.fullmatch(r"[A-Za-z0-9_]+", username):
            print("Username can only contain letters, numbers, and underscores")
            continue

        break

    while True:
        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password field is required")
            continue
        if len(password) < 8:
            print("Password is too short")
            continue
        if len(password) > 30:
            print("Password is too long")
            continue
        if not re.fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$", password):
            print(
                "Password must be at least 8 characters long and contain:\n"
                "- one uppercase letter\n"
                "- one lowercase letter\n"
                "- one number\n"
                "- one special character"
            )
            continue
        confirm_password = getpass("Confirm your password: ").strip()

        if not confirm_password:
            print("Confirm Password field is required")
            continue

        if password != confirm_password:
            print("Passwords don't match")
            continue

        break

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    while True:
        try:
            initial_deposit = int(
                input("Enter your initial deposit: ").strip())
        except ValueError as e:
            print("Initial deposit must be an integer")
            continue
        else:
            if not initial_deposit:
                print("Initial deposit field is required")
                continue
            if initial_deposit < 0:
                print("You can only enter a positive amount")
                continue
            if initial_deposit < 2000:
                print("You must deposit a minimum of 2000 naira")
                continue
        break

    account_number = generate_unique_account_number()

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
INSERT INTO clients (full_name, username, password, balance, account_number)
VALUES (?, ?, ?, ?, ?);
""", (full_name, username, hashed_password, initial_deposit, account_number))

        except sqlite3.IntegrityError as e:
            if "clients.username" in str(e):
                print("That username is already taken")
                return

    print("Sign up Successful")
    log_in()


def log_in():
    print("-------------------------------LOG IN-------------------------------")

    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username field is required")
            continue
        break

    while True:
        password = getpass("Enter your password: ").strip()

        if not password:
            print("Password field is required")
            continue
        break

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        client = cursor.execute(
            "SELECT id, full_name, account_number FROM clients WHERE username = ? AND password = ?", (username, hashed_password)).fetchone()
        if client is None:
            print("Invalid Credentials")
        else:
            client_id, full_name, account_number = client
            print("Login Successful")
            dashboard(client_id, full_name, account_number)

def processing(message="Processing"):
    print(message, end="", flush=True)
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print()

def deposit(client_id):
    while True:
        try:
            amount = int(input("Amount to deposit: ").strip())
            if amount <= 0:
                print("Deposit amount must be greater than zero")
                continue
        except ValueError:
            print("Please enter a valid number")
            continue
        break
    
    processing("Depositing funds")

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        
        cursor.execute("""
        UPDATE clients
        SET balance = balance + ?
        WHERE id = ?
        """, (amount, client_id))

        
        cursor.execute("""
        INSERT INTO transactions (client_id, amount, transaction_type, time)
        VALUES (?, ?, ?, ?)
        """, (client_id, amount, "deposit", time))

    print(f"₦{amount} deposited successfully")



def withdraw(client_id):
    while True:
        try:
            amount = int(input("Amount to withdraw: ").strip())
            if amount <= 0:
                print("Withdrawal amount must be greater than zero")
                continue
        except ValueError:
            print("Please enter a valid number")
            continue
        break

    processing("Processing withdrawal")

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        
        cursor.execute(
            "SELECT balance FROM clients WHERE id = ?",
            (client_id,)
        )
        row = cursor.fetchone()

        if row is None:
            print("Account not found")
            return

        current_balance = row[0]

        if amount > current_balance:
            print("Insufficient funds")
            return

        
        cursor.execute("""
        UPDATE clients
        SET balance = balance - ?
        WHERE id = ?
        """, (amount, client_id))

        
        cursor.execute("""
        INSERT INTO transactions (client_id, amount, transaction_type, time)
        VALUES (?, ?, ?, ?)
        """, (client_id, amount, "withdraw", time))

    print(f"₦{amount} withdrawn successfully")



def balance_inquiry(client_id):
    processing("Fetching balance")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM clients WHERE id = ?",
            (client_id,)
        )
        result = cursor.fetchone()

        if result is None:
            print("Account not found")
            return

        balance = result[0]

    print(f"Your current balance is: ₦{balance}")



def transaction_history(client_id):
    processing("Loading transaction history")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT transaction_type, amount, time
        FROM transactions
        WHERE client_id = ?
        ORDER BY time DESC
        """, (client_id,))

        transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found.")
        return

    print("\n---------------- TRANSACTION HISTORY ----------------")
    print(f"{'TYPE':<12} {'AMOUNT':<10} {'DATE & TIME'}")
    print("-" * 50)

    for t_type, amount, time in transactions:
        print(f"{t_type:<12} ₦{amount:<9} {time}")

    print("-" * 50)



def transfer(client_id, sender_account_number):

    while True:
        try:
            amount = int(input("Enter amount to transfer: ").strip())
            if amount <= 0:
                print("Transfer amount must be greater than zero")
                continue
        except ValueError:
            print("Please enter a valid number")
            continue
        break

    
    while True:
        recipient_account = input("Enter recipient account number: ").strip()

        if not recipient_account.isdigit():
            print("Account number must be numeric")
            continue

        if recipient_account == sender_account_number:
            print("You cannot transfer money to your own account")
            continue

        break
    
    processing("Transferring funds")
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM clients WHERE id = ?",
            (client_id,)
        )
        sender = cursor.fetchone()

        if sender is None:
            print("Sender account not found")
            return

        sender_balance = sender[0]

        if amount > sender_balance:
            print("Insufficient funds")
            return

        
        cursor.execute(
            "SELECT id FROM clients WHERE account_number = ?",
            (recipient_account,)
        )
        recipient = cursor.fetchone()

        if recipient is None:
            print("Recipient account does not exist")
            return

        recipient_id = recipient[0]

    
        cursor.execute("""
        UPDATE clients
        SET balance = balance - ?
        WHERE id = ?
        """, (amount, client_id))

        cursor.execute("""
        UPDATE clients
        SET balance = balance + ?
        WHERE id = ?
        """, (amount, recipient_id))

    
        cursor.execute("""
        INSERT INTO transactions (client_id, amount, transaction_type, time)
        VALUES (?, ?, ?, ?)
        """, (client_id, amount, "transfer", time))

    print(f"₦{amount} transferred successfully")



def account_details(client_id):
    processing("Fetching account details")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT full_name, username, account_number, balance
        FROM clients
        WHERE id = ?
        """, (client_id,))

        account = cursor.fetchone()

    if account is None:
        print("No account details found")
        return

    full_name, username, account_number, balance = account

    print("\n---------------- ACCOUNT DETAILS ----------------")
    print(f"Full Name      : {full_name}")
    print(f"Username       : {username}")
    print(f"Account Number : {account_number}")
    print(f"Balance        : ₦{balance}")
    print("------------------------------------------------")





def dashboard(client_id, full_name, account_number):
    print("-------------------------------DASHBOARD-------------------------------")
    print(f"Welcome {full_name}! Your account number is {account_number}")
    dashboard_menu = """
1. Deposit
2. Withdraw
3. Balance Inquiry
4. Transaction History
5. Transfer
6. Account Details 
7. Log out
"""
    while True:
        print(dashboard_menu)

        choice = input("Choose an option from the menu above: ").strip()

        if choice == "1":
            deposit(client_id)
        elif choice == "2":
            withdraw(client_id)
        elif choice == "3":
            balance_inquiry(client_id)
        elif choice == "4":
            transaction_history(client_id)
        elif choice == "5":
            transfer(client_id, account_number)
        elif choice == "6":
            account_details(client_id)
        elif choice == "7":
            print("Logged out successfully")
            break
        else:
            print("Invalid choice")


set_up()
menu = """
1. Sign Up
2. Log In
3. Quit
"""

while True:
    print("-------------------------------Welcome to your banking app-------------------------------")
    print(menu)
    choice = input("Choose an ooption from the menu above: ").strip()
    if choice == "1":
        sign_up()
    elif choice == "2":
        log_in()
    elif choice == "3":
        print("Goodbye")
        break
    else:
        print("You can only select an option from 1-3. Please try again.")
