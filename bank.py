import gradio as gr
import mysql.connector
from mysql.connector import pooling

# Connection Pooling
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Welcome@2020",
    "database": "banking_system",
    "pool_name": "mypool",
    "pool_size": 5
}
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def connect_db():
    return connection_pool.get_connection()

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255),
                        username VARCHAR(255) UNIQUE,
                        password VARCHAR(255),
                        balance DECIMAL(10,2) DEFAULT 0.0)''')
    cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_username'")
    if not cursor.fetchone():
        cursor.execute("CREATE INDEX idx_username ON users(username)")
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255),
                        type VARCHAR(50),
                        amount DECIMAL(10,2),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    cursor.close()
    conn.close()

create_tables()

def create_account(name, username, password):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, username, password, balance) VALUES (%s, %s, %s, %s)", (name, username, password, 0.0))
        conn.commit()
        cursor.close()
        conn.close()
        return "✅ Account created successfully! Please log in.", gr.update(visible=False), gr.update(visible=True)
    except mysql.connector.IntegrityError:
        return "⚠️ Username already exists. Try another one.", gr.update(visible=True), gr.update(visible=False)

def login(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return f"✅ Login successful! Welcome {user[1]}", username, gr.update(visible=True)
    else:
        return "❌ Invalid credentials. Try again.", "", gr.update(visible=False)

def check_balance(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=%s", (username,))
    balance = cursor.fetchone()
    cursor.close()
    conn.close()
    return f"💰 Your balance is: ₹{balance[0]:.2f}" if balance else "⚠️ User not found."

def deposit(username, amount):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + %s WHERE username=%s", (amount, username))
    cursor.execute("INSERT INTO transactions (username, type, amount) VALUES (%s, %s, %s)", (username, 'Deposit', amount))
    conn.commit()
    cursor.close()
    conn.close()
    return check_balance(username)

def withdraw(username, amount):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=%s", (username,))
    balance = cursor.fetchone()
    if balance and balance[0] >= amount:
        cursor.execute("UPDATE users SET balance = balance - %s WHERE username=%s", (amount, username))
        cursor.execute("INSERT INTO transactions (username, type, amount) VALUES (%s, %s, %s)", (username, 'Withdraw', amount))
        conn.commit()
        cursor.close()
        conn.close()
        return check_balance(username)
    else:
        cursor.close()
        conn.close()
        return "⚠️ Insufficient funds."

def transaction_history(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE username=%s ORDER BY timestamp DESC", (username,))
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    if transactions:
        return "\n".join([f"{t[0]}: ₹{t[1]:.2f} on {t[2]}" for t in transactions])
    return "⚠️ No transactions found."

def main_interface():
    with gr.Blocks() as app:
        gr.Markdown("# 🏦 Banking System")
        
        with gr.Row():
            create_account_btn = gr.Button("🆕 Create Account")
            login_btn = gr.Button("🔑 Login")
            dashboard_btn = gr.Button("📊 Dashboard")
        
        create_account_section = gr.Column(visible=False)
        login_section = gr.Column(visible=False)
        dashboard = gr.Column(visible=False, elem_id="dashboard")
        
        create_account_btn.click(lambda: gr.update(visible=True), outputs=[create_account_section])
        login_btn.click(lambda: gr.update(visible=True), outputs=[login_section])
        
        with create_account_section:
            name = gr.Textbox(label="Name")
            username_ca = gr.Textbox(label="Username")
            password_ca = gr.Textbox(label="Password", type="password")
            create_btn = gr.Button("Create Account")
            output_ca = gr.Text()
            
            create_btn.click(create_account, inputs=[name, username_ca, password_ca], outputs=[output_ca, create_account_section, login_section])
        
        with login_section:
            username_lg = gr.Textbox(label="Username")
            password_lg = gr.Textbox(label="Password", type="password")
            login_action_btn = gr.Button("Login")
            output_lg = gr.Text()
            user_state = gr.State("")
            
            login_action_btn.click(login, inputs=[username_lg, password_lg], outputs=[output_lg, user_state, dashboard])
        
        with dashboard:
            gr.Markdown("## 📊 Dashboard", elem_id="dashboard-title")
            
            balance_btn = gr.Button("💰 Check Balance")
            balance_output = gr.Text()
            
            deposit_amt = gr.Number(label="Deposit Amount")
            deposit_btn = gr.Button("➕ Deposit")
            
            withdraw_amt = gr.Number(label="Withdraw Amount")
            withdraw_btn = gr.Button("➖ Withdraw")
            
            transaction_btn = gr.Button("📜 Transaction History")
            transaction_output = gr.Text()
            
            deposit_btn.click(deposit, inputs=[user_state, deposit_amt], outputs=balance_output)
            withdraw_btn.click(withdraw, inputs=[user_state, withdraw_amt], outputs=balance_output)
            balance_btn.click(check_balance, inputs=[user_state], outputs=balance_output)
            transaction_btn.click(transaction_history, inputs=[user_state], outputs=transaction_output)
    
    return app

main_interface().launch()
