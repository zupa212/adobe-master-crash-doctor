import fs from 'node:fs';
import path from 'node:path';
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
  const region = req.headers['x-vercel-ip-country-region'] || '';

  const clientVersion = req.query.client_version || req.query.v || 'Unknown';
  const clientBuild = req.query.build || 'Unknown';
  const cpu = req.query.cpu ? decodeURIComponent(req.query.cpu) : 'Standard CPU';
  const gpu = req.query.gpu ? decodeURIComponent(req.query.gpu) : 'Standard GPU';
  const user = req.query.user ? decodeURIComponent(req.query.user) : 'Creator';

  // Read manifest
  let manifest = {
    version: '1.2.4',
    build_number: 124,
    release_date: '2026-10-25',
    min_os: 'Windows 10 / 11 64-bit',
    app_name: 'Adobe Master Crash Doctor',
    download_url: 'https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Master%20Crash%20Doctor.exe',
    launcher_url: 'https://github.com/zupa212/adobe-master-crash-doctor/raw/main/Adobe%20Premiere%20Pro%20(Repaired).exe',
    repository: 'https://github.com/zupa212/adobe-master-crash-doctor',
    changelog: [
      '🧠 Claude Opus 5.5 Max Deep Registry Auto-Healer: Architectural kernel & registry injection via Live API Gateway / Embedded Gold Master Matrix',
      '🎮 NVIDIA RTX 5060 (Blackwell) & AMD Ryzen 5 Dual-GPU Deconfliction: AMD Radeon iGPU decode disabled / NVIDIA NVDEC CUDA hardware prioritized',
      '🔥 1-Click Nuclear Driver & Service Uninstaller: Complete root eradication of AGSService, AdobeARMservice, AdobeUpdateService, scheduled tasks, registry trees & licensing tokens',
      '⏱️ Windows Kernel Graphics TDR Delay Boost: TdrDelay=10s, TdrDdiDelay=10s, HwSchMode=2 hardware-accelerated GPU scheduling',
      '🛡️ Broken CLSID Namespace Shell Extensions Sanitization: Prevents Explorer and RuntimeInstaller.DLL 0xc0000005 crashes'
    ]
  };

  try {
    const versionPath = path.join(process.cwd(), 'version.json');
    if (fs.existsSync(versionPath)) {
      manifest = JSON.parse(fs.readFileSync(versionPath, 'utf8'));
    }
  } catch (err) {
    // fallback
  }

  const isUpdateAvailable = clientVersion !== manifest.version && clientVersion !== 'Unknown';

  const timestamp = new Date().toISOString();
  const logMessage = `📡 [OTA CHECK] IP: ${clientIp} | Location: ${city}, ${country} | User: ${user} | Client: v${clientVersion} (Build ${clientBuild}) | Hardware: ${gpu} / ${cpu} | Update Served: ${isUpdateAvailable ? `YES (v${manifest.version})` : `UP TO DATE (v${manifest.version})`}`;

  console.log(logMessage);

  const eventObj = {
    id: Date.now() + '-' + Math.random().toString(36).substring(2, 6),
    type: 'OTA_CHECK',
    timestamp,
    ip: clientIp,
    country,
    city,
    user,
    clientVersion,
    clientBuild,
    hardware: `${gpu} | ${cpu}`,
    servedVersion: manifest.version,
    updateAvailable: isUpdateAvailable
  };

  recordEvent(eventObj);

  return res.status(200).json(manifest);
}
