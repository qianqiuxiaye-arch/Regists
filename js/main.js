// Global Data Store (loaded from data/data.js)
// GOGLOBAL_DATA is defined in data/data.js

// Utility
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const escapeHtml = str => { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const page = detectPage();
  if (page === 'glossary') renderGlossaryPage();
  else if (page === 'updates') renderUpdatesPage();
  else if (page === 'region') renderRegionPage(detectRegion());
  else renderHomePage();
});

function detectPage() {
  const path = window.location.pathname;
  const file = path.split('/').pop() || 'index.html';
  if (file.includes('glossary')) return 'glossary';
  if (file.includes('updates')) return 'updates';
  for (const id of ['hong-kong', 'singapore', 'us', 'uk', 'dubai']) {
    if (file.includes(id)) return 'region';
  }
  return 'home';
}

function detectRegion() {
  const path = window.location.pathname;
  const file = path.split('/').pop() || 'index.html';
  for (const id of ['hong-kong', 'singapore', 'us', 'uk', 'dubai']) {
    if (file.includes(id)) return id;
  }
  return null;
}

// ========== HOME PAGE ==========
function renderHomePage() {
  const app = document.getElementById('app');
  if (!app) return;

  const regions = GOGLOBAL_DATA.regions.regions || [];

  const cardsHtml = regions.map(r =>
    `<div class="region-card" style="--card-color:${r.color}">
      <div class="region-card-top">
        <span class="region-flag">${r.flag}</span>
        <div class="region-card-title-group">
          <span class="region-name">${r.name}</span>
          <span class="region-name-en">${r.nameEn}</span>
        </div>
      </div>
      <div class="region-card-body">
        <p>${r.summary}</p>
        <div class="region-card-meta">
          <span>📅 ${r.lastUpdated} 更新</span>
          <span>🏛️ ${r.officialSources.length} 个官方来源</span>
        </div>
        <a href="./${r.id}.html" class="region-card-link">
          <span>查看指南</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </a>
      </div>
    </div>`
  ).join('');

  // Overview comparison rows
  const overviewRows = regions.map(r => {
    const advantages = (r.advantages || []).map(a => `<li>${a}</li>`).join('');
    const bd = r.bankDifficulty || {};
    const diffHtml = bd.icon ? `<span style="font-size:18px">${bd.icon}</span> <strong>${bd.level}</strong><br><span style="font-size:11px;color:var(--text-muted)">${bd.detail || ''}</span>` : '-';
    return `<tr>
      <td><strong>${r.flag} ${r.name}</strong><br><span style="font-size:12px;color:var(--text-muted)">${r.nameEn}</span></td>
      <td>${r.businessSuggestion || '-'}</td>
      <td><ul class="overview-adv-list">${advantages}</ul></td>
      <td>${diffHtml}</td>
      <td><a href="./${r.id}.html" class="overview-link">查看详情 →</a></td>
    </tr>`;
  }).join('');

  app.innerHTML = `
    <section class="hero">
      <div class="hero-bg-pattern"></div>
      <div class="hero-content">
        <div class="hero-badge">🏛️ 信息 100% 源自各国政府官方网站</div>
        <h1>中国出海企业<span class="hero-highlight">全球开办公司</span>指南</h1>
        <p>从公司注册到企业银行开户，一站式的权威信息平台。</p>
      </div>
    </section>
    <div class="container">

      <!-- Overview Table -->
      <section style="padding:40px 0 16px">
        <h2 style="font-size:22px;font-weight:700;margin-bottom:4px">🌏 全球注册地总览</h2>
        <p style="color:var(--text-secondary);font-size:14px;margin-bottom:24px">主流出海注册地的对比分析，快速找到适合你的目的地。</p>
        <div class="overview-table-wrap">
          <table class="overview-table">
            <thead>
              <tr>
                <th style="width:15%">国家/地区</th>
                <th style="width:25%">业务建议</th>
                <th style="width:33%">核心优势</th>
                <th style="width:15%">🏦 开户难度</th>
                <th style="width:12%">指南</th>
              </tr>
            </thead>
            <tbody>${overviewRows}</tbody>
          </table>
        </div>
      </section>

      <!-- Cards -->
      <section style="padding:32px 0 16px">
        <h2 style="font-size:18px;font-weight:600;margin-bottom:20px">详细指南</h2>
        <div class="region-grid">${cardsHtml}</div>
      </section>
    </div>`;
}

