document.querySelector('#app').innerHTML = layout('medications', 'Medicamentos', 'Organize horários, dosagens e estoque.');
let editing = null;
let items = [];
const medicationForm = document.querySelector('#form');
const medicationModal = document.querySelector('#modal');
const fields = Object.fromEntries(['name','dosage','times','frequency','quantity','start_date','end_date','notes'].map(id => [id, document.querySelector(`#${id}`)]));
const localDateValue = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60 * 1000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
};
fields.start_date.value = localDateValue();

async function load() {
  try {
    items = await API.request('/medications');
    document.querySelector('#page').innerHTML = `<div class="section-title page-tools"><div><b>${items.length} medicamento${items.length === 1 ? '' : 's'} cadastrado${items.length === 1 ? '' : 's'}</b></div><button class="btn" onclick="openModal()">＋ Novo medicamento</button></div><div class="grid">${items.map(m => `<div class="card med-card"><div class="med-icon">💊</div><div class="grow"><h3>${m.name}</h3><div class="muted">${m.dosage} · ${m.times.join(' e ')} · ${m.frequency}</div><small>${m.quantity} unidades disponíveis${m.notes ? ` · ${m.notes}` : ''}</small></div><button class="btn ghost" onclick="editMedication(${m.id})">Editar</button><button class="btn danger" onclick="removeMed(${m.id})">Excluir</button></div>`).join('') || '<div class="card empty">Nenhum medicamento cadastrado. Comece pelo botão acima.</div>'}</div>`;
  } catch (error) { toast(error.message); }
}

function openModal() { medicationModal.classList.add('open'); fields.name.focus(); }
function closeModal() {
  medicationModal.classList.remove('open'); medicationForm.reset();
  fields.start_date.value = localDateValue();
  fields.frequency.value = 'Todos os dias'; fields.quantity.value = 0; editing = null;
}
function editMedication(id) {
  const medication = items.find(item => item.id === id); editing = id;
  for (const key of ['name','dosage','frequency','quantity','start_date','end_date','notes']) fields[key].value = medication[key] || '';
  fields.times.value = medication.times.join(', '); openModal();
}
medicationForm.onsubmit = async event => {
  event.preventDefault();
  const body = {name:fields.name.value, dosage:fields.dosage.value, times:fields.times.value.split(',').map(x => x.trim()).filter(Boolean), frequency:fields.frequency.value, start_date:fields.start_date.value, end_date:fields.end_date.value || null, quantity:Number(fields.quantity.value), notes:fields.notes.value, active:true};
  try {
    await API.request(`/medications${editing ? `/${editing}` : ''}`, {method:editing ? 'PUT' : 'POST', body:JSON.stringify(body)});
    closeModal(); toast('Medicamento salvo'); load();
  } catch (error) { toast(error.message); }
};
async function removeMed(id) {
  if (!confirm('Excluir este medicamento e suas doses?')) return;
  try { await API.request(`/medications/${id}`, {method:'DELETE'}); toast('Medicamento excluído'); load(); }
  catch (error) { toast(error.message); }
}
load();
