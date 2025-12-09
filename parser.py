import requests
import sqlite3
import csv
from datetime import datetime

DB = "tenders.db"
CSV = "tenders.csv"
KEYWORDS_FILE = "keywords.txt"

def load_keywords():
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        return [k.strip() for k in f.readlines() if k.strip()]

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id TEXT PRIMARY KEY,
        title TEXT,
        organizer TEXT,
        start_date TEXT,
        end_date TEXT,
        price TEXT,
        url TEXT,
        updated TEXT
    )
    """)
    conn.commit()
    conn.close()

def search_tenders():
    results = []
    keywords = load_keywords()
    for word in keywords:
        url = f"https://api.sk.kz/api/tenders/search?query={word}"
        try:
            r = requests.get(url, timeout=15)
        except:
            continue
        if r.status_code != 200:
            continue
        data = r.json()
        for item in data.get("data", []):
            tender_id = str(item["id"])
            results.append({
                "id": tender_id,
                "title": item.get("name"),
                "organizer": item.get("organizer_name"),
                "start": item.get("start_date"),
                "end": item.get("end_date"),
                "price": item.get("amount"),
                "url": f"https://zakup.sk.kz/tender/{tender_id}"
            })
    return results

def save_to_db(rows):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for r in rows:
        cur.execute("""
        INSERT OR REPLACE INTO tenders
        (id, title, organizer, start_date, end_date, price, url, updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"], r["title"], r["organizer"], r["start"], r["end"],
            r["price"], r["url"], datetime.utcnow().isoformat()
        ))
    conn.commit()
    conn.close()

def export_csv():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM tenders").fetchall()
    conn.close()
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Название", "Организатор", "Начало", "Конец",
                    "Сумма", "Ссылка", "Обновлено"])
        w.writerows(rows)

if __name__ == "__main__":
    init_db()
    tenders = search_tenders()
    save_to_db(tenders)
    export_csv()
