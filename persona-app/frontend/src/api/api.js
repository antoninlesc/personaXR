const API_BASE = "http://192.168.1.13:8000";
const API = "http://127.0.0.1:8000";

export async function parsePptx(file) {
  const form = new FormData();
  form.append("pptx", file);

  const res = await fetch(`${API}/parse`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Parse failed");
  }

  return await res.json();
}
