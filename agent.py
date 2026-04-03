import os
import json
from decimal import Decimal
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ── Database setup ────────────────────────────────────────────────────────────

def setup_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id SERIAL PRIMARY KEY,
            question TEXT,
            sql TEXT,
            answer TEXT,
            tokens_turn1 INTEGER,
            tokens_turn2 INTEGER,
            tokens_total INTEGER,
            error TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price NUMERIC
        );
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date DATE
        );
    """)

    # Seed only if empty
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO customers (name, email) VALUES
                ('Alice', 'alice@example.com'),
                ('Bob',   'bob@example.com'),
                ('Carol', 'carol@example.com');

            INSERT INTO products (name, price) VALUES
                ('Laptop',   999.99),
                ('Mouse',     29.99),
                ('Monitor',  399.99),
                ('Keyboard',  79.99);

            INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES
                (1, 1, 1, '2024-01-10'),
                (1, 2, 2, '2024-01-15'),
                (2, 3, 1, '2024-02-01'),
                (2, 4, 1, '2024-02-03'),
                (3, 1, 2, '2024-03-05'),
                (3, 2, 1, '2024-03-06');
        """)

    return conn

# ── Tool implementation ───────────────────────────────────────────────────────

def get_schema(conn) -> str:
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    rows = cur.fetchall()

    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, []).append(f"{column} ({dtype})")

    return "\n".join(f"{table}({', '.join(cols)})" for table, cols in schema.items())

def run_sql(conn, query: str) -> list[dict]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    return [{k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in cur.fetchall()]

# ── Agent loop ────────────────────────────────────────────────────────────────

def ask(question: str, conn) -> dict:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    schema = get_schema(conn)

    # Turn 1: generate SQL as plain text
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"""You are a data analyst. Output ONLY a valid PostgreSQL SELECT query with no explanation, no markdown, no code fences.
Database schema:
{schema}
Never modify data."""},
            {"role": "user", "content": question},
        ],
    )

    query = response.choices[0].message.content.strip().strip("`").strip()
    if not query.upper().startswith("SELECT"):
        error_msg = "I can only answer questions about the data. Try asking about orders, customers, or products."
        conn.cursor().execute(
            "INSERT INTO query_logs (question, error) VALUES (%s, %s)", (question, error_msg)
        )
        return {"error": error_msg}

    print(f"Generated SQL:\n  {query}\n")

    try:
        rows = run_sql(conn, query)
    except Exception as e:
        return {"error": f"SQL error: {e}", "sql": query}
    print(f"Query results: {rows}\n")

    # Turn 2: plain English answer
    response2 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful data analyst. Answer the user's question in one concise sentence using the data provided."},
            {"role": "user", "content": f"Question: {question}\nData: {json.dumps(rows)}"},
        ],
    )

    tokens = {
        "turn1": response.usage.total_tokens,
        "turn2": response2.usage.total_tokens,
        "total": response.usage.total_tokens + response2.usage.total_tokens,
    }
    print(f"Tokens — turn1: {tokens['turn1']}, turn2: {tokens['turn2']}, total: {tokens['total']}")

    answer = response2.choices[0].message.content
    conn.cursor().execute(
        """INSERT INTO query_logs (question, sql, answer, tokens_turn1, tokens_turn2, tokens_total)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (question, query, answer, tokens["turn1"], tokens["turn2"], tokens["total"])
    )

    return {"sql": query, "rows": rows, "answer": answer, "tokens": tokens}

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    conn = setup_db()
    result = ask("How many customers in total?", conn)
    print("SQL:   ", result["sql"])
    print("Rows:  ", result["rows"])
    print("Answer:", result["answer"])
