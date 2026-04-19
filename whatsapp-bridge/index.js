import express from 'express';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import qrcode from 'qrcode-terminal';
import dotenv from 'dotenv';
import cors from 'cors';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3002;
const TOKEN = process.env.WHATSAPP_WEBHOOK_TOKEN || 'local-secure-token';

app.use(cors());
app.use(express.json());

// Auth Middleware
const authenticate = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.split(' ')[1] : authHeader;

    if (token === TOKEN) {
        return next();
    }
    return res.status(401).json({ error: 'Unauthorized' });
};

class WhatsAppManager {
    constructor() {
        this.client = null;
        this.status = 'DISCONNECTED';
    }

    initialize() {
        console.log('[WhatsApp Bridge] Initializing...');
        this.status = 'CONNECTING';

        this.client = new Client({
            authStrategy: new LocalAuth({
                clientId: 'promanage-session'
            }),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            }
        });

        this.setupEventListeners();
        this.client.initialize();
    }

    setupEventListeners() {
        this.client.on('qr', (qr) => {
            console.log('[WhatsApp Bridge] QR RECEIVED. Scan this with your phone:');
            qrcode.generate(qr, { small: true });
            this.status = 'QR_REQUIRED';
        });

        this.client.on('ready', () => {
            console.log('[WhatsApp Bridge] Connected successfully!');
            this.status = 'READY';
        });

        this.client.on('authenticated', () => {
            this.status = 'AUTHENTICATED';
        });

        this.client.on('disconnected', (reason) => {
            console.log('[WhatsApp Bridge] Client disconnected:', reason);
            this.status = 'DISCONNECTED';
            setTimeout(() => this.initialize(), 5000);
        });
    }

    async sendMessage(phone, message) {
        if (this.status !== 'READY') throw new Error('WhatsApp Client is not ready');
        
        // Clean phone number
        let formattedPhone = phone.replace(/[^0-9]/g, '');
        if (formattedPhone.startsWith('0')) formattedPhone = '62' + formattedPhone.substring(1);
        if (!formattedPhone.includes('@c.us')) formattedPhone = `${formattedPhone}@c.us`;

        await this.client.sendMessage(formattedPhone, message);
    }
}

const waManager = new WhatsAppManager();
waManager.initialize();

// Routes
app.get('/status', (req, res) => {
    res.json({ status: waManager.status });
});

app.post('/send', authenticate, async (req, res) => {
    const { to, message } = req.body;
    
    if (!to || !message) {
        return res.status(400).json({ error: 'Missing to or message' });
    }

    try {
        await waManager.sendMessage(to, message);
        res.json({ success: true });
    } catch (err) {
        console.error('[WhatsApp Bridge] Send Error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`[WhatsApp Bridge] API running on http://localhost:${PORT}`);
    console.log(`[WhatsApp Bridge] Secure Token: ${TOKEN}`);
});
