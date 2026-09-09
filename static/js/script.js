const pwInput = document.getElementById('pw');
const toggleBtn = document.getElementById('toggleBtn');
const verdictEl = document.getElementById('verdict');
const entropyEl = document.getElementById('entropy');
const seg1 = document.getElementById('seg1');
const seg2 = document.getElementById('seg2');
const seg3 = document.getElementById('seg3');
const checklistEl = document.getElementById('checklist');
const feedbackEl = document.getElementById('feedback');
const leakedFlag = document.getElementById('leakedFlag');
const statusPing = document.getElementById('statusPing');

let debounceTimer = null;
let inFlightController = null;

toggleBtn.addEventListener('click', () => {
  const isPw = pwInput.type === 'password';
  pwInput.type = isPw ? 'text' : 'password';
  toggleBtn.textContent = isPw ? 'HIDE' : 'SHOW';
});

function renderIdle() {
  [seg1, seg2, seg3].forEach(s => s.className = 'seg');
  verdictEl.className = 'verdict idle';
  verdictEl.textContent = 'AWAITING INPUT';
  entropyEl.textContent = '0.0 bits est.';
  leakedFlag.classList.remove('show');
  checklistEl.querySelectorAll('.check-item').forEach(item => {
    item.classList.remove('pass');
    item.querySelector('.bracket').textContent = '[ ]';
  });
  feedbackEl.className = 'feedback empty';
  feedbackEl.textContent = '// analysis output will appear here';
  statusPing.textContent = '● idle';
}

function renderResult(r) {
  const verdictLower = r.verdict.toLowerCase();

  [seg1, seg2, seg3].forEach(s => s.className = 'seg');
  if (verdictLower === 'weak') {
    seg1.classList.add('on-weak');
  } else if (verdictLower === 'medium') {
    seg1.classList.add('on-medium'); seg2.classList.add('on-medium');
  } else if (verdictLower === 'strong') {
    seg1.classList.add('on-strong'); seg2.classList.add('on-strong'); seg3.classList.add('on-strong');
  }

  verdictEl.className = 'verdict ' + verdictLower;
  verdictEl.textContent = r.verdict.toUpperCase();
  entropyEl.textContent = `${r.entropy.toFixed(1)} bits est.`;

  leakedFlag.classList.toggle('show', !!r.leaked);

  checklistEl.querySelectorAll('.check-item').forEach(item => {
    const key = item.dataset.key;
    const passed = !!(r.checks && r.checks[key]);
    item.classList.toggle('pass', passed);
    item.querySelector('.bracket').textContent = passed ? '[x]' : '[ ]';
  });

  feedbackEl.className = 'feedback';
  feedbackEl.innerHTML = '<ul>' + r.reasons.map(x => `<li>${x}</li>`).join('') + '</ul>';

  statusPing.textContent = '● analyzed';
}

async function checkPassword(password) {
  if (inFlightController) inFlightController.abort();
  inFlightController = new AbortController();

  try {
    statusPing.textContent = '● scanning…';
    const res = await fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
      signal: inFlightController.signal
    });
    if (!res.ok) throw new Error('Request failed');
    const data = await res.json();
    renderResult(data);
  } catch (err) {
    if (err.name !== 'AbortError') {
      statusPing.textContent = '● backend unreachable';
    }
  }
}

pwInput.addEventListener('input', (e) => {
  const value = e.target.value;

  if (value.length === 0) {
    renderIdle();
    return;
  }

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => checkPassword(value), 150);
});

renderIdle();
