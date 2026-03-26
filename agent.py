import os
from decimal import Decimal
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from google import genai
from google.genai import types

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
    # Get all user tables (excludes postgres internal tables)
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # returns dicts, like sqlite3.Row
    cur.execute(query)
    return [{k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in cur.fetchall()]

# ── Gemini tool definition ────────────────────────────────────────────────────

tools = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="run_sql",
            description="Runs a SQL query against the sales database and returns the results.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="A valid SQLite SELECT query")
                },
                required=["query"]
            )
        )
    ])
]

# ── Agent loop ────────────────────────────────────────────────────────────────

def ask(question: str, conn) -> dict:
    client = genai.Client()
    schema = get_schema(conn)
    system_prompt = f"""You are a data analyst. When asked a question, call run_sql with a PostgreSQL query.
Database schema:
{schema}
Return only SELECT queries. Never modify data."""

    # Turn 1: Gemini decides to call run_sql
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools
        )
    )

    part = response.candidates[0].content.parts[0]
    if not part.function_call:  # Gemini answered in text — question isn't data-related
        msg = "I can only answer questions about the data. Try asking about orders, customers, or products."
        conn.cursor().execute(
            "INSERT INTO query_logs (question, error) VALUES (%s, %s)", (question, msg)
        )
        return {"error": msg}

    query = part.function_call.args["query"]
    print(f"Generated SQL:\n  {query}\n")

    try:
        rows = run_sql(conn, query)
    except Exception as e:
        return {"error": f"SQL error: {e}", "sql": query}
    print(f"Query results: {rows}\n")

    # Turn 2: Send results back, get plain English answer
    response2 = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(role="user",  parts=[types.Part(text=question)]),
            types.Content(role="model", parts=[types.Part(function_call=part.function_call)]),
            types.Content(role="user",  parts=[
                types.Part(function_response=types.FunctionResponse(
                    name="run_sql",
                    response={"result": rows}
                ))
            ])
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools
        )
    )

    tokens = {
        "turn1": response.usage_metadata.total_token_count,
        "turn2": response2.usage_metadata.total_token_count,
        "total": response.usage_metadata.total_token_count + response2.usage_metadata.total_token_count,
    }
    print(f"Tokens — turn1: {tokens['turn1']}, turn2: {tokens['turn2']}, total: {tokens['total']}")

    conn.cursor().execute(
        """INSERT INTO query_logs (question, sql, answer, tokens_turn1, tokens_turn2, tokens_total)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (question, query, response2.text, tokens["turn1"], tokens["turn2"], tokens["total"])
    )

    return {"sql": query, "rows": rows, "answer": response2.text, "tokens": tokens}

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    conn = setup_db()
    result = ask("How many customers in total?", conn)
    print("SQL:   ", result["sql"])
    print("Rows:  ", result["rows"])
    print("Answer:", result["answer"])