// ========== REGION PAGE ==========
function renderRegionPage(regionId) {
  const app = document.getElementById('app');
  if (!app) return;

  const region = GOGLOBAL_DATA.regions.regions?.find(r => r.id === regionId);
  if (!region) {
    app.innerHTML = '<div class="container" style="padding:60px 20px"><h1>地区未找到</h1><a href="./index.html">返回首页</a></div>';
    return;
  }

  const data = GOGLOBAL_DATA.regionData[regionId];
  if (!data) {
    app.innerHTML = '<div class="container" style="padding:60px 20px"><h1>数据加载失败</h1><p>请检查 data.js 文件。</p></div>';
    return;
  }

  const pages = data.pages || [];

  // Sidebar nav
  const navItems = pages.map((p, i) =>
    `<li class="sidebar-nav-item"><a class="sidebar-nav-link ${i === 0 ? 'active' : ''}" data-panel="${p.id}" href="#${p.id}">
      <span class="nav-icon">${p.icon}</span> ${p.title}
    </a></li>`
  ).join('');

  // Source badges
  const sourceBadges = region.officialSources.map(s =>
    `<a href="${s.url}" target="_blank" rel="noopener noreferrer"><span class="source-badge official">🏛️ ${s.name}</span></a>`
  ).join('');

  app.innerHTML = `
    <div class="container">
      <div class="region-page-header">
        <a href="./index.html" class="back-link">← 返回首页</a>
        <h1><span style="font-size:28px">${region.flag}</span> ${region.name} - 开办公司全指南</h1>
        <div class="region-subtitle">${region.summary}</div>
        <div class="source-list">${sourceBadges}</div>
        <div class="update-info" style="margin-top:12px">
          ✅ 所有信息均来自官方政府机构，最后验证日期：<strong>${region.lastUpdated}</strong>
        </div>
      </div>

      <div class="region-layout">
        <nav class="sidebar-nav">
          <ul class="sidebar-nav-list">${navItems}</ul>
        </nav>
        <div class="content-area" id="content-area">
          ${pages.map((p, i) => `<div class="panel-content ${i === 0 ? 'active' : ''}" id="panel-${p.id}"></div>`).join('')}
        </div>
      </div>
    </div>
  `;

  // Sidebar click handler
  $$('.sidebar-nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const panelId = link.dataset.panel;
      $$('.sidebar-nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      $$('.panel-content').forEach(p => p.classList.remove('active'));
      const panel = document.getElementById(`panel-${panelId}`);
      if (panel) panel.classList.add('active');
      window.history.replaceState(null, '', `#${panelId}`);
    });
  });

  // Render each page panel
  pages.forEach(p => renderPanel(p, document.getElementById(`panel-${p.id}`)));

  // Hash routing
  if (window.location.hash) {
    const target = window.location.hash.slice(1);
    const link = $(`.sidebar-nav-link[data-panel="${target}"]`);
    if (link) link.click();
  }
}

function renderPanel(page, container) {
  if (!container) return;

  const sectionsHtml = page.sections.map(s => {
    const contentHtml = s.content.map(c => renderContentBlock(c)).join('');
    const sourcesHtml = s.sources.map(src =>
      `<a href="${src.url}" target="_blank" rel="noopener noreferrer" class="source-link">📖 ${src.name}${src.type === 'official' ? ' (官方)' : ''}</a>`
    ).join(' | ');

    return `
      <div class="sub-section">
        <div class="verification-banner">
          ✅ 信息已验证 — 来源: ${s.sources.map(s => s.name).join(', ')}
          <span style="margin-left:auto;font-size:12px">验证日期: ${s.lastVerified}</span>
        </div>
        ${s.title ? `<div class="sub-section-title">${s.title}</div>` : ''}
        ${contentHtml}
        <div style="margin-top:8px">${sourcesHtml}</div>
      </div>
    `;
  }).join('');

  container.innerHTML = sectionsHtml;
}

function renderContentBlock(block) {
  switch (block.type) {
    case 'table':
      return renderTable(block);
    case 'list':
      return `<ul class="info-list">${block.items.map(i => `<li>${i}</li>`).join('')}</ul>`;
    case 'steps':
      return renderSteps(block);
    case 'note':
      return `<div class="note-block">💡 ${block.text}</div>`;
    default:
      return '';
  }
}

function renderTable(block) {
  const headerRow = block.headers.map(h => `<th>${h}</th>`).join('');
  const bodyRows = block.rows.map(row =>
    `<tr>${row.map(c => `<td>${c}</td>`).join('')}</tr>`
  ).join('');
  return `<table class="data-table"><thead><tr>${headerRow}</tr></thead><tbody>${bodyRows}</tbody></table>`;
}

function renderSteps(block) {
  const items = block.steps.map(s => {
    const meta = [];
    if (s.duration) meta.push(`⏱ ${s.duration}`);
    if (s.fee) meta.push(`💰 ${s.fee}`);
    const metaHtml = meta.length ? `<div class="step-meta">${meta.map(m => `<span>${m}</span>`).join('')}</div>` : '';
    return `
      <div class="step-item">
        <div class="step-number">${s.step}</div>
        <div class="step-content">
          <div class="step-title">${s.title}</div>
          <div class="step-desc">${s.desc}</div>
          ${metaHtml}
        </div>
      </div>
    `;
  }).join('');
  return `<div class="steps-list">${items}</div>`;
}

