document.querySelector('#app').innerHTML = layout('dashboard', 'Olá!', 'Aqui está o ritmo da sua rotina hoje.');

async function load() {
  try {
    const [me, doses, adherence, insights, meds, caregivers] = await Promise.all([
      API.request('/me'), API.request('/doses'), API.request('/adherence?days=30'),
      API.request('/insights'), API.request('/medications'), API.request('/caregiver')
    ]);
    document.querySelector('.topbar h1').textContent = `Olá, ${me.name.split(' ')[0]}!`;
    const pending = doses.filter(item => ['PENDING','LATE'].includes(item.status));
    const next = pending[0];
    const bars = adherence.evolution.slice(-10).map(item => `<div class="bar" style="height:${Math.max(8,item.percentage)}%" title="${item.date}: ${item.percentage}%"></div>`).join('') || '<div class="muted">Registre doses para ver a evolução.</div>';
    const doseRows = doses.map(dose => `<div class="dose"><div class="time">${new Date(dose.scheduled_at).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</div><div class="dose-info"><b>${dose.medication}</b><small>${dose.dosage}</small></div><span class="badge ${dose.status}">${statusNames[dose.status]}</span>${['PENDING','LATE'].includes(dose.status) ? `<button class="btn secondary" onclick="mark(${dose.id},'taken')">Tomei</button>` : ''}</div>`).join('') || '<div class="empty">Nenhuma dose programada hoje.</div>';
    document.querySelector('#page').innerHTML = `
      ${meds.length === 0 ? `<div class="card onboarding"><div><b>Conta pronta para começar.</b><p>Cadastre seu primeiro medicamento ou carregue uma rotina fictícia para conhecer o sistema.</p></div><div class="actions"><a class="btn" href="/medications.html">Cadastrar medicamento</a><button class="btn secondary" onclick="demo()">Usar demonstração</button></div></div>` : ''}
      <section class="grid stats">
        <div class="card stat"><strong>${doses.length}</strong><span>Doses hoje</span></div>
        <div class="card stat"><strong>${doses.filter(x => x.status === 'TAKEN').length}</strong><span>Tomadas</span></div>
        <div class="card stat"><strong>${pending.length}</strong><span>Pendentes</span></div>
        <div class="card stat"><strong>${adherence.percentage}%</strong><span>Adesão em 30 dias</span></div>
      </section>
      <section class="grid dashboard-grid">
        <div>
          <div class="card next"><div class="eyebrow">Próxima dose</div>${next ? `<div class="dose-time">${new Date(next.scheduled_at).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</div><div class="dose-name">${next.medication} — ${next.dosage}</div><div class="actions"><button class="btn" onclick="mark(${next.id},'taken')">✓ Tomei</button><button class="btn secondary" onclick="snooze(${next.id})">Adiar 10 min</button></div>` : '<div class="all-clear">Tudo certo por enquanto ✓</div>'}</div>
          <div class="card space-top"><div class="section-title"><h2>Medicamentos de hoje</h2><span class="muted">${doses.length} doses</span></div><div class="dose-list">${doseRows}</div></div>
        </div>
        <div>
          <a class="card support-card" href="/caregiver.html"><div class="support-icon">♡</div><div><div class="eyebrow">Modo cuidador</div><h2>${caregivers.length ? `${caregivers.length} contato${caregivers.length === 1 ? '' : 's'} autorizado${caregivers.length === 1 ? '' : 's'}` : 'Configure sua rede de apoio'}</h2><p>${caregivers.length ? 'Gerencie permissões e alertas do cuidador.' : 'Autorize alguém de confiança a receber alertas de doses atrasadas.'}</p><b>Abrir modo cuidador →</b></div></a>
          <div class="card space-top"><div class="section-title"><h2>Evolução da adesão</h2><b>${adherence.percentage}%</b></div><div class="chart">${bars}</div><div class="notice">${adherence.disclaimer}</div></div>
          <div class="card space-top"><div class="section-title"><h2>Insights da rotina</h2><span>✦</span></div>${insights.insights.map(text => `<div class="insight">${text}</div>`).join('')}<div class="notice">Análise dos seus registros, sem recomendações médicas.</div></div>
        </div>
      </section>`;
  } catch (error) { toast(error.message); }
}

async function mark(id, status) { try { await API.request(`/doses/${id}/${status}`, {method:'POST'}); toast('Dose registrada'); load(); } catch (error) { toast(error.message); } }
async function snooze(id) { try { await API.request(`/doses/${id}/snooze`, {method:'POST',body:'{"minutes":10}'}); toast('Lembrete adiado por 10 minutos'); load(); } catch (error) { toast(error.message); } }
async function demo() { try { await API.request('/demo', {method:'POST'}); toast('Dados fictícios carregados'); load(); } catch (error) { toast(error.message); } }
load();

