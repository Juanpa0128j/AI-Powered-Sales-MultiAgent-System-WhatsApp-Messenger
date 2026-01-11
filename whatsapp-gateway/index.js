const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');

const app = express();
const PORT = 3000;
const PYTHON_BACKEND_URL = 'http://localhost:8000/webhook';

app.use(bodyParser.json());

// Initialize WhatsApp Client
// puppeteer props allowed to run in root/docker if needed
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('QR RECEIVED', qr);
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('Client is ready!');
});

const fs = require('fs');
const path = require('path');
const mime = require('mime-types');

// Ensure media directory exists
const MEDIA_DIR = path.join(__dirname, 'media');
if (!fs.existsSync(MEDIA_DIR)) {
    fs.mkdirSync(MEDIA_DIR);
}

// Forward incoming messages AND Self-Sent Commands to Python Backend
client.on('message_create', async msg => {
    // Ignore status updates/broadcasts
    if (msg.from === 'status@broadcast') return;

    // Ignore Groups (User requirement: User-to-User only)
    if (msg.from.endsWith('@g.us') || (msg.to && msg.to.endsWith('@g.us'))) {
        return;
    }

    let payload = null;
    let localMediaPath = null;

    // Handle Media Download
    if (msg.hasMedia) {
        try {
            const media = await msg.downloadMedia();
            if (media) {
                const extension = mime.extension(media.mimetype) || 'dat';
                const filename = `${msg.id.id}.${extension}`;
                localMediaPath = path.join(MEDIA_DIR, filename);
                
                // Write file to disk (base64 to buffer)
                fs.writeFileSync(localMediaPath, media.data, 'base64');
                console.log(`Media saved to: ${localMediaPath}`);
            }
        } catch (err) {
            console.error('Failed to download media:', err);
        }
    }

    // CASE 1: Self-Sent Message (Admin Command?)
    if (msg.fromMe) {
        // Only forward if it looks like a command
        if (!msg.body.startsWith('/')) return;

        console.log(`Admin Command sent to ${msg.to}: ${msg.body}`);
        
        payload = {
            from: msg.to, 
            body: msg.body,
            hasMedia: msg.hasMedia,
            mediaPath: localMediaPath
        };
    } 
    // CASE 2: Incoming Message (Customer)
    else {
        console.log(`Received message from ${msg.from}: ${msg.body}`);
        payload = {
            from: msg.from,
            body: msg.body,
            hasMedia: msg.hasMedia,
            mediaPath: localMediaPath
        };
    }

    // Forward to Python
    if (payload) {
        try {
            await axios.post(PYTHON_BACKEND_URL, payload);
        } catch (error) {
            console.error('Error forwarding message to Python:', error.message);
        }
    }
});

// Endpoint to send messages FROM Python
app.post('/send', async (req, res) => {
    const { to, body, mediaUrl } = req.body;
    
    if (!to || (!body && !mediaUrl)) {
        return res.status(400).json({ error: 'Missing "to" or content ("body" or "mediaUrl")' });
    }

    try {
        // Normalize ID
        let chatId = to;
        
        // If it looks like a full ID (contains @), trust it.
        // e.g. "123456@c.us" or "123456@g.us"
        if (!chatId.includes('@')) {
            // If it's just a number, assume private chat
            chatId = chatId.replace('whatsapp:', '').replace('+', '');
             chatId = `${chatId}@c.us`;
        }

        // Handle Media
        if (mediaUrl) {
            const { MessageMedia } = require('whatsapp-web.js');
            const media = await MessageMedia.fromUrl(mediaUrl);
            await client.sendMessage(chatId, media, { caption: body || '' });
        } else {
            await client.sendMessage(chatId, body);
        }

        res.json({ status: 'sent', chatId });
        
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ error: 'Failed to send message' });
    }
});

// Start Server
app.listen(PORT, () => {
    console.log(`WhatsApp Bridge running on http://localhost:${PORT}`);
    client.initialize();
});
