import { recordEvent } from './_store.js';

export default async function handler(req, res) {
  const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.headers['x-real-ip'] || req.socket.remoteAddress || '127.0.0.1';
  const country = req.headers['x-vercel-ip-country'] || 'GR';
  const city = req.headers['x-vercel-ip-city'] ? decodeURIComponent(req.headers['x-vercel-ip-city']) : 'Athens';
  const userAgent = req.headers['user-agent'] || 'Browser';
  const referer = req.headers['referer'] || 'Direct';

  const type = req.query.type || 'doctor';
  const targetUrl = type === 'repaired'
    ? 'https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Premiere%20Pro%20(Repaired).exe'
    : 'https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Master%20Crash%20Doctor.exe';

  const fileName = type === 'repaired' ? 'Adobe Premiere Pro (Repaired).exe' : 'Adobe Master Crash Doctor.exe';

  console.log(`📥 [DIRECT WEB DOWNLOAD] IP: ${clientIp} (${city}, ${country}) | File: ${fileName} | UA: ${userAgent} | Referer: ${referer}`);

  recordEvent({
    id: Date.now() + '-' + Math.random().toString(36).substring(2, 6),
    type: 'WEB_DOWNLOAD',
    timestamp: new Date().toISOString(),
    ip: clientIp,
    country,
    city,
    fileName,
    referer
  });

  // 302 Redirect to direct executable binary
  res.redirect(302, targetUrl);
}
