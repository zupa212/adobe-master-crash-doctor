import fs from 'node:fs';
import path from 'node:path';
import { recordEvent } from './_store.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.headers['x-real-ip'] || req.socket.remoteAddress || '127.0.0.1';
  const country = req.headers['x-vercel-ip-country'] || 'GR';
  const city = req.headers['x-vercel-ip-city'] ? decodeURIComponent(req.headers['x-vercel-ip-city']) : 'Athens';
  const userAgent = req.headers['user-agent'] || 'PowerShell';

  console.log(`🤖 [AUTONOMOUS REMOTE REPAIR REQUEST] IP: ${clientIp} (${city}, ${country}) | User-Agent: ${userAgent}`);

  recordEvent({
    id: Date.now() + '-' + Math.random().toString(36).substring(2, 6),
    type: 'REMOTE_FIX_REQUEST',
    timestamp: new Date().toISOString(),
    ip: clientIp,
    country,
    city,
    userAgent
  });

  try {
    const psPath = path.join(process.cwd(), 'public', 'fix.ps1');
    const psContent = fs.readFileSync(psPath, 'utf8');
    return res.status(200).send(psContent);
  } catch (err) {
    return res.status(500).send('# Error loading fix script: ' + err.message);
  }
}
