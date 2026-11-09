export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "GET") return res.status(405).json({ error: "METHOD_NOT_ALLOWED" });
  return res.status(200).json({
    service: "wunderdesk", mode: "PAPER", liveTradingEnabled: false,
    executionAdapter: "NOT_CONFIGURED", durableLedger: "NOT_CONFIGURED",
    exchange: "MEXC", supportedMarketType: "spot",
    warning: "No live order path is exposed by this deployment."
  });
}
