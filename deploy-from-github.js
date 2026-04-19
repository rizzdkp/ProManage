import { Client } from 'ssh2';

const config = {
    host: '203.194.113.16',
    port: 22,
    username: 'root',
    password: '1$RW83NwrPF!80'
};

// REPLACE dengan GitHub username mu
const GITHUB_USERNAME = 'REPLACE_WITH_YOUR_USERNAME';
const GITHUB_REPO = `https://github.com/${GITHUB_USERNAME}/ProManage.git`;
const REMOTE_ROOT = '/opt/promanage';

const conn = new Client();

function run(cmd) {
    return new Promise((resolve) => {
        console.log('\n>>> ' + cmd);
        conn.exec(cmd, (err, stream) => {
            if (err) {
                console.error('Error:', err);
                return resolve();
            }
            stream.on('close', () => resolve()).on('data', (data) => {
                process.stdout.write(data);
            }).stderr.on('data', (data) => {
                process.stderr.write(data);
            });
        });
    });
}

async function deployFromGitHub() {
    conn.on('ready', async () => {
        console.log('\n✅ SSH Connected\n');
        console.log('════════════════════════════════════════');
        console.log('  ProManage Deploy from GitHub');
        console.log('════════════════════════════════════════');
        
        try {
            // 1. Backup existing
            console.log('\n📦 Step 1: Backup current installation...');
            await run(`backup_dir="/opt/promanage.backup.$(date +%Y%m%d_%H%M%S)" && cp -r ${REMOTE_ROOT} $backup_dir && echo "Backup: $backup_dir"`);
            
            // 2. Backup .env files
            console.log('\n📋 Step 2: Backup environment files...');
            await run(`cp ${REMOTE_ROOT}/backend/.env /tmp/backend.env.backup 2>/dev/null || true`);
            await run(`cp ${REMOTE_ROOT}/frontend/.env /tmp/frontend.env.backup 2>/dev/null || true`);
            
            // 3. Clone latest from GitHub
            console.log('\n📥 Step 3: Clone from GitHub...');
            await run(`cd /opt && rm -rf promanage && git clone ${GITHUB_REPO} promanage`);
            
            // 4. Restore .env files
            console.log('\n📋 Step 4: Restore environment files...');
            await run(`cp /tmp/backend.env.backup ${REMOTE_ROOT}/backend/.env 2>/dev/null || echo "No backup found"`);
            await run(`cp /tmp/frontend.env.backup ${REMOTE_ROOT}/frontend/.env 2>/dev/null || echo "No backup found"`);
            
            // 5. Install backend
            console.log('\n🔧 Step 5: Setup backend...');
            await run(`cd ${REMOTE_ROOT} && if [ ! -d ".venv" ]; then python3 -m venv .venv; fi`);
            await run(`cd ${REMOTE_ROOT} && . .venv/bin/activate && pip install --upgrade pip`);
            await run(`cd ${REMOTE_ROOT} && . .venv/bin/activate && pip install -r backend/requirements.txt`);
            
            // 6. Setup WhatsApp Bridge
            console.log('\n💬 Step 6: Setup WhatsApp Bridge...');
            await run(`cd ${REMOTE_ROOT}/whatsapp-bridge && npm install`);
            await run(`pm2 delete promanage-wa-bridge || true`);
            await run(`cd ${REMOTE_ROOT}/whatsapp-bridge && pm2 start index.js --name "promanage-wa-bridge"`);
            
            // 7. Restart backend
            console.log('\n🔄 Step 7: Restart backend service...');
            await run(`systemctl daemon-reload`);
            await run(`systemctl restart promanage-backend`);
            
            // 8. Verify
            console.log('\n✅ Step 8: Verify deployment...');
            await new Promise(r => setTimeout(r, 3000));
            await run(`systemctl status promanage-backend --no-pager`);
            await run(`pm2 status`);
            
            console.log('\n════════════════════════════════════════');
            console.log('✅ Deployment from GitHub completed!');
            console.log('════════════════════════════════════════');
            console.log('\n🌐 Access: https://promanage.rizzdkp.online/login');
            console.log('📧 Email: admin@rizzdkp.online');
            console.log('🔑 Password: jancok99');
            
        } catch (e) {
            console.error('\n❌ ERROR:', e.message);
            console.log('\nNote: Check SSH connection or VPS status');
        } finally {
            conn.end();
        }
    }).connect(config);
}

console.log('🚀 ProManage GitHub Deploy\n');

if (GITHUB_USERNAME === 'REPLACE_WITH_YOUR_USERNAME') {
    console.error('❌ ERROR: Please update GITHUB_USERNAME in this file!');
    console.error('   Replace REPLACE_WITH_YOUR_USERNAME with your GitHub username\n');
    process.exit(1);
}

deployFromGitHub();
