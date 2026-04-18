from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import (
    RegisterInput, LoginInput, AuthResponse, UserInDB, UserOut, UserUpdate, PasswordChange,
    CreateUserInput,
    ProjectCreate, ProjectUpdate, ProjectInDB,
    TaskCreate, TaskUpdate, TaskInDB,
    SubtaskCreate, SubtaskUpdate, SubtaskInDB,
    CommentCreate, CommentInDB,
    NotificationInDB,
)
from auth import hash_password, verify_password, create_token, get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'promanage')]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ===== HELPERS =====
def user_to_out(u: dict) -> dict:
    return {k: v for k, v in u.items() if k not in ('password_hash', '_id')}


async def compute_project_progress(project_id: str) -> int:
    tasks = await db.tasks.find({"projectId": project_id}).to_list(1000)
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.get('status') == 'Selesai')
    return round((done / len(tasks)) * 100)


async def create_notification(ntype: str, message: str, target_email: str, task_id: str = None):
    notif = NotificationInDB(
        type=ntype,
        taskId=task_id,
        message=message,
        targetEmail=target_email,
    )
    await db.notifications.insert_one(notif.dict())


# ===== AUTH =====
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    existing = await db.users.find_one({"$or": [{"phone": data.phone}, {"email": data.email}]})
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")
    # First user in the system becomes Manager
    users_count = await db.users.count_documents({})
    role = "Manager" if users_count == 0 else "Anggota Tim"
    user = UserInDB(
        name=data.name,
        phone=data.phone,
        email=data.email or "",
        role=role,
        password_hash=hash_password(data.password),
    )
    await db.users.insert_one(user.dict())
    token = create_token(user.id, user.email or "", user.role)
    return {"user": user_to_out(user.dict()), "token": token}


