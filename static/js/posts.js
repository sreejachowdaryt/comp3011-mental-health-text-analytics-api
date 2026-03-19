/**
 * posts.js
 * Handles all Posts page functionality:
 * - Load and render posts list
 * - Create post (modal)
 * - Edit post (modal)
 * - Delete post
 * - Inline latest prediction display
 * - Prediction history modal
 * - Quick Predict page (/predict endpoint)
 */

// ── LOAD POSTS ──

async function loadPosts() {
  const el = document.getElementById('posts-list');
  el.innerHTML = `
    <div class="empty">
      <div class="empty-icon">◌</div>
      <p>Loading...</p>
    </div>`;

  try {
    const posts = await api('GET', '/posts/');

    if (!posts.length) {
      el.innerHTML = `
        <div class="empty">
          <div class="empty-icon">◻</div>
          <p>No posts yet — create one!</p>
        </div>`;
      return;
    }

    // Newest first
    el.innerHTML = [...posts].reverse().map(p => `
      <div class="post-card">
        <div class="post-meta">
          <span class="post-id">#${p.id}</span>
          <span class="post-source">${escapeHTML(p.source)}</span>
          <span class="post-date">${formatDate(p.created_at)}</span>
        </div>
        <div class="post-text">${escapeHTML(p.text)}</div>
        <div class="post-actions">
          <button class="btn btn-ghost" style="padding:6px 14px;font-size:12px"
            onclick="loadLatestPred(${p.id}, this)">◈ Latest Prediction</button>
          <button class="btn btn-ghost" style="padding:6px 14px;font-size:12px"
            onclick="openHistory(${p.id})">⊞ History</button>
          <button class="btn btn-ghost" style="padding:6px 14px;font-size:12px"
            onclick="openEdit(${p.id}, \`${escapeJS(p.text)}\`, '${escapeHTML(p.source)}')">✎ Edit</button>
          <button class="btn btn-danger" style="padding:6px 14px;font-size:12px"
            onclick="deletePost(${p.id})">✕ Delete</button>
        </div>
        <div id="inline-pred-${p.id}" style="margin-top:10px"></div>
      </div>`).join('');

  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── INLINE LATEST PREDICTION ──

async function loadLatestPred(postId, btn) {
  btn.disabled = true;
  try {
    const pred = await api('GET', `/posts/${postId}/prediction/latest`);
    const pct  = pred.confidence ? Math.round(pred.confidence * 100) : 0;
    const el   = document.getElementById(`inline-pred-${postId}`);

    el.innerHTML = `
      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
          ${badgeHTML(pred.label)}
          <span style="font-size:11px;color:var(--muted)">Confidence: ${pct}%</span>
          <span style="font-size:11px;color:var(--muted);margin-left:auto">${pred.model_version}</span>
        </div>
        <div class="conf-bar-bg">
          <div class="conf-bar-fill fill-${pred.label.toLowerCase()}" style="width:${pct}%"></div>
        </div>
      </div>`;
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ── CREATE POST MODAL ──

function openCreateModal() {
  document.getElementById('new-post-text').value   = '';
  document.getElementById('new-post-source').value = 'manual';
  document.getElementById('create-modal').classList.add('show');
}

async function submitPost() {
  const text   = document.getElementById('new-post-text').value.trim();
  const source = document.getElementById('new-post-source').value;

  if (!text) { toast('Text is required', 'error'); return; }

  try {
    await api('POST', '/posts/', { text, source });
    closeModal('create-modal');
    loadPosts();
    toast('Post created + prediction generated', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── EDIT POST MODAL ──

function openEdit(id, text, source) {
  document.getElementById('edit-post-id').value     = id;
  document.getElementById('edit-post-text').value   = text;
  document.getElementById('edit-post-source').value = source;
  document.getElementById('edit-modal').classList.add('show');
}

async function submitEdit() {
  const id     = document.getElementById('edit-post-id').value;
  const text   = document.getElementById('edit-post-text').value.trim();
  const source = document.getElementById('edit-post-source').value;

  try {
    await api('PUT', `/posts/${id}`, { text, source });
    closeModal('edit-modal');
    loadPosts();
    toast('Post updated', 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── DELETE POST ──

async function deletePost(id) {
  if (!confirm(`Delete post #${id}? This will also remove all its predictions.`)) return;

  try {
    await api('DELETE', `/posts/${id}`);
    loadPosts();
    toast(`Post #${id} deleted`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── PREDICTION HISTORY MODAL ──

async function openHistory(postId) {
  document.getElementById('history-post-id').textContent = postId;
  document.getElementById('history-list').innerHTML =
    '<div style="color:var(--muted);font-size:13px">Loading...</div>';
  document.getElementById('history-modal').classList.add('show');

  try {
    const history = await api('GET', `/posts/${postId}/prediction/history`);

    document.getElementById('history-list').innerHTML = history.map(p => `
      <div class="history-item">
        <div class="history-dot" style="background:${labelColor(p.label)}"></div>
        <div style="flex:1;min-width:0">
          <div style="font-size:12px;color:var(--text);margin-bottom:4px">
            ${escapeHTML(p.text_snapshot)}
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            ${badgeHTML(p.label)}
            <span style="font-size:10px;color:var(--muted)">
              ${p.confidence ? Math.round(p.confidence * 100) + '% confidence' : ''}
            </span>
            <span style="font-size:10px;color:var(--muted);margin-left:auto">
              ${formatDate(p.created_at)}
            </span>
          </div>
        </div>
      </div>`).join('');

  } catch (e) {
    document.getElementById('history-list').innerHTML =
      `<div class="error-msg">${escapeHTML(e.message)}</div>`;
  }
}

// ── QUICK PREDICT ──

async function doPredict() {
  const text = document.getElementById('predict-text').value.trim();
  if (!text) { toast('Enter some text first', 'error'); return; }

  const btn = document.getElementById('predict-btn');
  btn.disabled  = true;
  btn.innerHTML = '<span class="spinner"></span>Analysing...';

  try {
    const res = await api('POST', '/predict', { text });
    showPredictResult(res);
    toast('Prediction complete', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled  = false;
    btn.innerHTML = '⚡ Run Prediction';
  }
}

function showPredictResult(res) {
  const pct = res.confidence ? Math.round(res.confidence * 100) : 0;

  document.getElementById('result-label').textContent = res.label;
  document.getElementById('result-label').style.color = labelColor(res.label);
  document.getElementById('result-badge').innerHTML   = badgeHTML(res.label);
  document.getElementById('result-conf-pct').textContent = `${pct}%`;
  document.getElementById('result-model').textContent    = res.model_version;
  document.getElementById('result-postid').textContent   = res.post_id;

  const bar = document.getElementById('result-bar');
  bar.style.width = `${pct}%`;
  bar.className   = `conf-bar-fill fill-${res.label.toLowerCase()}`;

  const unc = document.getElementById('result-uncertain');
  unc.style.display = res.uncertain ? 'block' : 'none';

  document.getElementById('predict-result').classList.add('show');
}

function resetPredictForm() {
  document.getElementById('predict-text').value = '';
  document.getElementById('predict-result').classList.remove('show');
  document.getElementById('predict-text').focus();
}