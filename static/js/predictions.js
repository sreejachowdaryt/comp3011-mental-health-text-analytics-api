/**
 * predictions.js
 * Loads and renders the Predictions page.
 * Shows all latest predictions across all posts with
 * confidence bars, labels, text snapshots and timestamps.
 */

async function loadPredictions() {
  const el = document.getElementById('predictions-list');
  el.innerHTML = `
    <div class="empty">
      <div class="empty-icon">◌</div>
      <p>Loading...</p>
    </div>`;

  try {
    const preds = await api('GET', '/predictions/?limit=100');

    if (!preds.length) {
      el.innerHTML = `
        <div class="empty">
          <div class="empty-icon">◈</div>
          <p>No predictions yet — create a post to generate one</p>
        </div>`;
      return;
    }

    el.innerHTML = preds.map(p => {
      const pct = p.confidence ? Math.round(p.confidence * 100) : 0;
      return `
        <div class="card" style="cursor:default">
          <div style="display:flex;align-items:flex-start;gap:16px">
            <div style="flex:1;min-width:0">
              <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
                ${badgeHTML(p.label)}
                <span style="font-size:11px;color:var(--muted)">Post #${p.post_id}</span>
                <span style="font-size:11px;color:var(--muted)">${escapeHTML(p.model_version)}</span>
                <span style="font-size:11px;color:var(--muted);margin-left:auto">
                  ${formatDate(p.created_at)}
                </span>
              </div>
              <div style="font-size:13px;color:var(--text);margin-bottom:10px;line-height:1.5">
                ${escapeHTML(p.text_snapshot)}
              </div>
              <div class="conf-bar-wrap">
                <div class="conf-bar-label">
                  <span>Confidence</span>
                  <span>${pct}%</span>
                </div>
                <div class="conf-bar-bg">
                  <div class="conf-bar-fill fill-${p.label.toLowerCase()}" style="width:${pct}%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>`;
    }).join('');

  } catch (e) {
    toast(e.message, 'error');
  }
}