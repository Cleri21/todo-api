from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()  # reads your .env file and loads DATABASE_URL

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]

# ---- Database setup ----
def get_db():
    return psycopg.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Buy milk", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Walk the dog", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Finish assignment", True))
    conn.commit()
    cur.close()
    conn.close()

init_db()

def row_to_dict(row):
    return {"id": row[0], "title": row[1], "done": row[2]}

# ---- Root & health ----
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---- Read ----
@app.get("/tasks")
def get_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row_to_dict(r) for r in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    return row_to_dict(row)

# ---- Create ----
@app.post("/tasks", status_code=201)
def create_task(payload: dict):
    title = payload.get("title")
    if not title:
        return JSONResponse(status_code=400, content={"error": "Title is required"})
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
        (title, False)
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row_to_dict(row)

# ---- Update ----
@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    new_title = payload.get("title", row[1])
    new_done = payload.get("done", row[2])

    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
        (new_title, new_done, task_id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row_to_dict(updated)

# ---- Delete ----
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return