@api_router.post("/auth/login")
async def login(data: LoginInput):
    user = await db.users.find_one({
        "$or": [{"email": data.identifier}, {"phone": data.identifier}],
        "deletedAt": None
    })
    if not user or not verify_password(data.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Kredensial tidak valid")
    token = create_token(user['id'], user.get('email', ''), user['role'])
    return {"user": user_to_out(user), "token": token}


@api_router.get("/auth/me")
async def get_me(current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"], "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user_to_out(user)


# ===== USERS =====
@api_router.get("/users")
async def get_users(current=Depends(get_current_user)):
    users = await db.users.find({"deletedAt": None}).to_list(1000)
    return [user_to_out(u) for u in users]


@api_router.post("/users")
async def create_user(data: CreateUserInput, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    existing = await db.users.find_one({"$or": [{"phone": data.phone}, {"email": data.email}]})
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")
    valid_roles = ["Admin", "Team Lead", "Anggota Tim"]
    role = data.role if data.role in valid_roles else "Anggota Tim"
    user = UserInDB(
        name=data.name,
        phone=data.phone,
        email=data.email or "",
        role=role,
        password_hash=hash_password(data.password),
        createdBy=current["sub"],
    )
    await db.users.insert_one(user.dict())
    return user_to_out(user.dict())


@api_router.get("/users/role")
async def get_users_by_role(role: str = Query(...), current=Depends(get_current_user)):
    users = await db.users.find({"role": role, "deletedAt": None}).to_list(1000)
    return [user_to_out(u) for u in users]


@api_router.get("/users/{user_id}")
async def get_user(user_id: str, current=Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id, "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user_to_out(user)


@api_router.put("/users/{user_id}")
async def update_user(user_id: str, data: UserUpdate, current=Depends(get_current_user)):
    if current["sub"] != user_id and current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")
    await db.users.update_one({"id": user_id}, {"$set": updates})
    user = await db.users.find_one({"id": user_id})
    return user_to_out(user)


@api_router.put("/users/{user_id}/password")
async def change_password(user_id: str, data: PasswordChange, current=Depends(get_current_user)):
    if current["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    user = await db.users.find_one({"id": user_id})
    if not user or not verify_password(data.currentPassword, user.get('password_hash', '')):
        raise HTTPException(status_code=400, detail="Password saat ini tidak benar")
    await db.users.update_one({"id": user_id}, {"$set": {"password_hash": hash_password(data.newPassword)}})
    return {"message": "Password berhasil diubah"}


@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    await db.users.update_one({"id": user_id}, {"$set": {"deletedAt": datetime.utcnow().isoformat() + "Z"}})
    return {"message": "Akun berhasil dihapus"}


# ===== PROJECTS =====
@api_router.get("/projects")
async def get_projects(current=Depends(get_current_user)):
    projects = await db.projects.find({"deletedAt": None}).to_list(1000)
    for p in projects:
        p['progress'] = await compute_project_progress(p['id'])
        p.pop('_id', None)
    return projects


@api_router.post("/projects")
async def create_project(data: ProjectCreate, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    project = ProjectInDB(
        name=data.name,
        description=data.description or "",
        startDate=data.startDate,
        endDate=data.endDate,
        teamMembers=[current["sub"]],
        createdBy=current["sub"],
    )
    await db.projects.insert_one(project.dict())
    result = project.dict()
    result.pop('_id', None)
    return result


@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, current=Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id, "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    project['progress'] = await compute_project_progress(project_id)
    project.pop('_id', None)
    return project


@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, current=Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id, "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")
    await db.projects.update_one({"id": project_id}, {"$set": updates})
    updated = await db.projects.find_one({"id": project_id})
    updated['progress'] = await compute_project_progress(project_id)
    updated.pop('_id', None)
    return updated


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    await db.projects.update_one({"id": project_id}, {"$set": {"deletedAt": datetime.utcnow().isoformat() + "Z"}})
    return {"message": "Proyek berhasil dihapus"}


# ===== TASKS =====
@api_router.get("/tasks")
async def get_tasks(projectId: Optional[str] = None, current=Depends(get_current_user)):
    query = {}
    if projectId:
        query["projectId"] = projectId
    tasks = await db.tasks.find(query).to_list(1000)
    for t in tasks:
        t.pop('_id', None)
    return tasks


@api_router.post("/tasks")
async def create_task(data: TaskCreate, current=Depends(get_current_user)):
    task = TaskInDB(
        projectId=data.projectId,
        name=data.name,
        description=data.description or "",
        dueDate=data.dueDate,
        priority=data.priority,
        assignee=data.assignee,
    )
    await db.tasks.insert_one(task.dict())
    result = task.dict()
    result.pop('_id', None)

    # Notify assignee
    if data.assignee:
        assignee_user = await db.users.find_one({"id": data.assignee})
        if assignee_user:
            await create_notification(
                "task_assigned",
                f'Anda ditugaskan pada "{data.name}"',
                assignee_user.get('email', ''),
                task.id,
            )
    return result


@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, data: TaskUpdate, current=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    # Business rule: reject Selesai if subtasks incomplete
    if data.status == "Selesai":
        subtasks = await db.subtasks.find({"taskId": task_id}).to_list(1000)
        incomplete = [s for s in subtasks if not s.get('isDone', False)]
        if incomplete:
            raise HTTPException(status_code=400, detail=f"Tidak bisa menyelesaikan tugas: {len(incomplete)} subtask belum selesai")

    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")

    old_status = task.get('status')
    await db.tasks.update_one({"id": task_id}, {"$set": updates})
    updated = await db.tasks.find_one({"id": task_id})
    updated.pop('_id', None)

    # Notify on status change
    if data.status and data.status != old_status and task.get('assignee'):
        assignee_user = await db.users.find_one({"id": task['assignee']})
        if assignee_user:
            await create_notification(
                "status_changed",
                f'Status "{task["name"]}" diubah ke {data.status}',
                assignee_user.get('email', ''),
                task_id,
            )
    return updated


# ===== SUBTASKS =====
@api_router.get("/subtasks")
async def get_subtasks(taskId: Optional[str] = None, current=Depends(get_current_user)):
    query = {}
    if taskId:
        query["taskId"] = taskId
    subtasks = await db.subtasks.find(query).to_list(1000)
    for s in subtasks:
        s.pop('_id', None)
    return subtasks


@api_router.post("/subtasks")
async def create_subtask(data: SubtaskCreate, current=Depends(get_current_user)):
    subtask = SubtaskInDB(
        taskId=data.taskId,
        title=data.title,
        projectId=data.projectId,
    )
    await db.subtasks.insert_one(subtask.dict())
    result = subtask.dict()
    result.pop('_id', None)
    return result


@api_router.put("/subtasks/{subtask_id}")
async def update_subtask(subtask_id: str, data: SubtaskUpdate, current=Depends(get_current_user)):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")
    await db.subtasks.update_one({"id": subtask_id}, {"$set": updates})
    sub = await db.subtasks.find_one({"id": subtask_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Subtask tidak ditemukan")
    sub.pop('_id', None)
    return sub


@api_router.delete("/subtasks/{subtask_id}")
async def delete_subtask(subtask_id: str, current=Depends(get_current_user)):
    result = await db.subtasks.delete_one({"id": subtask_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subtask tidak ditemukan")
    return {"message": "Subtask berhasil dihapus"}


# ===== COMMENTS =====
@api_router.get("/comments")
async def get_comments(taskId: str = Query(...), current=Depends(get_current_user)):
    comments = await db.comments.find({"taskId": taskId}).to_list(1000)
    for c in comments:
        c.pop('_id', None)
    return comments


@api_router.post("/comments")
async def create_comment(data: CommentCreate, current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"]})
    comment = CommentInDB(
        taskId=data.taskId,
        actor=user['name'] if user else 'Unknown',
        message=data.message,
    )
    await db.comments.insert_one(comment.dict())
    result = comment.dict()
    result.pop('_id', None)

    # Notify task assignee about new comment
    task = await db.tasks.find_one({"id": data.taskId})
    if task and task.get('assignee') and task['assignee'] != current["sub"]:
        assignee_user = await db.users.find_one({"id": task['assignee']})
        if assignee_user:
            await create_notification(
                "comment",
                f'Komentar baru pada "{task["name"]}"',
                assignee_user.get('email', ''),
                data.taskId,
            )
    return result


# ===== NOTIFICATIONS =====
@api_router.get("/notifications")
async def get_notifications(current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"]})
    if not user:
        return []
    notifs = await db.notifications.find({"targetEmail": user.get('email', '')}).sort("timestamp", -1).to_list(50)
    for n in notifs:
        n.pop('_id', None)
    return notifs


@api_router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current=Depends(get_current_user)):
    await db.notifications.update_one({"id": notif_id}, {"$set": {"isRead": True}})
    return {"message": "OK"}


# ===== WHATSAPP STATUS =====
@api_router.get("/whatsapp/status")
async def whatsapp_status(current=Depends(get_current_user)):
    wa_enabled = os.environ.get("WHATSAPP_ENABLED", "false").lower() == "true"
    return {
        "enabled": wa_enabled,
        "provider": os.environ.get("WHATSAPP_PROVIDER", "webhook"),
        "connected": wa_enabled,
        "lastPing": datetime.utcnow().isoformat() + "Z" if wa_enabled else None,
        "gatewayUrl": os.environ.get("WHATSAPP_WEBHOOK_URL", ""),
    }


# ===== STATS =====
@api_router.get("/stats")
async def get_stats(current=Depends(get_current_user)):
    projects = await db.projects.find({"deletedAt": None}).to_list(1000)
    tasks = await db.tasks.find().to_list(5000)
    users = await db.users.find({"deletedAt": None}).to_list(1000)
    now = datetime.utcnow().isoformat()

    active = sum(1 for p in projects if p.get('status') == 'Aktif')
    completed = sum(1 for p in projects if p.get('status') == 'Selesai')
    pending = sum(1 for p in projects if p.get('status') == 'Tertunda')
    completed_tasks = sum(1 for t in tasks if t.get('status') == 'Selesai')
    in_progress = sum(1 for t in tasks if t.get('status') == 'Dikerjakan')
    pending_tasks = sum(1 for t in tasks if t.get('status') == 'Belum Mulai')
    overdue = sum(1 for t in tasks if t.get('dueDate', '') < now and t.get('status') != 'Selesai')

    return {
        "totalProjects": len(projects),
        "activeProjects": active,
        "completedProjects": completed,
        "pendingProjects": pending,
        "totalTasks": len(tasks),
        "completedTasks": completed_tasks,
        "inProgressTasks": in_progress,
        "pendingTasks": pending_tasks,
        "totalMembers": len(users),
        "overdueCount": overdue,
    }


# ===== ROOT =====
@api_router.get("/")
async def root():
    return {"message": "ProManage API v1.0"}


# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("id", unique=True)
    await db.users.create_index("email")
    await db.users.create_index("phone")
    await db.projects.create_index("id", unique=True)
    await db.tasks.create_index("id", unique=True)
    await db.tasks.create_index("projectId")
    await db.subtasks.create_index("id", unique=True)
    await db.subtasks.create_index("taskId")
    await db.comments.create_index("taskId")
    await db.notifications.create_index("targetEmail")
    logger.info("ProManage API started - indexes created")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
