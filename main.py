from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# ---- In-memory "database" ----
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Finish assignment", "done": True},
]
next_id = 4  # tracks the next free id to assign

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
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

# ---- Create ----
@app.post("/tasks", status_code=201)
def create_task(payload: dict):
    global next_id
    title = payload.get("title")
    if not title:
        return JSONResponse(status_code=400, content={"error": "Title is required"})
    new_task = {"id": next_id, "title": title, "done": False}
    tasks.append(new_task)
    next_id += 1
    return new_task

# ---- Update ----
@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: dict):
    for task in tasks:
        if task["id"] == task_id:
            if "title" in payload:
                task["title"] = payload["title"]
            if "done" in payload:
                task["done"] = payload["done"]
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

# ---- Delete ----
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})