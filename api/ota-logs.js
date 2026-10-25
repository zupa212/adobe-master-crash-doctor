import { getEvents } from './_store.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const events = getEvents();

  return res.status(200).json({
    status: 'ok',
    total_recorded_events: events.length,
    events: events.slice(0, 100)
  });
}
