import psycopg2
from psycopg2.errors import DuplicateTable
import xml.etree.ElementTree as ET
import re
import json
import os
from datetime import datetime

# === CONFIG ===
DB_CONFIG = {
    "dbname": "momo_pay",
    "user": "postgres",
    "password": "Kofigershon",
    "host": "localhost",
    "port": "5432"
}
XML_FILE = os.path.join(os.path.dirname(__file__), "..", "frontend", "sms_data.xml")


def categorize_transaction(description):
    description = description.lower()

    if "received" in description:
        return "incoming_money"
    elif "transferred to" in description:
        return "transfers_to_mobile_numbers"
    elif "bank deposit" in description:
        return "bank_deposits"
    elif "airtime" in description:
        return "airtime_bill_payments"
    elif "power" in description:
        return "cash_power"
    elif "withdrawn" in description or "agent withdrawal" in description:
        return "withdrawal"
    elif "transferred" in description and "bank" in description:
        return "bank_transfer"
    elif "voice" in description or "pack" in description:
        return "pack"
    elif "third party" in description:
        return "third_party"
    elif "payment of" in description:
        return "payments_to_code_holders"

    return "uncategorized"


def setup_database():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                body TEXT,
                amount NUMERIC(10, 2),
                balance NUMERIC(10, 2),
                readable_date TIMESTAMP,
                category VARCHAR(50),
                transaction_id VARCHAR(60) UNIQUE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transaction_details (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(60) REFERENCES transactions(transaction_id),
                status VARCHAR(50),
                description TEXT,
                additional_info JSONB
            );
        """)

        conn.commit()
        print("✅ Database setup completed.")
        insert_transactions_from_xml(XML_FILE)

    except Exception as e:
        print("❌ Error during DB setup:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()


def insert_transaction_details(conn, cur, transaction_id, status, description, additional_info):
    if transaction_id == "N/A":
        return

    try:
        cur.execute("""
            INSERT INTO transaction_details (transaction_id, status, description, additional_info)
            VALUES (%s, %s, %s, %s)
        """, (transaction_id, status, description, json.dumps(additional_info)))
        conn.commit()
    except Exception as e:
        print(f"❌ Error inserting transaction details: {e}")
        conn.rollback()


def insert_transactions_from_xml(xml_file_path):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    categories = {
        "incoming_money": [],
        "payments_to_code_holders": [],
        "transfers_to_mobile_numbers": [],
        "bank_deposits": [],
        "airtime_bill_payments": [],
        "cash_power": [],
        "withdrawal": [],
        "bank_transfer": [],
        "pack": [],
        "third_party": [],
        "uncategorized": []
    }

    try:
        tree = ET.parse(xml_file_path)
    except Exception as e:
        print(f"❌ Could not parse XML: {e}")
        return

    root = tree.getroot()
    default_transaction = 1

    for sms in root.findall("sms"):
        body = sms.get("body", "")
        readable_date = sms.get("readable_date", "")
        try:
            readable_date = datetime.strptime(readable_date, "%b %d, %Y %I:%M:%S %p")
        except:
            readable_date = datetime.now()

        if "one-time password" in body:
            continue

        amount_match = re.search(r"([\d,]+) RWF", body) or re.search(r"RWF ([\d,]+)", body)
        balance_match = re.search(r"balance.*?([\d,]+).*?\.", body.lower())

        amount = int(str(amount_match.group(1)).replace(',', '')) if amount_match else 0
        balance = int(str(balance_match.group(1)).replace(',', '')) if balance_match else 0

        txid_match = re.search(r"TxId:\s?(\d+)", body)
        transaction_id = txid_match.group(1) if txid_match else f"tx_{default_transaction}"
        default_transaction += 1

        category = categorize_transaction(body)
        categories[category].append({
            "transaction_id": transaction_id,
            "amount": amount,
            "date": readable_date.isoformat(),
            "body": body
        })

        try:
            cur.execute("""
                INSERT INTO transactions (amount, balance, body, readable_date, category, transaction_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (amount, balance, body, readable_date, category, transaction_id))

            insert_transaction_details(conn, cur, transaction_id, "Completed", "Transaction completed", {"note": "Parsed from XML"})
            conn.commit()

        except Exception as e:
            print(f"⚠️ Skipped inserting transaction {transaction_id}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("✅ Transactions parsed and inserted.")

    # Save uncategorized logs
    if categories["uncategorized"]:
        with open("uncategorized_logs.json", "w") as log_file:
            json.dump(categories["uncategorized"], log_file, indent=4)
        print("⚠️ Some transactions were uncategorized. Logged to 'uncategorized_logs.json'")


# Entry point
if __name__ == "__main__":
    setup_database()
