from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import base64
import os
import logging
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from models import (
    RegisterInput, CreateUserInput, LoginInput, AuthResponse, UserInDB, UserOut, UserUpdate, PasswordChange,
    ProjectCreate, ProjectUpdate, ProjectInDB,
    TaskCreate, TaskUpdate, TaskInDB,
    SubtaskCreate, SubtaskUpdate, SubtaskInDB,
    CommentCreate, CommentInDB,
    NotificationInDB,
    WhatsAppTestInput,
)
from auth import hash_password, verify_password, create_token, get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'promanage')]

APP_ENV = os.environ.get("APP_ENV", "development").lower()
ALLOW_PUBLIC_REGISTER = os.environ.get("ALLOW_PUBLIC_REGISTER", "false").lower() == "true"
SINGLE_ADMIN_ONLY = os.environ.get("SINGLE_ADMIN_ONLY", "true").lower() == "true"
BOOTSTRAP_ADMIN_NAME = os.environ.get("BOOTSTRAP_ADMIN_NAME", "Administrator")
BOOTSTRAP_ADMIN_EMAIL = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "")
BOOTSTRAP_ADMIN_PHONE = os.environ.get("BOOTSTRAP_ADMIN_PHONE", "")
BOOTSTRAP_ADMIN_PASSWORD = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")

cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.environ.get("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

ALLOWED_ROLES = {"Manager", "Admin", "Team Lead", "Anggota Tim"}
ALLOWED_TASK_STATUSES = {"Belum Mulai", "Dikerjakan", "Selesai"}
ALLOWED_TASK_PRIORITIES = {"Rendah", "Sedang", "Tinggi"}
ALLOWED_PROJECT_STATUSES = {"Aktif", "Selesai", "Tertunda"}

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ===== HELPERS =====
def user_to_out(u: dict) -> dict:
    return {k: v for k, v in u.items() if k not in ('password_hash', '_id')}


def normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def normalize_phone(value: str) -> str:
    return (value or "").strip()


def normalize_whatsapp_phone(value: Optional[str]) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("0"):
        return f"62{digits[1:]}"
    if digits.startswith("8"):
        return f"62{digits}"
    return digits


def parse_float_env(name: str, default: float) -> float:
    raw = (os.environ.get(name, "") or "").strip()
    if not raw:
        return default
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def is_admin_or_manager(current: dict) -> bool:
    return current.get("role") in ("Manager", "Admin")


def get_whatsapp_config() -> Dict[str, Any]:
    enabled = os.environ.get("WHATSAPP_ENABLED", "false").lower() == "true"
    provider = (os.environ.get("WHATSAPP_PROVIDER", "webhook") or "webhook").strip().lower()
    webhook_url = (os.environ.get("WHATSAPP_WEBHOOK_URL", "") or "").strip()
    webhook_token = (os.environ.get("WHATSAPP_WEBHOOK_TOKEN", "") or "").strip()
    auth_header = (os.environ.get("WHATSAPP_WEBHOOK_AUTH_HEADER", "Authorization") or "Authorization").strip()
    waha_base_url = (os.environ.get("WHATSAPP_WAHA_BASE_URL", "http://127.0.0.1:3000") or "").strip()
    waha_api_key = (os.environ.get("WHATSAPP_WAHA_API_KEY", "") or "").strip()
    waha_session = (os.environ.get("WHATSAPP_WAHA_SESSION", "default") or "default").strip() or "default"
    timeout_seconds = parse_float_env("WHATSAPP_TIMEOUT_SECONDS", 10.0)

    configured = False
    if provider == "webhook":
        configured = bool(webhook_url)
    elif provider == "waha":
        configured = bool(waha_base_url)

    return {
        "enabled": enabled,
        "provider": provider,
        "webhook_url": webhook_url,
        "webhook_token": webhook_token,
        "auth_header": auth_header,
        "waha_base_url": waha_base_url,
        "waha_api_key": waha_api_key,
        "waha_session": waha_session,
        "timeout_seconds": timeout_seconds,
        "configured": configured,
    }


def build_waha_url(wa_cfg: Dict[str, Any], path: str) -> str:
    base = wa_cfg["waha_base_url"].rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def build_waha_headers(wa_cfg: Dict[str, Any]) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if wa_cfg.get("waha_api_key"):
        headers["X-Api-Key"] = wa_cfg["waha_api_key"]
    return headers


async def waha_request(
    wa_cfg: Dict[str, Any],
    method: str,
    path: str,
    json_payload: Optional[dict] = None,
    params: Optional[dict] = None,
) -> httpx.Response:
    url = build_waha_url(wa_cfg, path)
    async with httpx.AsyncClient(timeout=wa_cfg["timeout_seconds"]) as client:
        return await client.request(
            method=method,
            url=url,
            headers=build_waha_headers(wa_cfg),
            json=json_payload,
            params=params,
        )


def map_waha_status(info: Optional[dict]) -> Dict[str, Any]:
    session_state = (info or {}).get("status")
    normalized_state = (session_state or "").upper()
    connected = normalized_state == "WORKING"
    needs_qr_scan = normalized_state == "SCAN_QR_CODE"
    return {
        "sessionState": normalized_state or None,
        "connected": connected,
        "needsQrScan": needs_qr_scan,
    }


async def get_waha_session_info(wa_cfg: Dict[str, Any]) -> Optional[dict]:
    response = await waha_request(wa_cfg, "GET", f"/api/sessions/{wa_cfg['waha_session']}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def ensure_waha_session(wa_cfg: Dict[str, Any]) -> Optional[dict]:
    info = await get_waha_session_info(wa_cfg)
    if info:
        state = (info.get("status") or "").upper()
        if state == "STOPPED":
            start_response = await waha_request(wa_cfg, "POST", f"/api/sessions/{wa_cfg['waha_session']}/start")
            if start_response.status_code not in (200, 201, 204):
                start_response.raise_for_status()
            info = await get_waha_session_info(wa_cfg)
        return info

    create_payload = {"name": wa_cfg["waha_session"], "start": True}
    create_response = await waha_request(wa_cfg, "POST", "/api/sessions", json_payload=create_payload)
    if create_response.status_code not in (200, 201, 409):
        create_response.raise_for_status()

    if create_response.status_code == 409:
        start_response = await waha_request(wa_cfg, "POST", f"/api/sessions/{wa_cfg['waha_session']}/start")
        if start_response.status_code not in (200, 201, 204):
            start_response.raise_for_status()

    return await get_waha_session_info(wa_cfg)


async def get_waha_qr_data(wa_cfg: Dict[str, Any]) -> Dict[str, Any]:
    response = await waha_request(
        wa_cfg,
        "GET",
        f"/api/{wa_cfg['waha_session']}/auth/qr",
        params={"format": "image"},
    )
    response.raise_for_status()

    content_type = (response.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("mimetype") and payload.get("data"):
            return {
                "mimetype": payload["mimetype"],
                "data": payload["data"],
                "imageDataUrl": f"data:{payload['mimetype']};base64,{payload['data']}",
                "raw": None,
            }
        if isinstance(payload, dict) and payload.get("value"):
            return {
                "mimetype": None,
                "data": None,
                "imageDataUrl": None,
                "raw": payload["value"],
            }
        raise RuntimeError("Format respons QR WAHA tidak dikenali")

    mimetype = content_type.split(";")[0] or "image/png"
    encoded = base64.b64encode(response.content).decode("ascii")
    return {
        "mimetype": mimetype,
        "data": encoded,
        "imageDataUrl": f"data:{mimetype};base64,{encoded}",
        "raw": None,
    }


async def get_whatsapp_runtime_status() -> Dict[str, Any]:
    wa_cfg = get_whatsapp_config()
    base_response = {
        "enabled": wa_cfg["enabled"],
        "provider": wa_cfg["provider"],
        "configured": wa_cfg["configured"],
        "connected": False,
        "lastPing": None,
        "gatewayUrl": "",
        "session": None,
        "sessionState": None,
        "needsQrScan": False,
    }

    if wa_cfg["provider"] == "webhook":
        is_connected = wa_cfg["enabled"] and wa_cfg["configured"]
        base_response.update({
            "connected": is_connected,
            "lastPing": datetime.utcnow().isoformat() + "Z" if is_connected else None,
            "gatewayUrl": wa_cfg["webhook_url"],
        })
        return base_response

    if wa_cfg["provider"] == "waha":
        base_response.update({
            "gatewayUrl": wa_cfg["waha_base_url"],
            "session": wa_cfg["waha_session"],
        })

        if not wa_cfg["enabled"] or not wa_cfg["configured"]:
            return base_response

        try:
            info = await get_waha_session_info(wa_cfg)
            status_data = map_waha_status(info)
            base_response.update(status_data)
            base_response["lastPing"] = datetime.utcnow().isoformat() + "Z"
        except Exception as exc:
            logger.warning("WAHA status check gagal: %s", exc)
        return base_response

    return base_response


async def send_whatsapp_message(
    target_user: dict,
    message: str,
    notif_type: str,
    task_id: Optional[str] = None,
) -> bool:
    wa_cfg = get_whatsapp_config()
    if not wa_cfg["enabled"]:
        return False

    target_phone = normalize_whatsapp_phone(target_user.get("phone"))
    if not target_phone:
        logger.warning("WA skip: phone kosong untuk user %s", target_user.get("id", "unknown"))
        return False

    if wa_cfg["provider"] == "webhook":
        if not wa_cfg["configured"]:
            logger.warning("WA skip: WHATSAPP_WEBHOOK_URL belum di-set")
            return False

        headers = {"Content-Type": "application/json"}
        token = wa_cfg["webhook_token"]
        if token:
            auth_header = wa_cfg["auth_header"]
            if auth_header.lower() == "authorization" and not token.lower().startswith("bearer "):
                headers[auth_header] = f"Bearer {token}"
            else:
                headers[auth_header] = token

        payload = {
            "to": target_phone,
            "message": message,
            "type": notif_type,
            "taskId": task_id,
            "userId": target_user.get("id"),
            "userName": target_user.get("name"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        try:
            async with httpx.AsyncClient(timeout=wa_cfg["timeout_seconds"]) as client:
                response = await client.post(wa_cfg["webhook_url"], json=payload, headers=headers)
                response.raise_for_status()
        except Exception as exc:
            logger.warning("WA send gagal untuk %s: %s", target_phone, exc)
            return False

        logger.info("WA notification terkirim ke %s (%s)", target_phone, notif_type)
        return True

    if wa_cfg["provider"] == "waha":
        if not wa_cfg["configured"]:
            logger.warning("WAHA skip: WHATSAPP_WAHA_BASE_URL belum di-set")
            return False

        try:
            info = await ensure_waha_session(wa_cfg)
            state = (info or {}).get("status", "")
            if state != "WORKING":
                logger.warning("WAHA belum terhubung. Status session: %s", state or "unknown")
                return False

            chat_id = f"{target_phone}@c.us"
            payload = {
                "chatId": chat_id,
                "text": message,
                "session": wa_cfg["waha_session"],
            }
            response = await waha_request(wa_cfg, "POST", "/api/sendText", json_payload=payload)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("WAHA send gagal untuk %s: %s", target_phone, exc)
            return False

        logger.info("WA notification terkirim via WAHA ke %s (%s)", target_phone, notif_type)
        return True

    logger.warning("WA skip: provider %s belum didukung", wa_cfg["provider"])
    return False


async def ensure_bootstrap_admin() -> None:
    users_total_count = await db.users.count_documents({})
    if users_total_count > 0:
        return

    bootstrap_name = (BOOTSTRAP_ADMIN_NAME or "Administrator").strip() or "Administrator"
    bootstrap_email = normalize_email(BOOTSTRAP_ADMIN_EMAIL) or None
    bootstrap_phone = normalize_phone(BOOTSTRAP_ADMIN_PHONE)
    bootstrap_password = (BOOTSTRAP_ADMIN_PASSWORD or "").strip()

    if not bootstrap_phone or not bootstrap_password:
        logger.warning("Collection users kosong, tetapi BOOTSTRAP_ADMIN_PHONE/BOOTSTRAP_ADMIN_PASSWORD belum di-set.")
        return

    admin = UserInDB(
        name=bootstrap_name,
        role="Admin",
        phone=bootstrap_phone,
        email=bootstrap_email,
        password_hash=hash_password(bootstrap_password),
    )
    await db.users.insert_one(admin.dict())
    logger.info("Bootstrap admin dibuat untuk %s", bootstrap_email or bootstrap_phone)


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.strip()
        if len(normalized) == 10:
            normalized = f"{normalized}T00:00:00Z"
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        return datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None


def can_manage_project(current: dict, project: dict) -> bool:
    if current.get("role") in ("Manager", "Admin"):
        return True
    if project.get("createdBy") == current.get("sub"):
        return True
    return current.get("sub") in (project.get("teamMembers") or [])


async def compute_project_progress(project_id: str) -> int:
    tasks = await db.tasks.find({"projectId": project_id}).to_list(1000)
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.get('status') == 'Selesai')
    return round((done / len(tasks)) * 100)


async def create_notification(ntype: str, message: str, target_user: dict, task_id: str = None):
    target_email = normalize_email(target_user.get("email"))
    notif = NotificationInDB(
        type=ntype,
        taskId=task_id,
        message=message,
        targetUserId=target_user["id"],
        targetEmail=target_email or None,
    )
    await db.notifications.insert_one(notif.dict())
    asyncio.create_task(
        send_whatsapp_message(
            target_user=target_user,
            message=f"[ProManage] {message}",
            notif_type=ntype,
            task_id=task_id,
        )
    )


# ===== AUTH =====
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    active_users_count = await db.users.count_documents({"deletedAt": None})
    if active_users_count > 0 and not ALLOW_PUBLIC_REGISTER:
        raise HTTPException(status_code=403, detail="Registrasi publik dinonaktifkan. Hubungi admin.")

    phone = normalize_phone(data.phone)
    email = normalize_email(data.email) or None
    unique_filters = [{"phone": phone}]
    if email:
        unique_filters.append({"email": email})

    existing = await db.users.find_one({"$or": unique_filters, "deletedAt": None})
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")

    role = "Anggota Tim"
    if active_users_count == 0:
        role = "Admin"

    if role == "Admin" and SINGLE_ADMIN_ONLY:
        admin_count = await db.users.count_documents({"role": "Admin", "deletedAt": None})
        if admin_count > 0:
            raise HTTPException(status_code=400, detail="Akun Admin utama sudah ada. Hanya 1 akun Admin diperbolehkan.")

    user = UserInDB(
        name=data.name,
        role=role,
        phone=phone,
        email=email,
        password_hash=hash_password(data.password),
    )
    await db.users.insert_one(user.dict())
    token = create_token(user.id, user.email or "", user.role)
    return {"user": user_to_out(user.dict()), "token": token}


@api_router.post("/auth/login")
async def login(data: LoginInput):
    identifier = (data.identifier or "").strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Identifier wajib diisi")

    user = await db.users.find_one({
        "$or": [
            {"email": normalize_email(identifier)},
            {"email": identifier},
            {"phone": identifier},
        ],
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

    role = (data.role or "Anggota Tim").strip()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    if role == "Admin" and SINGLE_ADMIN_ONLY:
        admin_count = await db.users.count_documents({"role": "Admin", "deletedAt": None})
        if admin_count > 0:
            raise HTTPException(status_code=400, detail="Akun Admin utama sudah ada. Hanya 1 akun Admin diperbolehkan.")

    phone = normalize_phone(data.phone)
    email = normalize_email(data.email) or None
    unique_filters = [{"phone": phone}]
    if email:
        unique_filters.append({"email": email})

    existing = await db.users.find_one({"$or": unique_filters, "deletedAt": None})
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")

    if role == "Admin" and SINGLE_ADMIN_ONLY:
        admin_count = await db.users.count_documents({"role": "Admin", "deletedAt": None})
        if admin_count > 0:
            raise HTTPException(status_code=400, detail="Akun Admin utama sudah ada. Hanya 1 akun Admin diperbolehkan.")

    user = UserInDB(
        name=data.name,
        role=role,
        phone=phone,
        email=email,
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
    user = await db.users.find_one({"id": user_id, "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if current["sub"] != user_id and current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")

    if "email" in updates:
        updates["email"] = normalize_email(updates["email"]) or None
    if "phone" in updates:
        updates["phone"] = normalize_phone(updates["phone"])

    unique_filters = []
    if updates.get("phone"):
        unique_filters.append({"phone": updates["phone"]})
    if updates.get("email"):
        unique_filters.append({"email": updates["email"]})
    if unique_filters:
        existing = await db.users.find_one({
            "id": {"$ne": user_id},
            "deletedAt": None,
            "$or": unique_filters,
        })
        if existing:
            raise HTTPException(status_code=400, detail="Nomor WA atau email sudah terdaftar")

    await db.users.update_one({"id": user_id, "deletedAt": None}, {"$set": updates})
    updated_user = await db.users.find_one({"id": user_id, "deletedAt": None})
    return user_to_out(updated_user)


@api_router.put("/users/{user_id}/password")
async def change_password(user_id: str, data: PasswordChange, current=Depends(get_current_user)):
    if current["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    user = await db.users.find_one({"id": user_id, "deletedAt": None})
    if not user or not verify_password(data.currentPassword, user.get('password_hash', '')):
        raise HTTPException(status_code=400, detail="Password saat ini tidak benar")

    await db.users.update_one({"id": user_id, "deletedAt": None}, {"$set": {"password_hash": hash_password(data.newPassword)}})
    return {"message": "Password berhasil diubah"}


@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    user = await db.users.find_one({"id": user_id, "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if SINGLE_ADMIN_ONLY and user.get("role") == "Admin":
        admin_count = await db.users.count_documents({"role": "Admin", "deletedAt": None})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Akun Admin terakhir tidak boleh dihapus")

    result = await db.users.update_one(
        {"id": user_id, "deletedAt": None},
        {"$set": {"deletedAt": datetime.utcnow().isoformat() + "Z"}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    return {"message": "Akun berhasil dihapus"}


# ===== PROJECTS =====
@api_router.get("/projects")
async def get_projects(current=Depends(get_current_user)):
    project_query = {"deletedAt": None}
    if current.get("role") not in ("Manager", "Admin"):
        project_query["$or"] = [
            {"createdBy": current["sub"]},
            {"teamMembers": current["sub"]},
        ]

    projects = await db.projects.find(project_query).to_list(1000)
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

    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    project['progress'] = await compute_project_progress(project_id)
    project.pop('_id', None)
    return project


@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, current=Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id, "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Tidak ada field yang diubah")

    if "status" in updates and updates["status"] not in ALLOWED_PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail="Status proyek tidak valid")

    if "teamMembers" in updates:
        member_ids = list(dict.fromkeys(updates["teamMembers"] or []))
        users = await db.users.find({"id": {"$in": member_ids}, "deletedAt": None}).to_list(max(len(member_ids), 1))
        if len(users) != len(member_ids):
            raise HTTPException(status_code=400, detail="Terdapat anggota tim yang tidak valid")
        updates["teamMembers"] = member_ids

    await db.projects.update_one({"id": project_id, "deletedAt": None}, {"$set": updates})
    updated = await db.projects.find_one({"id": project_id})
    updated['progress'] = await compute_project_progress(project_id)
    updated.pop('_id', None)
    return updated


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current=Depends(get_current_user)):
    if current["role"] not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    result = await db.projects.update_one(
        {"id": project_id, "deletedAt": None},
        {"$set": {"deletedAt": datetime.utcnow().isoformat() + "Z"}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    return {"message": "Proyek berhasil dihapus"}


# ===== TASKS =====
@api_router.get("/tasks")
async def get_tasks(projectId: Optional[str] = None, current=Depends(get_current_user)):
    query = {}
    if projectId:
        project = await db.projects.find_one({"id": projectId, "deletedAt": None})
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
        if not can_manage_project(current, project):
            raise HTTPException(status_code=403, detail="Tidak memiliki akses ke proyek ini")
        query["projectId"] = projectId
    elif current.get("role") not in ("Manager", "Admin"):
        projects = await db.projects.find({
            "deletedAt": None,
            "$or": [
                {"createdBy": current["sub"]},
                {"teamMembers": current["sub"]},
            ],
        }).to_list(1000)
        project_ids = [p["id"] for p in projects]
        query["projectId"] = {"$in": project_ids}

    tasks = await db.tasks.find(query).to_list(1000)
    for t in tasks:
        t.pop('_id', None)
    return tasks


@api_router.post("/tasks")
async def create_task(data: TaskCreate, current=Depends(get_current_user)):
    project = await db.projects.find_one({"id": data.projectId, "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke proyek ini")

    if data.priority not in ALLOWED_TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Prioritas tugas tidak valid")

    assignee_user = None
    if data.assignee:
        assignee_user = await db.users.find_one({"id": data.assignee, "deletedAt": None})
        if not assignee_user:
            raise HTTPException(status_code=400, detail="Assignee tidak ditemukan")
        if data.assignee not in (project.get("teamMembers") or []):
            raise HTTPException(status_code=400, detail="Assignee harus merupakan anggota proyek")

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
    if assignee_user:
        await create_notification(
            "task_assigned",
            f'Anda ditugaskan pada "{data.name}"',
            assignee_user,
            task.id,
        )

    return result


@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, data: TaskUpdate, current=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    project = await db.projects.find_one({"id": task.get("projectId"), "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tugas tidak ditemukan")

    if not can_manage_project(current, project) and task.get("assignee") != current.get("sub"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    if data.status and data.status not in ALLOWED_TASK_STATUSES:
        raise HTTPException(status_code=400, detail="Status tugas tidak valid")

    if data.priority and data.priority not in ALLOWED_TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Prioritas tugas tidak valid")

    assignee_user = None
    if data.assignee is not None:
        assignee = data.assignee.strip() if isinstance(data.assignee, str) else data.assignee
        if assignee:
            assignee_user = await db.users.find_one({"id": assignee, "deletedAt": None})
            if not assignee_user:
                raise HTTPException(status_code=400, detail="Assignee tidak ditemukan")
            if project and assignee not in (project.get("teamMembers") or []):
                raise HTTPException(status_code=400, detail="Assignee harus merupakan anggota proyek")
        data.assignee = assignee or None

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

    notify_target_user = assignee_user
    if not notify_target_user and updated.get('assignee'):
        notify_target_user = await db.users.find_one({"id": updated['assignee'], "deletedAt": None})

    # Notify on status change
    if data.status and data.status != old_status and notify_target_user:
        await create_notification(
            "status_changed",
            f'Status "{task["name"]}" diubah ke {data.status}',
            notify_target_user,
            task_id,
        )

    return updated


# ===== SUBTASKS =====
@api_router.get("/subtasks")
async def get_subtasks(taskId: Optional[str] = None, current=Depends(get_current_user)):
    query = {}
    if taskId:
        task = await db.tasks.find_one({"id": taskId})
        if not task:
            raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

        project = await db.projects.find_one({"id": task.get("projectId"), "deletedAt": None})
        if not project:
            raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
        if not can_manage_project(current, project):
            raise HTTPException(status_code=403, detail="Tidak memiliki izin")

        query["taskId"] = taskId
    elif current.get("role") not in ("Manager", "Admin"):
        projects = await db.projects.find({
            "deletedAt": None,
            "$or": [
                {"createdBy": current["sub"]},
                {"teamMembers": current["sub"]},
            ],
        }).to_list(1000)
        project_ids = [p["id"] for p in projects]
        query["projectId"] = {"$in": project_ids}

    subtasks = await db.subtasks.find(query).to_list(1000)
    for s in subtasks:
        s.pop('_id', None)
    return subtasks


@api_router.post("/subtasks")
async def create_subtask(data: SubtaskCreate, current=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": data.taskId})
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    if task.get("projectId") != data.projectId:
        raise HTTPException(status_code=400, detail="taskId dan projectId tidak cocok")

    project = await db.projects.find_one({"id": data.projectId, "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

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
    subtask = await db.subtasks.find_one({"id": subtask_id})
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask tidak ditemukan")

    project = await db.projects.find_one({"id": subtask.get("projectId"), "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

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
    subtask = await db.subtasks.find_one({"id": subtask_id})
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask tidak ditemukan")

    project = await db.projects.find_one({"id": subtask.get("projectId"), "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    result = await db.subtasks.delete_one({"id": subtask_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subtask tidak ditemukan")
    return {"message": "Subtask berhasil dihapus"}


# ===== COMMENTS =====
@api_router.get("/comments")
async def get_comments(taskId: str = Query(...), current=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": taskId})
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    project = await db.projects.find_one({"id": task.get("projectId"), "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    comments = await db.comments.find({"taskId": taskId}).to_list(1000)
    for c in comments:
        c.pop('_id', None)
    return comments


@api_router.post("/comments")
async def create_comment(data: CommentCreate, current=Depends(get_current_user)):
    task = await db.tasks.find_one({"id": data.taskId})
    if not task:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")

    project = await db.projects.find_one({"id": task.get("projectId"), "deletedAt": None})
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    if not can_manage_project(current, project):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin")

    user = await db.users.find_one({"id": current["sub"], "deletedAt": None})
    comment = CommentInDB(
        taskId=data.taskId,
        actor=user['name'] if user else 'Unknown',
        message=data.message,
    )
    await db.comments.insert_one(comment.dict())
    result = comment.dict()
    result.pop('_id', None)

    # Notify task assignee about new comment
    if task and task.get('assignee') and task['assignee'] != current["sub"]:
        assignee_user = await db.users.find_one({"id": task['assignee'], "deletedAt": None})
        if assignee_user:
            await create_notification(
                "comment",
                f'Komentar baru pada "{task["name"]}"',
                assignee_user,
                data.taskId,
            )
    return result


# ===== NOTIFICATIONS =====
@api_router.get("/notifications")
async def get_notifications(current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"], "deletedAt": None})
    if not user:
        return []

    ownership_filters = [{"targetUserId": current["sub"]}]
    normalized_email = normalize_email(user.get("email"))
    if normalized_email:
        ownership_filters.append({"targetEmail": normalized_email})

    notifs = await db.notifications.find({"$or": ownership_filters}).sort("timestamp", -1).to_list(50)
    for n in notifs:
        n.pop('_id', None)
    return notifs


@api_router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"], "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    ownership_filters = [{"targetUserId": current["sub"]}]
    normalized_email = normalize_email(user.get("email"))
    if normalized_email:
        ownership_filters.append({"targetEmail": normalized_email})

    result = await db.notifications.update_one(
        {"id": notif_id, "$or": ownership_filters},
        {"$set": {"isRead": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan")

    return {"message": "OK"}


# ===== WHATSAPP STATUS =====
@api_router.get("/whatsapp/status")
async def whatsapp_status(current=Depends(get_current_user)):
    return await get_whatsapp_runtime_status()


@api_router.post("/whatsapp/connect")
async def whatsapp_connect(current=Depends(get_current_user)):
    if not is_admin_or_manager(current):
        raise HTTPException(status_code=403, detail="Hanya Admin/Manager yang dapat menghubungkan WhatsApp")

    wa_cfg = get_whatsapp_config()
    if not wa_cfg["enabled"]:
        raise HTTPException(status_code=400, detail="WhatsApp belum diaktifkan (WHATSAPP_ENABLED=false)")
    if wa_cfg["provider"] != "waha":
        raise HTTPException(status_code=400, detail="Mode scan QR hanya tersedia untuk WHATSAPP_PROVIDER=waha")
    if not wa_cfg["configured"]:
        raise HTTPException(status_code=400, detail="WHATSAPP_WAHA_BASE_URL belum di-set")

    try:
        session_info = await ensure_waha_session(wa_cfg)
    except Exception as exc:
        logger.warning("WAHA connect gagal: %s", exc)
        raise HTTPException(status_code=502, detail="Gagal menghubungkan ke WAHA")

    status_data = map_waha_status(session_info)
    return {
        "message": "Session WhatsApp siap",
        "session": wa_cfg["waha_session"],
        **status_data,
    }


@api_router.get("/whatsapp/qr")
async def whatsapp_qr(current=Depends(get_current_user)):
    if not is_admin_or_manager(current):
        raise HTTPException(status_code=403, detail="Hanya Admin/Manager yang dapat melihat QR WhatsApp")

    wa_cfg = get_whatsapp_config()
    if not wa_cfg["enabled"]:
        raise HTTPException(status_code=400, detail="WhatsApp belum diaktifkan (WHATSAPP_ENABLED=false)")
    if wa_cfg["provider"] != "waha":
        raise HTTPException(status_code=400, detail="Endpoint QR hanya tersedia untuk WHATSAPP_PROVIDER=waha")
    if not wa_cfg["configured"]:
        raise HTTPException(status_code=400, detail="WHATSAPP_WAHA_BASE_URL belum di-set")

    try:
        session_info = await ensure_waha_session(wa_cfg)
        status_data = map_waha_status(session_info)
        if status_data["connected"]:
            return {
                "session": wa_cfg["waha_session"],
                **status_data,
                "qr": None,
            }

        qr_data = await get_waha_qr_data(wa_cfg)
    except Exception as exc:
        logger.warning("WAHA QR gagal: %s", exc)
        raise HTTPException(status_code=502, detail="Gagal mengambil QR WhatsApp dari WAHA")

    return {
        "session": wa_cfg["waha_session"],
        **status_data,
        "qr": qr_data,
    }


@api_router.post("/whatsapp/logout")
async def whatsapp_logout(current=Depends(get_current_user)):
    if not is_admin_or_manager(current):
        raise HTTPException(status_code=403, detail="Hanya Admin/Manager yang dapat memutuskan WhatsApp")

    wa_cfg = get_whatsapp_config()
    if wa_cfg["provider"] != "waha":
        raise HTTPException(status_code=400, detail="Logout WA hanya tersedia untuk WHATSAPP_PROVIDER=waha")
    if not wa_cfg["configured"]:
        raise HTTPException(status_code=400, detail="WHATSAPP_WAHA_BASE_URL belum di-set")

    try:
        response = await waha_request(wa_cfg, "POST", f"/api/sessions/{wa_cfg['waha_session']}/logout")
        if response.status_code not in (200, 201, 204):
            response.raise_for_status()
    except Exception as exc:
        logger.warning("WAHA logout gagal: %s", exc)
        raise HTTPException(status_code=502, detail="Gagal logout session WhatsApp")

    return {
        "message": "Session WhatsApp berhasil diputus",
        "session": wa_cfg["waha_session"],
    }


@api_router.post("/whatsapp/test")
async def whatsapp_test(data: WhatsAppTestInput, current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["sub"], "deletedAt": None})
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    own_phone = normalize_whatsapp_phone(user.get("phone"))
    requested_phone = normalize_whatsapp_phone(data.phone)
    if requested_phone and requested_phone != own_phone and current.get("role") not in ("Manager", "Admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki izin kirim test ke nomor lain")

    target_phone = requested_phone or own_phone
    if not target_phone:
        raise HTTPException(status_code=400, detail="Nomor WA tujuan tidak tersedia")

    message = (data.message or "Tes notifikasi WhatsApp dari ProManage").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Pesan test tidak boleh kosong")

    sent = await send_whatsapp_message(
        target_user={"id": user["id"], "name": user.get("name"), "phone": target_phone},
        message=message,
        notif_type="manual_test",
    )
    if not sent:
        raise HTTPException(
            status_code=502,
            detail="Gagal mengirim WhatsApp. Periksa konfigurasi provider (webhook/waha) dan status koneksi WA.",
        )

    return {
        "message": "Pesan test WhatsApp terkirim",
        "to": target_phone,
    }


# ===== STATS =====
@api_router.get("/stats")
async def get_stats(current=Depends(get_current_user)):
    projects = await db.projects.find({"deletedAt": None}).to_list(1000)
    tasks = await db.tasks.find().to_list(5000)
    users = await db.users.find({"deletedAt": None}).to_list(1000)
    now = datetime.now(timezone.utc)

    active = sum(1 for p in projects if p.get('status') == 'Aktif')
    completed = sum(1 for p in projects if p.get('status') == 'Selesai')
    pending = sum(1 for p in projects if p.get('status') == 'Tertunda')
    completed_tasks = sum(1 for t in tasks if t.get('status') == 'Selesai')
    in_progress = sum(1 for t in tasks if t.get('status') == 'Dikerjakan')
    pending_tasks = sum(1 for t in tasks if t.get('status') == 'Belum Mulai')
    overdue = 0
    for t in tasks:
        due = parse_iso_datetime(t.get("dueDate"))
        if due and due < now and t.get("status") != "Selesai":
            overdue += 1

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
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_origins=CORS_ORIGINS or ["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("id", unique=True)
    await db.users.create_index(
        "email",
        unique=True,
        partialFilterExpression={"email": {"$type": "string"}},
    )
    await db.users.create_index("phone", unique=True)
    await db.projects.create_index("id", unique=True)
    await db.tasks.create_index("id", unique=True)
    await db.tasks.create_index("projectId")
    await db.subtasks.create_index("id", unique=True)
    await db.subtasks.create_index("taskId")
    await db.comments.create_index("taskId")
    await db.notifications.create_index("id", unique=True)
    await db.notifications.create_index("targetUserId")
    await db.notifications.create_index("targetEmail")
    await ensure_bootstrap_admin()
    logger.info("ProManage API started - indexes created")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
