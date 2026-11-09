import { evaluateSpotOpportunity } from "../lib/risk.js";
export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ error: "METHOD_NOT_ALLOWED" });
  const expected = process.env.WUNDERDESK_CONTROL_TOKEN;
  if (!expected || req.headers.authorization !== `Bearer ${expected}`)
    return res.status(401).json({ error: "UNAUTHORIZED" });
  const payload = req.body;
  if (!payload || typeof payload !== "object" || Array.isArray(payload))
    return res.status(400).json({ error: "INVALID_JSON_BODY" });
  return res.status(200).json(evaluateSpotOpportunity(payload));
}
