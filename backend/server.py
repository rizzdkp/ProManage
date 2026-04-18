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
    user = UserInDB(
        name=data.name,
        phone=data.phone,
        email=data.email or "",
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
async def create_user(data: RegisterInput, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")
    existing = await db.users.find_one({"$or": [{"phone": data.phone}, {"email": data.email}]})
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")
    user = UserInDB(
        name=data.name,
        phone=data.phone,
        email=data.email or "",
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


# ===== SEED DATA =====
@api_router.post("/seed")
async def seed_data():
    """Seed initial data for testing"""
    users_count = await db.users.count_documents({})
    if users_count > 0:
        return {"message": "Data sudah ada"}

    # Create seed users
    seed_users = [
        {"name": "Budi Santoso", "phone": "628123456789", "email": "manager@promanage.id", "role": "Manager"},
        {"name": "Siti Nurhaliza", "phone": "628234567890", "email": "admin@promanage.id", "role": "Admin"},
        {"name": "Andi Pratama", "phone": "628345678901", "email": "lead@promanage.id", "role": "Team Lead"},
        {"name": "Dewi Lestari", "phone": "628456789012", "email": "member1@promanage.id", "role": "Anggota Tim"},
        {"name": "Rizki Ramadhan", "phone": "628567890123", "email": "member2@promanage.id", "role": "Anggota Tim"},
        {"name": "Fajar Nugroho", "phone": "628678901234", "email": "lead2@promanage.id", "role": "Team Lead"},
    ]
    user_ids = []
    for i, su in enumerate(seed_users):
        user = UserInDB(
            name=su["name"],
            phone=su["phone"],
            email=su["email"],
            role=su["role"],
            password_hash=hash_password("password123"),
            createdBy=None if i == 0 else user_ids[0],
        )
        user_ids.append(user.id)
        await db.users.insert_one(user.dict())

    # Create seed projects
    seed_projects = [
        {"name": "Website Redesign PT Maju", "desc": "Redesign website korporat untuk PT Maju Bersama dengan tampilan modern dan responsif.", "start": "2025-01-15", "end": "2025-06-30", "status": "Aktif", "members": [0, 2, 3, 4]},
        {"name": "Aplikasi Mobile E-Commerce", "desc": "Pengembangan aplikasi mobile e-commerce untuk toko retail modern.", "start": "2025-02-01", "end": "2025-08-31", "status": "Aktif", "members": [0, 1, 5, 4]},
        {"name": "Sistem Inventory Gudang", "desc": "Pembangunan sistem manajemen inventory untuk gudang distribusi.", "start": "2025-03-01", "end": "2025-07-15", "status": "Aktif", "members": [1, 2, 3]},
        {"name": "Portal HR Internal", "desc": "Platform HR internal untuk manajemen karyawan dan cuti.", "start": "2024-10-01", "end": "2025-03-31", "status": "Selesai", "members": [0, 2, 4]},
        {"name": "Dashboard Analitik Penjualan", "desc": "Dashboard analitik real-time untuk monitoring penjualan harian.", "start": "2025-05-01", "end": "2025-09-30", "status": "Tertunda", "members": [5, 3]},
    ]
    project_ids = []
    for sp in seed_projects:
        proj = ProjectInDB(
            name=sp["name"],
            description=sp["desc"],
            startDate=sp["start"],
            endDate=sp["end"],
            status=sp["status"],
            teamMembers=[user_ids[i] for i in sp["members"]],
            createdBy=user_ids[0],
        )
        project_ids.append(proj.id)
        await db.projects.insert_one(proj.dict())

    # Create seed tasks
    seed_tasks = [
        {"proj": 0, "name": "Riset UI/UX Kompetitor", "desc": "Melakukan analisis mendalam terhadap 5 website kompetitor utama.", "due": "2025-02-15", "pri": "Tinggi", "status": "Selesai", "assignee": 3},
        {"proj": 0, "name": "Desain Wireframe Halaman Utama", "desc": "Membuat wireframe untuk halaman utama website baru.", "due": "2025-03-01", "pri": "Tinggi", "status": "Selesai", "assignee": 2},
        {"proj": 0, "name": "Implementasi Frontend", "desc": "Mengembangkan frontend berdasarkan desain yang sudah disetujui.", "due": "2025-05-15", "pri": "Tinggi", "status": "Dikerjakan", "assignee": 4},
        {"proj": 0, "name": "Integrasi API Backend", "desc": "Menghubungkan frontend dengan API backend.", "due": "2025-06-01", "pri": "Sedang", "status": "Belum Mulai", "assignee": 3},
        {"proj": 0, "name": "Testing & QA", "desc": "Pengujian menyeluruh terhadap fitur dan performa website.", "due": "2025-06-20", "pri": "Sedang", "status": "Belum Mulai", "assignee": 2},
        {"proj": 1, "name": "Setup Environment React Native", "desc": "Konfigurasi environment development React Native.", "due": "2025-02-15", "pri": "Tinggi", "status": "Selesai", "assignee": 5},
        {"proj": 1, "name": "Desain UI Katalog Produk", "desc": "Membuat desain halaman katalog produk.", "due": "2025-03-15", "pri": "Tinggi", "status": "Dikerjakan", "assignee": 4},
        {"proj": 1, "name": "Implementasi Keranjang Belanja", "desc": "Fitur keranjang belanja dan checkout.", "due": "2025-05-01", "pri": "Tinggi", "status": "Belum Mulai", "assignee": 5},
        {"proj": 2, "name": "Desain Database Schema", "desc": "Merancang schema database untuk sistem inventory.", "due": "2025-03-20", "pri": "Tinggi", "status": "Selesai", "assignee": 2},
        {"proj": 2, "name": "CRUD Produk Inventory", "desc": "Implementasi fitur CRUD untuk data produk.", "due": "2025-04-30", "pri": "Sedang", "status": "Dikerjakan", "assignee": 3},
    ]
    task_ids = []
    for st in seed_tasks:
        task = TaskInDB(
            projectId=project_ids[st["proj"]],
            name=st["name"],
            description=st["desc"],
            dueDate=st["due"],
            priority=st["pri"],
            status=st["status"],
            assignee=user_ids[st["assignee"]],
        )
        task_ids.append(task.id)
        await db.tasks.insert_one(task.dict())

    # Create seed subtasks
    seed_subtasks = [
        {"task": 0, "title": "Identifikasi 5 kompetitor utama", "done": True, "proj": 0},
        {"task": 0, "title": "Screenshot dan analisis UI masing-masing", "done": True, "proj": 0},
        {"task": 0, "title": "Buat laporan perbandingan", "done": True, "proj": 0},
        {"task": 1, "title": "Wireframe halaman beranda", "done": True, "proj": 0},
        {"task": 1, "title": "Wireframe halaman tentang kami", "done": True, "proj": 0},
        {"task": 1, "title": "Wireframe halaman kontak", "done": True, "proj": 0},
        {"task": 2, "title": "Setup project React", "done": True, "proj": 0},
        {"task": 2, "title": "Implementasi komponen header", "done": True, "proj": 0},
        {"task": 2, "title": "Implementasi halaman beranda", "done": False, "proj": 0},
        {"task": 2, "title": "Implementasi responsive design", "done": False, "proj": 0},
        {"task": 6, "title": "Mockup grid produk", "done": True, "proj": 1},
        {"task": 6, "title": "Mockup detail produk", "done": False, "proj": 1},
        {"task": 9, "title": "API endpoint produk", "done": True, "proj": 2},
        {"task": 9, "title": "Form input produk", "done": False, "proj": 2},
    ]
    for ss in seed_subtasks:
        sub = SubtaskInDB(
            taskId=task_ids[ss["task"]],
            title=ss["title"],
            isDone=ss["done"],
            projectId=project_ids[ss["proj"]],
        )
        await db.subtasks.insert_one(sub.dict())

    # Create seed comments
    seed_comments = [
        {"task": 0, "actor": "Budi Santoso", "msg": "Pastikan analisis mencakup aspek mobile juga.", "ts": "2025-02-01T10:30:00Z"},
        {"task": 0, "actor": "Dewi Lestari", "msg": "Sudah saya tambahkan analisis mobile di laporan.", "ts": "2025-02-02T14:15:00Z"},
        {"task": 2, "actor": "Andi Pratama", "msg": "Gunakan Tailwind CSS untuk styling.", "ts": "2025-04-10T09:00:00Z"},
        {"task": 2, "actor": "Rizki Ramadhan", "msg": "Noted, sudah saya setup.", "ts": "2025-04-10T11:30:00Z"},
        {"task": 6, "actor": "Fajar Nugroho", "msg": "Referensi desain ada di Figma link yang saya share.", "ts": "2025-03-10T08:00:00Z"},
        {"task": 8, "actor": "Siti Nurhaliza", "msg": "Schema sudah di-review dan approved.", "ts": "2025-03-18T16:00:00Z"},
    ]
    for sc in seed_comments:
        cmt = CommentInDB(
            taskId=task_ids[sc["task"]],
            actor=sc["actor"],
            message=sc["msg"],
            timestamp=sc["ts"],
        )
        await db.comments.insert_one(cmt.dict())

    return {"message": "Data seed berhasil dibuat", "users": len(seed_users), "projects": len(seed_projects), "tasks": len(seed_tasks)}


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
