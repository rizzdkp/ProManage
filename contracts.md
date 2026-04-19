# ProManage API Contracts

## Auth
- `POST /api/auth/register` → {name, phone, password, email?} → {user, token}
- `POST /api/auth/login` → {identifier, password} → {user, token}
- Auth via JWT Bearer token in Authorization header

## Projects
- `GET /api/projects` → [{id, name, description, startDate, endDate, status, teamMembers, createdBy, progress, deletedAt}]
- `POST /api/projects` → {name, description, startDate, endDate} → project
- `GET /api/projects/{id}` → project with computed progress
- `PUT /api/projects/{id}` → {fields} → updated project
- `DELETE /api/projects/{id}` → soft delete (set deletedAt)

## Tasks
- `GET /api/tasks?projectId=x` → [task]
- `POST /api/tasks` → {projectId, name, description, dueDate, priority, assignee} → task
- `PATCH /api/tasks/{id}` → {fields} → task (reject status=Selesai if subtasks incomplete)

## Subtasks
- `GET /api/subtasks?taskId=x` → [subtask]
- `POST /api/subtasks` → {taskId, title, projectId} → subtask
- `PUT /api/subtasks/{id}` → {title?, isDone?} → subtask
- `DELETE /api/subtasks/{id}` → deleted

## Comments
- `GET /api/comments?taskId=x` → [comment]
- `POST /api/comments` → {taskId, message} → comment

## Users
- `GET /api/users` → [user] (no password)
- `GET /api/users/{id}` → user
- `PUT /api/users/{id}` → {name?, email?, phone?} → user
- `DELETE /api/users/{id}` → soft delete
- `GET /api/users/role?role=x` → [user]
- `PUT /api/users/{id}/password` → {currentPassword, newPassword}

## Notifications
- `GET /api/notifications` → [notification] for current user
- `PATCH /api/notifications/{id}/read` → mark as read

## WhatsApp
- `GET /api/whatsapp/status` → {enabled, provider, configured, connected, lastPing, session?, sessionState?, needsQrScan?}
- `POST /api/whatsapp/connect` → inisialisasi/aktifkan session WA (provider waha)
- `GET /api/whatsapp/qr` → ambil QR image untuk scan login WhatsApp
- `POST /api/whatsapp/logout` → putuskan session WA yang sedang aktif
- `POST /api/whatsapp/test` → {phone?, message?} → kirim pesan test ke gateway WA

## Mock Data to Replace
- mockUsers → /api/users + /api/auth
- mockProjects → /api/projects  
- mockTasks → /api/tasks
- mockSubtasks → /api/subtasks
- mockComments → /api/comments
- mockNotifications → /api/notifications
- mockWhatsAppStatus → /api/whatsapp/status
- mockStats → computed from /api/projects + /api/tasks + /api/users

## Frontend Integration
- Create /src/lib/api.js with axios instance + auth interceptor
- Replace all mock imports with API calls using React state + useEffect
- Store JWT in localStorage, attach to all requests
- AuthContext: real login/register via API, token management
