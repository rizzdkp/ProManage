# Deploy ProManage di VPS (Production)

Panduan ini untuk VPS Linux Ubuntu 22.04/24.04, termasuk skenario tanpa domain (akses via IP publik).

## 1. Install Dependensi Sistem

```bash
sudo apt update
sudo apt install -y curl ca-certificates gnupg lsb-release software-properties-common git rsync nginx python3 python3-venv python3-pip
```

Install Node.js LTS:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Install MongoDB Community (official repo):

```bash
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list > /dev/null
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod --no-pager
```

## 2. Clone Project

```bash
sudo mkdir -p /opt/promanage
sudo chown -R $USER:$USER /opt/promanage
git clone <REPO_URL> /opt/promanage
cd /opt/promanage
```

## 3. Setup Backend

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.production.example backend/.env
```

Edit backend/.env:

- JWT_SECRET
- MONGO_URL (default lokal: mongodb://127.0.0.1:27017)
- DB_NAME
- CORS_ORIGINS
- ALLOW_PUBLIC_REGISTER=false
- SINGLE_ADMIN_ONLY=true
- BOOTSTRAP_ADMIN_NAME
- BOOTSTRAP_ADMIN_EMAIL
- BOOTSTRAP_ADMIN_PHONE
- BOOTSTRAP_ADMIN_PASSWORD

Catatan:

- Saat database kosong, backend otomatis membuat 1 akun Admin dari BOOTSTRAP_ADMIN_*.
- Dengan SINGLE_ADMIN_ONLY=true, admin tambahan ditolak.

## 4. Setup Frontend

```bash
cp frontend/.env.production.example frontend/.env
```

Jika akses via IP publik, set:

- REACT_APP_BACKEND_URL=http://YOUR_VPS_IP

Build frontend:

```bash
npm --prefix frontend install --legacy-peer-deps
npm --prefix frontend run build
```

Publish build:

```bash
sudo mkdir -p /var/www/promanage
sudo rsync -av --delete frontend/build/ /var/www/promanage/
```

## 5. Konfigurasi systemd Backend

```bash
sudo cp deploy/promanage-backend.service /etc/systemd/system/promanage-backend.service
sudo systemctl daemon-reload
sudo systemctl enable promanage-backend
sudo systemctl restart promanage-backend
sudo systemctl status promanage-backend --no-pager
```

## 6. Konfigurasi Nginx

```bash
sudo cp deploy/promanage-nginx.conf /etc/nginx/sites-available/promanage
sudo ln -sf /etc/nginx/sites-available/promanage /etc/nginx/sites-enabled/promanage
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Buka Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw --force enable
sudo ufw status
```

## 8. Verifikasi Deploy

Cek API internal:

```bash
curl http://127.0.0.1:8000/api/
```

Cek dari browser publik:

- http://YOUR_VPS_IP/login

Login pertama pakai:

- BOOTSTRAP_ADMIN_EMAIL atau BOOTSTRAP_ADMIN_PHONE
- BOOTSTRAP_ADMIN_PASSWORD

## 9. Update Rutin

```bash
cd /opt/promanage
git pull
. .venv/bin/activate
pip install -r backend/requirements.txt
npm --prefix frontend install --legacy-peer-deps
npm --prefix frontend run build
sudo rsync -av --delete frontend/build/ /var/www/promanage/
sudo systemctl restart promanage-backend
sudo systemctl restart nginx
```
