import os
import uuid
import sqlite3

def get_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'mcb.db')
    return sqlite3.connect(db_path)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')) NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')) NOT NULL,
            deleted_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_tabung (
            id TEXT NOT NULL,
            code TEXT NOT NULL,
            type TEXT NOT NULL,
            customer_id TEXT,
            created_at TEXT DEFAULT (datetime('now')) NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')) NOT NULL,
            deleted_at TEXT,
            PRIMARY KEY (id, customer_id)
        )
    ''')

    conn.commit()
    conn.close()

def insert_customer(name):
    cust_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (id, name) VALUES (?, ?)", (cust_id, name))
    conn.commit()
    conn.close()

def insert_tabung(code, type, customer):
    conn = get_connection()
    cursor = conn.cursor()

    # ambil customer_id di table customer berdasarkan nama
    cursor.execute('select id from customers where name = ? limit 1',(customer,))
    result = cursor.fetchone()
    tbg_id = str(uuid.uuid4())
    customer_id = result[0]

    cursor.execute('''
        INSERT INTO asset_tabung
            (id, code, type, customer_id)
            VALUES (?, ?, ?, ?)''', (tbg_id, code, type, customer_id)
    )
    conn.commit()
    conn.close()

def get_data_customer():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        with total_tbg_besar as (
        select
            customer_id, type, count(id) total
        from asset_tabung
        where deleted_at is null and type = '6m3'
        group by customer_id, type
        ), total_tbg_kecil as (
        select
            customer_id, type, count(id) total
        from asset_tabung
        where deleted_at is null and type = '1m3'
        group by customer_id, type
        )
        SELECT
            c.*, a.total, b.total
        FROM customers c
        left join total_tbg_besar a on a.customer_id = c.id
        left join total_tbg_kecil b on b.customer_id = c.id
        where c.deleted_at is null
        order by c.name
    ''')
    result = cursor.fetchall()
    conn.close()
    return result

def get_customer_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        with total_tbg as (
        select customer_id, count(id) total from asset_tabung
        where deleted_at is null
        group by customer_id
        )
        SELECT c.*, a.total FROM customers c
        left join total_tbg a on a.customer_id = c.id
        where c.deleted_at is null
    ''')
    result = [row[1] for row in cursor.fetchall()]
    conn.close()
    return result

def get_data_tabung():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        select
            a.code, a.type, c.name
        from asset_tabung a
            left join customers c on a.customer_id = c.id
    ''')
    result = cursor.fetchall()
    return result