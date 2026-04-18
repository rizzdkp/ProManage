from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


def generate_id(prefix: str = ""):
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# Auth Models
class RegisterInput(BaseModel):
    name: str
    phone: str
    password: str
    email: Optional[str] = None


class LoginInput(BaseModel):
    identifier: str  # email or phone
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


# User Models
class UserInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("usr-"))
    email: Optional[str] = None
    name: str
    role: str = "Anggota Tim"
    phone: str
    password_hash: str
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    createdBy: Optional[str] = None
    deletedAt: Optional[str] = None
    avatar: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: Optional[str] = None
    name: str
    role: str
    phone: str
    createdAt: str
    createdBy: Optional[str] = None
    deletedAt: Optional[str] = None
    avatar: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CreateUserInput(BaseModel):
    name: str
    phone: str
    password: str
    email: Optional[str] = None
    role: str = "Anggota Tim"


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str


# Project Models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    startDate: str
    endDate: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    status: Optional[str] = None
    teamMembers: Optional[List[str]] = None


class ProjectInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("prj-"))
    name: str
    description: str = ""
    startDate: str
    endDate: str
    status: str = "Aktif"
    teamMembers: List[str] = []
    createdBy: str
    progress: int = 0
    deletedAt: Optional[str] = None


# Task Models
class TaskCreate(BaseModel):
    projectId: str
    name: str
    description: Optional[str] = ""
    dueDate: str
    priority: str = "Sedang"
    assignee: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dueDate: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None


class TaskInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("tsk-"))
    projectId: str
    name: str
    description: str = ""
    dueDate: str
    priority: str = "Sedang"
    status: str = "Belum Mulai"
    assignee: Optional[str] = None


# Subtask Models
class SubtaskCreate(BaseModel):
    taskId: str
    title: str
    projectId: str


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    isDone: Optional[bool] = None


class SubtaskInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("sub-"))
    taskId: str
    title: str
    isDone: bool = False
    projectId: str


# Comment Models
class CommentCreate(BaseModel):
    taskId: str
    message: str


class CommentInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("cmt-"))
    taskId: str
    actor: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# Notification Models
class NotificationInDB(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("ntf-"))
    type: str
    taskId: Optional[str] = None
    message: str
    targetEmail: str
    isRead: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
