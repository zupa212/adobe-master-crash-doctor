import { recordEvent } from './_store.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, User-Agent');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.headers['x-real-ip'] || req.socket.remoteAddress || '127.0.0.1';
  const country = req.headers['x-vercel-ip-country'] || 'GR';
  const city = req.headers['x-vercel-ip-city'] ? decodeURIComponent(req.headers['x-vercel-ip-city']) : 'Athens';

  let body = {};
  if (req.method === 'POST') {
    body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  } else {
    body = req.query || {};
  }

  const action = body.action || body.event || 'general_ping';
  const user = body.user || 'Unknown';
  const clientVersion = body.client_version || 'Unknown';
  const targetVersion = body.target_version || '1.2.4';
  const hardware = body.hardware || body.gpu || 'Hardware';
  const timestamp = new Date().toISOString();

  let logMessage = '';
  let eventType = 'TELEMETRY';

  if (action === 'download_started' || action === 'click_download') {
    eventType = 'OTA_DOWNLOAD_STARTED';
    logMessage = `📥 [OTA DOWNLOAD STARTED] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Client v${clientVersion} -> Downloading v${targetVersion} | Hardware: ${hardware}`;
  } else if (action === 'download_completed') {
    eventType = 'OTA_DOWNLOAD_COMPLETE';
    logMessage = `📦 [OTA DOWNLOAD COMPLETE] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Binary v${targetVersion} verified on disk!`;
  } else if (action === 'update_applied' || action === 'updater_spawned') {
    eventType = 'OTA_UPDATE_APPLIED';
    logMessage = `🚀 [OTA UPDATE APPLIED] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Successfully patched from v${clientVersion} -> Relaunching v${targetVersion}!`;
  } else {
    logMessage = `ℹ️ [OTA TELEMETRY: ${action.toUpperCase()}] IP: ${clientIp} (${city}, ${country}) | User: ${user} | v${clientVersion} | Event: ${action}`;
  }

  // Print to Vercel Runtime Logs
  console.log(logMessage);

  const eventObj = {
    id: Date.now() + '-' + Math.random().toString(36).substring(2, 6),
    type: eventType,
    action,
    timestamp,
    ip: clientIp,
    country,
    city,
    user,
    clientVersion,
    targetVersion,
    hardware
  };

  recordEvent(eventObj);

  return res.status(200).json({
    status: 'ok',
    logged: true,
    event: eventType,
    clientIp,
    location: `${city}, ${country}`,
    timestamp
  });
}
