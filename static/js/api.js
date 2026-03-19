/**
 * api.js
 * Shared API client, token management, toast, and utility helpers.
 * Loaded first — all other JS files depend on these.
 */

// ── TOKEN / SESSION STATE ──
let token = localStorage.getItem('mp_token') || null;
let currentUser = localStorage.getItem('mp_email') || null;

/**
 * Central fetch wrapper.
 * Automatically attaches JWT, parses JSON, and throws on error.
 */
async function api(method, path, body = null, auth = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Auto-logout on 401
  if (res.status === 401) {
    logout();
    throw new Error('Session expired — please sign in again');
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

// ── TOAST NOTIFICATIONS ──
let toastTimer;
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = ''; }, 3000);
}

// ── SHARED HELPERS ──

/** Returns the CSS colour variable for a prediction label */
function labelColor(label) {
  if (!label) return 'var(--muted)';
  const l = label.toLowerCase();
  if (l === 'depression') return 'var(--depression)';
  if (l === 'anxiety')    return 'var(--anxiety)';
  return 'var(--normal)';
}

/** Returns a coloured badge HTML string for a prediction label */
function badgeHTML(label) {
  if (!label) return '';
  const l = label.toLowerCase();
  const cls = l === 'depression' ? 'badge-depression'
             : l === 'anxiety'   ? 'badge-anxiety'
             : 'badge-normal';
  return `<span class="badge ${cls}">${label}</span>`;
}

/** Formats an ISO datetime string to readable UK format */
function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit',
  });
}

/** Escapes HTML special characters to prevent XSS */
function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Escapes backtick template literal characters */
function escapeJS(str) {
  return String(str)
    .replace(/\\/g, '\\\\')
    .replace(/`/g, '\\`')
    .replace(/\$/g, '\\$');
}