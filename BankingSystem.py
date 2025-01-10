import sqlite3
import random
import re
import hashlib

# Database setup
conn = sqlite3.connect('banking_system.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    dob TEXT NOT NULL,
    city TEXT NOT NULL,
    password TEXT NOT NULL,
    balance REAL NOT NULL,
    contact_number TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    active INTEGER DEFAULT 1
)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

conn.commit()

# Utility functions
def validate_password(password):
    pattern = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    return bool(pattern.match(password))

def validate_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return bool(pattern.match(email))

def validate_contact(contact):
    return bool(re.match(r'^\d{10}$', contact))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_account_number():
    return str(random.randint(10**9, 10**10 - 1))

def add_user():
    print("\n--- Add User ---")
    name = input("Enter name: ")
    dob = input("Enter date of birth (YYYY-MM-DD): ")
    city = input("Enter city: ")
    address = input("Enter address: ")
    contact = input("Enter contact number: ")
    email = input("Enter email: ")
    
    if not validate_contact(contact):
        print("Invalid contact number. Must be 10 digits.")
        return
    
    if not validate_email(email):
        print("Invalid email address.")
        return

    while True:
        password = input("Enter password (min 8 chars, upper, lower, digit, special char): ")
        if validate_password(password):
            password = hash_password(password)
            break
        print("Invalid password format.")

    balance = float(input("Enter initial balance (minimum 2000): "))
    if balance < 2000:
        print("Initial balance must be at least 2000.")
        return

    account_number = generate_account_number()

    try:
        c.execute('''INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, account_number, dob, city, password, balance, contact, email, address))
        conn.commit()
        print(f"User added successfully! Account Number: {account_number}")
    except sqlite3.IntegrityError:
        print("Failed to add user. Account number might already exist.")

def show_users():
    print("\n--- Show Users ---")
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    for row in rows:
        print(f"\nID: {row[0]}\nName: {row[1]}\nAccount Number: {row[2]}\nDOB: {row[3]}\nCity: {row[4]}\nBalance: {row[6]}\nContact: {row[7]}\nEmail: {row[8]}\nAddress: {row[9]}\nActive: {'Yes' if row[10] else 'No'}")

def login():
    print("\n--- Login ---")
    acc_number = input("Enter account number: ")
    password = hash_password(input("Enter password: "))

    c.execute("SELECT * FROM users WHERE account_number = ? AND password = ?", (acc_number, password))
    user = c.fetchone()

    if user:
        if not user[10]:
            print("Account is deactivated.")
            return

        print("Login successful.")
        while True:
            print("\n1. Show Balance\n2. Show Transactions\n3. Credit Amount\n4. Debit Amount\n5. Transfer Amount\n6. Activate/Deactivate Account\n7. Change Password\n8. Update Profile\n9. Logout")
            choice = input("Enter choice: ")

            if choice == '1':
                print(f"Balance: {user[6]}")

            elif choice == '2':
                c.execute("SELECT * FROM transactions WHERE account_number = ?", (acc_number,))
                transactions = c.fetchall()
                for t in transactions:
                    print(f"{t[3]} - {t[2]}: {t[1]}")

            elif choice == '3':
                amount = float(input("Enter amount to credit: "))
                c.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, acc_number))
                c.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'Credit', ?)", (acc_number, amount))
                conn.commit()
                print("Amount credited.")

            elif choice == '4':
                amount = float(input("Enter amount to debit: "))
                if amount > user[6]:
                    print("Insufficient balance.")
                else:
                    c.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, acc_number))
                    c.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'Debit', ?)", (acc_number, amount))
                    conn.commit()
                    print("Amount debited.")

            elif choice == '5':
                target_acc = input("Enter target account number: ")
                amount = float(input("Enter amount to transfer: "))

                if amount > user[6]:
                    print("Insufficient balance.")
                else:
                    c.execute("SELECT * FROM users WHERE account_number = ?", (target_acc,))
                    target_user = c.fetchone()

                    if target_user:
                        c.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, acc_number))
                        c.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, target_acc))
                        c.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'Transfer Out', ?)", (acc_number, amount))
                        c.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'Transfer In', ?)", (target_acc, amount))
                        conn.commit()
                        print("Amount transferred.")
                    else:
                        print("Target account not found.")

            elif choice == '6':
                new_status = 0 if user[10] else 1
                c.execute("UPDATE users SET active = ? WHERE account_number = ?", (new_status, acc_number))
                conn.commit()
                print("Account status updated.")
                break

            elif choice == '7':
                while True:
                    new_password = input("Enter new password: ")
                    if validate_password(new_password):
                        new_password = hash_password(new_password)
                        c.execute("UPDATE users SET password = ? WHERE account_number = ?", (new_password, acc_number))
                        conn.commit()
                        print("Password updated.")
                        break
                    print("Invalid password format.")

            elif choice == '8':
                city = input("Enter new city: ")
                address = input("Enter new address: ")
                contact = input("Enter new contact number: ")
                email = input("Enter new email: ")

                if not validate_contact(contact):
                    print("Invalid contact number.")
                    continue

                if not validate_email(email):
                    print("Invalid email.")
                    continue

                c.execute("UPDATE users SET city = ?, address = ?, contact_number = ?, email = ? WHERE account_number = ?", (city, address, contact, email, acc_number))
                conn.commit()
                print("Profile updated.")

            elif choice == '9':
                print("Logged out.")
                break

            else:
                print("Invalid choice.")
    else:
        print("Invalid credentials.")

def main():
    while True:
        print("\n--- Banking System ---")
        print("1. Add User\n2. Show Users\n3. Login\n4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            add_user()
        elif choice == '2':
            show_users()
        elif choice == '3':
            login()
        elif choice == '4':
            print("Exiting system.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

conn.close()
