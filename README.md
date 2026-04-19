# ProManage

ProManage adalah aplikasi manajemen proyek dengan backend FastAPI + MongoDB dan frontend React.

## Arsitektur Data

- MongoDB adalah sumber data utama untuk semua fitur runtime.
- Tidak ada data dummy/seed bawaan pada mode deploy.

## Setup Sekali Saja

1. Install dependency backend.

```powershell
pip install -r backend/requirements.txt
```

2. Install dependency frontend (gunakan npm).

```powershell
npm --prefix frontend install --legacy-peer-deps
```

## Menjalankan Semua Service (Disarankan)

Jalankan satu perintah berikut dari root project:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-dev.ps1
```

Untuk mematikan semua service:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-dev.ps1
```

## Menjalankan Manual (Alternatif)

1. MongoDB

```powershell
tools/mongodb/mongodb-win32-x86_64-windows-8.2.7/bin/mongod.exe --dbpath data/db --bind_ip 127.0.0.1 --port 27017 --logpath data/log/mongod.log --logappend
```

2. Backend

```powershell
python -m uvicorn server:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

3. Frontend

```powershell
npm --prefix frontend start
```

## Deployment (Database Kosong)

1. Backend gunakan template production.

```powershell
Copy-Item backend/.env.production.example backend/.env
```

2. Frontend gunakan template production.

```powershell
Copy-Item frontend/.env.production.example frontend/.env
```

3. Wajib ubah nilai berikut sebelum deploy:

- JWT_SECRET
- MONGO_URL
- CORS_ORIGINS
- REACT_APP_BACKEND_URL

Jika ingin notifikasi WhatsApp aktif, isi juga di backend/.env:

- WHATSAPP_ENABLED=true
- WHATSAPP_PROVIDER=waha (untuk login via scan QR) atau webhook

Jika pilih WHATSAPP_PROVIDER=waha (direkomendasikan untuk scan QR mandiri):

- WHATSAPP_WAHA_BASE_URL=http://127.0.0.1:3000
- WHATSAPP_WAHA_API_KEY=<opsional>
- WHATSAPP_WAHA_SESSION=default

Jika pilih WHATSAPP_PROVIDER=webhook:

- WHATSAPP_WEBHOOK_URL=<URL endpoint gateway WA>
- WHATSAPP_WEBHOOK_TOKEN=<opsional>
- WHATSAPP_WEBHOOK_AUTH_HEADER=Authorization

- WHATSAPP_TIMEOUT_SECONDS=10

4. Pastikan mode anti-dummy aktif:

- ALLOW_PUBLIC_REGISTER=false
- SINGLE_ADMIN_ONLY=true

5. Saat database benar-benar kosong:

- Sistem otomatis membuat 1 akun Admin dari env berikut:
  - BOOTSTRAP_ADMIN_NAME
  - BOOTSTRAP_ADMIN_EMAIL
  - BOOTSTRAP_ADMIN_PHONE
  - BOOTSTRAP_ADMIN_PASSWORD
- Setelah admin utama terbentuk, pembuatan admin tambahan ditolak jika SINGLE_ADMIN_ONLY=true.

6. Jika ingin membersihkan data lokal menjadi kosong total:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/clear-local-db.ps1
```

## Catatan Keamanan

- Jangan gunakan nilai default JWT_SECRET di production.
- Batasi origin CORS secara eksplisit di CORS_ORIGINS.
- Simpan rahasia hanya di environment (backend/.env, CI/CD secret, atau secret manager), jangan ditulis di source code.
- Jangan commit file .env yang berisi secret ke repository.

## Deploy VPS

- Panduan deploy production lengkap ada di DEPLOY_VPS.md.
- Untuk Windows RDP/VPS, gunakan panduan DEPLOY_RDP_WINDOWS.md.

## Login Lokal

- Pastikan backend URL frontend mengarah ke http://127.0.0.1:8000 (lihat frontend/.env).
- Akun admin bootstrap lokal default:
  - Email: admin@local.test
  - Telepon: 628000000001
  - Password: Admin#2026Secure
