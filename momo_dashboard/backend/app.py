from flask import Flask, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from parser import setup_database, insert_transactions_from_xml

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend requests

# Categories (use for display or filtering)
categories = {
    "incoming_money": "Incoming Money",
    "payments_to_code_holders": "Payments to Code Holders",
    "transfers_to_mobile_numbers": "Transfers to Mobile Numbers",
    "bank_deposits": "Bank Deposits",
    "airtime_bill_payments": "Airtime Bill Payments",
    "cash_power": "Cash Power Bill Payments",
    "withdrawal": "Withdrawals from Agents",
    "bank_transfer": "Bank Transfers",
    "pack": "Internet and Voice Bundle Purchases",
    "third_party": "Transactions Initiated by Third Parties",
    "uncategorized": "Uncategorized"
}

# Database configuration
DB_CONFIG = {
    "dbname": "momo_pay",
    "user": "postgres",
    "password": "Kofigershon",
    "host": "localhost",
    "port": "5432"
}

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all transactions
        cursor.execute("SELECT * FROM transactions ORDER BY readable_date DESC")
        transactions = cursor.fetchall()

        # Total transaction volume
        cursor.execute("SELECT SUM(amount) AS total_amount FROM transactions")
        total_amount = cursor.fetchone()["total_amount"]

        conn.close()

        # Append total to each transaction for frontend use (or send separately)
        for tx in transactions:
            tx["total_transactions"] = total_amount

        return jsonify(transactions)

    except Exception as e:
        print("Error fetching transactions:", e)
        return jsonify({"error": "Failed to fetch transactions"}), 500

if __name__ == "__main__":
    setup_database()  # Create table if it doesn't exist
    insert_transactions_from_xml("mtn_sms.xml")  # Optional: parse XML only once
    print("Data processing completed! Backend running at http://127.0.0.1:5000")
    app.run(debug=True)
