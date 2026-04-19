# GitHub & Deployment Setup Guide

## 📋 Overview

ProManage kini menggunakan GitHub untuk version control dan deployment otomatis ke VPS.

## 🚀 Step-by-Step Setup

### 1. Create GitHub Repository

- Go to https://github.com/new
- Repository name: `ProManage`
- Description: `Project management with WhatsApp integration`
- Choose Public or Private
- **IMPORTANT**: Do NOT initialize with README, .gitignore, or license
- Click "Create repository"

### 2. Push Existing Code

Jalan Commands berikut (replace `USERNAME` dengan GitHub username mu):

```bash
git branch -M main
git remote add origin https://github.com/USERNAME/ProManage.git
git push -u origin main
```

Atau menggunakan GitHub CLI:

```bash
gh repo create ProManage --public --source=. --remote=origin --push
```

### 3. Verify GitHub Repository

- Buka https://github.com/USERNAME/ProManage
- Lihat files sudah ter-push dengan benar
- Check that `.env` files tidak di-push (protected by .gitignore)

## 🔄 Deployment dari GitHub

### Prerequisites

- GitHub repository sudah di-setup
- VPS credentials: `203.194.113.16` (sudah ada)

### Update Script

Edit `deploy-from-github.js`:

```javascript
// Line 8: Replace dengan GitHub username
const GITHUB_USERNAME = 'YOUR_USERNAME';
```

### Deploy to VPS

```powershell
node deploy-from-github.js
```

Script akan:
1. ✅ Backup current installation
2. ✅ Backup .env files
3. ✅ Clone latest code dari GitHub
4. ✅ Restore .env files
5. ✅ Install dependencies (Python + Node)
6. ✅ Setup WhatsApp Bridge
7. ✅ Restart services
8. ✅ Verify deployment

## 📝 .env Files (Protected)

Files ini NOT di-push ke GitHub (via .gitignore):

- `backend/.env` - Backend config (JWT_SECRET, MongoDB, WhatsApp)
- `frontend/.env` - Frontend config (API URLs)

Saat deploy, files ini di-restore dari backup untuk continuity.

## 🔐 Credentials

| Item | Value |
|------|-------|
| Domain | promanage.rizzdkp.online |
| VPS IP | 203.194.113.16 |
| SSH User | root |
| API Port | 8000 |
| WA Bridge | 3000 (internal) |
| Admin Email | admin@rizzdkp.online |
| Admin Password | jancok99 |

## 📦 Repository Structure

```
ProManage/
├── backend/              # FastAPI application
│   ├── auth.py
│   ├── models.py
│   ├── server.py
│   ├── requirements.txt
│   ├── .env            (NOT in git)
│   └── .env.example    (in git)
├── frontend/            # React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env            (NOT in git)
├── whatsapp-bridge/     # WhatsApp integration
│   ├── index.js
│   └── package.json
├── deploy/              # Deployment configs
│   ├── promanage-backend.service
│   └── promanage-nginx.conf
├── scripts/             # Dev scripts
├── tests/               # Test files
└── .gitignore          # Excludes sensitive files
```

## ✅ Workflow

### Local Development

```bash
# 1. Make changes
# 2. Test locally
# 3. Commit to git
git add .
git commit -m "Description of changes"

# 4. Push to GitHub
git push

# 5. (Optional) Tag release
git tag v1.0.1
git push --tags
```

### Deploy to Production

```bash
# Update deploy script with GitHub username
# Then run:
node deploy-from-github.js
```

## 🛠️ Troubleshooting

### SSH Connection Timeout

```bash
# Test connection
ssh -v root@203.194.113.16

# Check VPS status
# Try manual deployment via SSH
ssh root@203.194.113.16
```

### Deploy Fails

```bash
# Check VPS logs
ssh root@203.194.113.16 'journalctl -u promanage-backend -n 50'

# Check backup exists
ssh root@203.194.113.16 'ls -la /opt/promanage.backup.*'

# Restore from backup if needed
ssh root@203.194.113.16 'cp -r /opt/promanage.backup.LATEST /opt/promanage'
```

### Missing Dependencies

```bash
# Manually install
ssh root@203.194.113.16 'cd /opt/promanage && . .venv/bin/activate && pip install -r backend/requirements.txt'
```

## 📚 References

- GitHub Docs: https://docs.github.com
- FastAPI: https://fastapi.tiangolo.com
- MongoDB: https://docs.mongodb.com
- WhatsApp WAHA: https://waha.devlike.dev

## ❓ Need Help?

Contact: admin@rizzdkp.online

---

Last Updated: 2026-04-19