// ========== GLOSSARY PAGE ==========
function renderGlossaryPage() {
  const app = document.getElementById('app-glossary');
  if (!app) return;

  const items = GOGLOBAL_DATA.glossary.glossary || [];
  const categories = [...new Set(items.map(i => i.category))];

  let html = `
    <div class="container" style="padding:36px 0 80px">
      <h1 style="font-size:28px;font-weight:700;margin-bottom:4px">📖 常用名词解释</h1>
      <p style="color:var(--text-secondary);font-size:15px;margin-bottom:28px">出海公司注册相关的专有名词，按类别分类。覆盖香港、新加坡、美国三地。</p>
      <div class="glossary-cats">`;

  for (const cat of categories) {
    const catItems = items.filter(i => i.category === cat);
    html += `
      <div class="page-section">
        <div class="page-section-header" onclick="this.classList.toggle('collapsed');this.nextElementSibling.classList.toggle('collapsed')">
          <h3>${cat}</h3>
          <span class="toggle-icon" style="font-size:14px;color:var(--text-muted)">▼</span>
        </div>
        <div class="page-section-body">`;

    for (const item of catItems) {
      const regionBadges = (item.regions || []).map(r => {
        const names = {'hong-kong':'🇭🇰 香港','singapore':'🇸🇬 新加坡','us':'🇺🇸 美国'};
        return `<span class="glossary-region">${names[r] || r}</span>`;
      }).join('');

      const relatedHtml = (item.relatedTerms || []).map(t =>
        `<span class="glossary-related-tag">${t}</span>`
      ).join('');

      html += `
        <div class="glossary-item">
          <div class="glossary-term-row">
            <span class="glossary-term">${item.term}</span>
            ${item.full ? `<span class="glossary-full">${item.full}</span>` : ''}
            <div class="glossary-badges">${regionBadges}</div>
          </div>
          <p class="glossary-def">${item.definition}</p>
          ${relatedHtml ? `<div style="margin-top:8px"><span style="font-size:12px;color:var(--text-muted)">关联: </span>${relatedHtml}</div>` : ''}
        </div>`;
    }

    html += `</div></div>`;
  }

  html += `</div></div>`;
  app.innerHTML = html;
}

// ========== UPDATES PAGE ==========
function renderUpdatesPage() {
  const app = document.getElementById('app-updates');
  if (!app) return;

  const WP_API = 'https://public-api.wordpress.com/rest/v1.1/sites/registscom.wordpress.com';

  function renderPosts(posts) {
    let html = `
      <div class="container" style="padding:36px 0 80px">
        <h1 style="font-size:28px;font-weight:700;margin-bottom:4px">📰 最新动态</h1>
        <p style="color:var(--text-secondary);font-size:15px;margin-bottom:28px">出海公司注册相关政策动态、合规更新和行业资讯。</p>
        <div class="updates-list">`;

    for (const item of posts) {
      const tagHtml = (item.tags || []).map(t => `<span class="glossary-related-tag">${t}</span>`).join('');
      const link = item.link || (item.sourceUrl ? item.sourceUrl : null);
      html += `
        <div class="update-card">
          <div class="update-card-top">
            <span class="update-category">${escapeHtml(item.category)}</span>
            <span class="update-date">${item.date}</span>
          </div>
          <h3 class="update-title">${escapeHtml(item.title)}</h3>
          <p class="update-summary">${escapeHtml(item.summary)}</p>
          <div style="display:flex;align-items:center;gap:8px">
            <div>${tagHtml}</div>
            ${link ? `<a href="${link}" target="_blank" rel="noopener noreferrer" class="update-source-link">查看详情 →</a>` : ''}
          </div>
        </div>`;
    }

    html += `</div></div>`;
    app.innerHTML = html;
  }

  // Load from WordPress.com API
  fetch(`${WP_API}/posts?number=20`)
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(data => {
      const mapped = (data.posts || []).map(p => ({
        title: p.title, date: p.date.slice(0, 10),
        category: Object.values(p.categories || {})[0]?.name || '动态',
        summary: p.excerpt.replace(/<[^>]+>/g, '').trim().slice(0, 200),
        tags: (p.tags || []).map(t => t.name), link: p.URL
      }));
      renderPosts(mapped);
    })
    .catch(() => {
      const items = (GOGLOBAL_DATA.updates.updates || []).map(u => ({
        ...u, tags: u.tags || [], link: u.sourceUrl
      }));
      renderPosts(items);
    });
}
