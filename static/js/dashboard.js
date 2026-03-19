/**
 * dashboard.js
 * Loads and renders the dashboard page:
 * - Summary stat cards (posts, predictions, depression, normal counts)
 * - Donut chart showing label distribution
 * - Recent predictions list
 */

async function loadDashboard() {
  try {
    const [posts, preds] = await Promise.all([
      api('GET', '/posts/'),
      api('GET', '/predictions/?limit=100'),
    ]);

    // ── STAT CARDS ──
    document.getElementById('stat-posts').textContent = posts.length;
    document.getElementById('stat-preds').textContent = preds.length;

    const counts = { Depression: 0, Anxiety: 0, Normal: 0 };
    preds.forEach(p => {
      if (counts[p.label] !== undefined) counts[p.label]++;
      else counts['Normal']++;
    });

    document.getElementById('stat-dep').textContent  = counts.Depression;
    document.getElementById('stat-anx').textContent  = counts.Anxiety;
    document.getElementById('stat-norm').textContent = counts.Normal;

    // ── CHART + RECENT ──
    drawDonut(counts);
    renderRecent(preds.slice(0, 5));

  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── DONUT CHART (canvas) ──

function drawDonut(counts) {
  const canvas = document.getElementById('donut-chart');
  const ctx    = canvas.getContext('2d');
  const total  = Object.values(counts).reduce((a, b) => a + b, 0) || 1;

  const colors = {
    Depression: '#f76a8a',
    Anxiety:    '#f7c06a',
    Normal:     '#6af7c8',
  };

  let startAngle = -Math.PI / 2;
  ctx.clearRect(0, 0, 130, 130);

  Object.entries(counts).forEach(([label, val]) => {
    const slice = (val / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(65, 65);
    ctx.arc(65, 65, 55, startAngle, startAngle + slice);
    ctx.closePath();
    ctx.fillStyle = colors[label];
    ctx.fill();
    startAngle += slice;
  });

  // Donut hole
  ctx.beginPath();
  ctx.arc(65, 65, 32, 0, 2 * Math.PI);
  ctx.fillStyle = '#ffffff'; // matches --surface (light theme)
  ctx.fill();

  // Legend
  const legend = document.getElementById('donut-legend');
  legend.innerHTML = Object.entries(counts).map(([label, val]) => `
    <div class="legend-item">
      <div class="legend-dot" style="background:${colors[label]}"></div>
      <span style="color:var(--muted)">${label}</span>
      <span style="margin-left:auto">
        ${val}
        <span style="color:var(--muted)">(${Math.round((val / total) * 100)}%)</span>
      </span>
    </div>`).join('');
}

// ── RECENT PREDICTIONS LIST ──

function renderRecent(preds) {
  const el = document.getElementById('recent-list');

  if (!preds.length) {
    el.innerHTML = `
      <div class="empty">
        <div class="empty-icon">◈</div>
        <p>No predictions yet</p>
      </div>`;
    return;
  }

  el.innerHTML = preds.map(p => `
    <div class="history-item">
      <div class="history-dot" style="background:${labelColor(p.label)}"></div>
      <div style="flex:1;min-width:0">
        <div style="font-size:12px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
          ${escapeHTML(p.text_snapshot)}
        </div>
        <div style="font-size:10px;color:var(--muted);margin-top:2px">${formatDate(p.created_at)}</div>
      </div>
      <div>${badgeHTML(p.label)}</div>
    </div>`).join('');
}