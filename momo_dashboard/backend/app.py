from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from parser import setup_database, insert_transactions_from_xml
import os

# Set frontend directory path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_FOLDER = os.path.join(BASE_DIR, "frontend")

# Configure Flask to use frontend folder
app = Flask(
    __name__,
    static_folder=FRONTEND_FOLDER,
    template_folder=FRONTEND_FOLDER
)

CORS(app)  # Enable Cross-Origin Resource Sharing for frontend requests

# Categories (used for display or filtering)
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

# Route to serve index.html
@app.route('/')
def home():
    return render_template("index.html")

# Serve static files (like CSS, JS) from frontend folder
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)

# Route to return transaction data
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

        for tx in transactions:
            tx["total_transactions"] = total_amount

        return jsonify(transactions)

    except Exception as e:
        print("Error fetching transactions:", e)
        return jsonify({"error": "Failed to fetch transactions"}), 500

if __name__ == "__main__":
    setup_database()  # Create table if it doesn't exist
    insert_transactions_from_xml("mtn_sms.xml")  # Optional: parse XML only once
    print("✅ Backend running at http://127.0.0.1:5000")
    app.run(debug=True)
