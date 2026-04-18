# Deploy ProManage di Windows RDP/VPS

Panduan ini untuk Windows Server (akses RDP).

## 1. Persiapan Software

Install:

- Python 3.12+
- Node.js LTS
- MongoDB Community Server
- NSSM (Non-Sucking Service Manager) untuk menjalankan backend sebagai service
- Nginx Windows (opsional, untuk reverse proxy)

## 2. Clone Project

```powershell
git clone <REPO_URL> D:\apps\ProManage
Set-Location D:\apps\ProManage
```

## 3. Setup Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.production.example backend\.env
```

Edit backend/.env dan isi nilai production:

- JWT_SECRET
- MONGO_URL
- DB_NAME
- CORS_ORIGINS
- ALLOW_PUBLIC_REGISTER=false
- SINGLE_ADMIN_ONLY=true
- BOOTSTRAP_ADMIN_NAME
- BOOTSTRAP_ADMIN_EMAIL
- BOOTSTRAP_ADMIN_PHONE
- BOOTSTRAP_ADMIN_PASSWORD

## 4. Setup Frontend Build

```powershell
Copy-Item frontend\.env.production.example frontend\.env
```

Edit frontend/.env:

- REACT_APP_BACKEND_URL=http://YOUR_SERVER_IP

Build frontend:

```powershell
npm --prefix frontend install --legacy-peer-deps
npm --prefix frontend run build
```

## 5. Jalankan Backend Sebagai Windows Service (NSSM)

```powershell
nssm install ProManageBackend "D:\apps\ProManage\.venv\Scripts\python.exe" "-m uvicorn server:app --app-dir D:\apps\ProManage\backend --host 127.0.0.1 --port 8000"
nssm set ProManageBackend AppDirectory "D:\apps\ProManage"
nssm set ProManageBackend Start SERVICE_AUTO_START
nssm start ProManageBackend
```

## 6. Serve Frontend

Disarankan gunakan Nginx Windows untuk serve frontend/build dan proxy /api ke 127.0.0.1:8000.

## 7. Verifikasi

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/
```

Buka aplikasi di IP server lalu login pakai akun bootstrap admin.
