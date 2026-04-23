import { API } from "./config";

export async function parsePptx(file) {
  const form = new FormData();
  form.append("pptx", file);

  const res = await fetch(`${API}/parser/parse`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Parse failed");
  }

  return await res.json();
}

export async function submitPersona(data) {
  const res = await fetch(`${API}/parser/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Submit failed");
  }
  return await res.json();
}

export async function loadPersona(data) {
  const res = await fetch(`${API}/chat/load-persona`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Load persona failed");
  }
  return await res.json();
}

export async function streamChat(message, history = []) {
  const res = await fetch(`${API}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_message: message, history }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Chat failed");
  }
  return res.body;
}
