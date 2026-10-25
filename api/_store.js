import fs from 'node:fs';
import path from 'node:path';

const TMP_FILE = path.join('/tmp', 'ota_events.json');
globalThis.__otaLogs = globalThis.__otaLogs || [];

export function recordEvent(event) {
  // 1. Add to globalThis
  globalThis.__otaLogs.unshift(event);
  if (globalThis.__otaLogs.length > 100) {
    globalThis.__otaLogs.pop();
  }

  // 2. Persist to /tmp if available
  try {
    let list = [];
    if (fs.existsSync(TMP_FILE)) {
      list = JSON.parse(fs.readFileSync(TMP_FILE, 'utf8') || '[]');
    }
    list.unshift(event);
    if (list.length > 100) list = list.slice(0, 100);
    fs.writeFileSync(TMP_FILE, JSON.stringify(list), 'utf8');
  } catch (e) {
    // ignore filesystem write errors in ephemeral environments
  }
}

export function getEvents() {
  try {
    if (fs.existsSync(TMP_FILE)) {
      const fileData = JSON.parse(fs.readFileSync(TMP_FILE, 'utf8') || '[]');
      if (fileData && fileData.length > 0) {
        return fileData;
      }
    }
  } catch (e) {}
  return globalThis.__otaLogs || [];
}
