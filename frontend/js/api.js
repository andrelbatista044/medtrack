function apiErrorMessage(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const labels = {name:'nome', email:'e-mail', password:'senha', times:'horários', start_date:'data de início'};
    return detail.map(item => {
      const field = Array.isArray(item.loc) ? item.loc.filter(x => x !== 'body').join(' → ') : '';
      const label = labels[field] || field;
      return `${label ? `${label}: ` : ''}${item.msg || 'valor inválido'}`;
    }).join(' ');
  }
  if (detail && typeof detail === 'object') return detail.message || detail.msg || 'Os dados informados são inválidos.';
  return 'Não foi possível concluir a ação.';
}

const API = {
  token: localStorage.getItem('medtrack_token'),
  async request(path, options = {}) {
    const headers = {'Content-Type':'application/json', ...(options.headers || {})};
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    const response = await fetch(`/api${path}`, {...options, headers});
    if (response.status === 401 && path !== '/login') {
      localStorage.removeItem('medtrack_token');
      location.href = '/';
    }
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(apiErrorMessage(data.detail));
    }
    return response.status === 204 ? null : response.json();
  },
  setToken(token) {
    this.token = token;
    localStorage.setItem('medtrack_token', token);
  }
};

const statusNames = {PENDING:'Pendente', TAKEN:'Tomada', LATE:'Atrasada', MISSED:'Não registrada', SKIPPED:'Ignorada'};
const navItems = [
  ['dashboard', '⌂', 'Visão geral'],
  ['medications', '✚', 'Medicamentos'],
  ['history', '◷', 'Histórico'],
  ['caregiver', '♡', 'Modo cuidador']
];

function toast(text) {
  const element = document.createElement('div');
  element.className = 'toast';
  element.setAttribute('role', 'status');
  element.textContent = text;
  document.body.append(element);
  setTimeout(() => element.remove(), 2800);
}

function fmtDate(value) {
  return new Date(value).toLocaleString('pt-BR', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
}

function layout(active, title, subtitle = '') {
  const links = navItems.map(([key, icon, label]) =>
    `<a class="${active === key ? 'active' : ''}" href="/${key}.html" ${active === key ? 'aria-current="page"' : ''}><span class="nav-icon">${icon}</span><span>${label}</span></a>`
  ).join('');
  return `<aside class="sidebar">
    <a class="brand" href="/dashboard.html" aria-label="MedTrack — início"><span class="brandmark">✚</span><span>MedTrack</span></a>
    <div class="nav-label">Sua rotina</div><nav class="nav" aria-label="Navegação principal">${links}</nav>
    <a class="caregiver-callout" href="/caregiver.html"><span>♡</span><div><b>Rede de apoio</b><small>Configure o cuidador</small></div><strong>›</strong></a>
    <div class="side-foot">Organização da rotina<br>Não substitui orientação médica.</div>
  </aside>
  <main class="content">
    <header class="topbar"><div><div class="eyebrow">MedTrack</div><h1>${title}</h1><div class="muted">${subtitle}</div></div><div class="top-actions"><a class="btn ghost caregiver-shortcut" href="/caregiver.html">♡ Modo cuidador</a><button class="btn ghost" onclick="logout()">Sair</button></div></header>
    <div id="page"></div>
  </main>
  <nav class="mobile-nav" aria-label="Navegação móvel">${links}</nav>`;
}

function logout() {
  localStorage.removeItem('medtrack_token');
  location.href = '/';
}

if (!API.token && !location.pathname.endsWith('index.html') && location.pathname !== '/') location.href = '/';
