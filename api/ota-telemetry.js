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
  const user = body.user || 'Creator';
  const clientVersion = body.client_version || '1.2.5';
  const targetVersion = body.target_version || '1.2.5';
  const hardware = body.hardware || body.gpu || 'Discrete GPU / Multi-Core';
  const details = body.details || '';
  const timestamp = new Date().toISOString();

  let logMessage = '';
  let eventType = 'TELEMETRY';

  switch (action) {
    case 'stream_step':
      eventType = 'STREAM_STEP';
      const stepNum = body.step || '•';
      logMessage = `📡 [LIVE STREAM ${stepNum}] IP: ${clientIp} (${city}, ${country}) | User: ${user} | ${details} | Hardware: ${hardware}`;
      break;
    case 'download_started':
    case 'click_download':
      eventType = 'OTA_DOWNLOAD_STARTED';
      logMessage = `📥 [OTA DOWNLOAD STARTED] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Client: v${clientVersion} -> Target: v${targetVersion} | Hardware: ${hardware}`;
      break;
    case 'download_completed':
      eventType = 'OTA_DOWNLOAD_COMPLETE';
      logMessage = `📦 [OTA DOWNLOAD COMPLETE] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Binary v${targetVersion} verified on client disk!`;
      break;
    case 'update_applied':
    case 'updater_spawned':
      eventType = 'OTA_UPDATE_APPLIED';
      logMessage = `🚀 [OTA UPDATE APPLIED] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Hot-patch applied v${clientVersion} -> Relaunched v${targetVersion}!`;
      break;
    case 'app_started':
      eventType = 'APP_STARTED';
      logMessage = `💻 [APP ONLINE] IP: ${clientIp} (${city}, ${country}) | User: ${user} | v${clientVersion} | Hardware: ${hardware}`;
      break;
    case 'repair_runtime_installer':
      eventType = 'RUNTIME_INSTALLER_REPAIRED';
      logMessage = `🛡️ [RUNTIMEINSTALLER 0xC0000005 CURED] IP: ${clientIp} (${city}, ${country}) | User: ${user} | SLStore/SLCache purged & NTFS Full Control unlocked! | Hardware: ${hardware}`;
      break;
    case 'repair_universal':
      eventType = 'UNIVERSAL_REPAIR_EXECUTED';
      logMessage = `🚀 [1-CLICK UNIVERSAL REPAIR] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Full Suite Healed | Details: ${details || 'All modules executed'}`;
      break;
    case 'premiere_launched':
      eventType = 'PREMIERE_LAUNCHED';
      logMessage = `🎬 [PREMIERE LAUNCHED VIA REPAIRED ENGINE] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Launch Target: ${details || 'Premiere Pro 2026'}`;
      break;
    case 'crash_detected':
      eventType = 'CRASH_REPORTED';
      logMessage = `⚠️ [CRASH REPORTED BY CLIENT] IP: ${clientIp} (${city}, ${country}) | User: ${user} | Details: ${details}`;
      break;
    default:
      logMessage = `📡 [TELEMETRY: ${action.toUpperCase()}] IP: ${clientIp} (${city}, ${country}) | User: ${user} | v${clientVersion} | Event: ${action} | Details: ${details}`;
      break;
  }

  // Print directly to Vercel console logs
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
