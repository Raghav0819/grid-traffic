const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function detect(file: File, conf: number = 0.25) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/api/detect?conf=${conf}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Detection failed: ${res.status}`);
  return res.json();
}

export async function detectRaw(file: File, conf: number = 0.25) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/api/detect/raw?conf=${conf}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Raw detection failed: ${res.status}`);
  return res.json();
}

export async function downloadPdf(data: {
  plate: string;
  violations: string[];
  total_fine: number;
  timestamp: string;
  riders: number;
  facts: Record<string, unknown>;
}) {
  const res = await fetch(`${API}/api/challan/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`PDF generation failed: ${res.status}`);
  return res.blob();
}

export async function getAnalytics() {
  const res = await fetch(`${API}/api/analytics`);
  if (!res.ok) throw new Error(`Analytics failed: ${res.status}`);
  return res.json();
}

export async function getHistory(query: string = "") {
  const url = query
    ? `${API}/api/history?q=${encodeURIComponent(query)}`
    : `${API}/api/history`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`History failed: ${res.status}`);
  return res.json();
}

export async function ragQuery(query: string) {
  const res = await fetch(`${API}/api/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`RAG query failed: ${res.status}`);
  return res.json();
}

export async function ragChat(message: string, history: { role: string; content: string }[] = []) {
  const res = await fetch(`${API}/api/rag/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}
