// ---------------- generic modal helper ----------------
function showModal(innerHtml) {
  const root = document.getElementById('modal-root');
  root.innerHTML = `<div class="modal-overlay open" id="active-modal-overlay">
    <div class="modal">${innerHtml}</div>
  </div>`;
  document.getElementById('active-modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'active-modal-overlay') closeModal();
  });
}
function closeModal() {
  const root = document.getElementById('modal-root');
  root.innerHTML = '';
}

// ---------------- placeholder modals (account report page) ----------------
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : str;
  return div.innerHTML;
}

// ---------------- metric info icons (account report: Customer Health & Usage) ----------------
const METRIC_INFO = {
  active_user_ratio: {
    title: 'Active User Ratio',
    body: 'Weekly active users ÷ licensed seats — are people actually logging in and using the platform, not just installed hardware sitting idle. Source: Segment product telemetry.',
  },
  alert_to_workorder_rate: {
    title: 'Alert → Work Order Rate',
    body: 'The % of sensor alerts that get converted into an actual work order within a few days — the best proxy for whether the team is acting on what TRACTIAN surfaces, not just receiving alerts. Source: TRACTIAN CMMS activity, stitched via Segment.',
  },
  days_since_last_login: {
    title: 'Days Since Last Login',
    body: 'How recently anyone at the account logged into the platform. A rising number here is usually the earliest warning sign of an account going unhealthy. Source: Segment product telemetry.',
  },
  plants_live: {
    title: 'Plants Live',
    body: 'How many of the account’s known plants currently have TRACTIAN deployed, out of how many plants they have in total — the site-expansion whitespace (the "land and expand" axis). Source: Salesforce (total plant count) + internal deployment records.',
  },
  sensors: {
    title: 'Sensors',
    body: 'Sensors actively reporting data, out of how many are contracted — the in-site density expansion axis. If deployed exceeds contracted, that’s what fires the Usage Above Contracted Capacity signal. Source: Segment product telemetry + Salesforce contract data.',
  },
  renewal: {
    title: 'Renewal',
    body: 'The account’s current contract renewal date. Source: Salesforce.',
  },
};

function openMetricInfoModal(key) {
  const info = METRIC_INFO[key];
  if (!info) return;
  showModal(`
    <h3>${escapeHtml(info.title)}</h3>
    <p>${info.body}</p>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Close</button>
    </div>
  `);
}
document.querySelectorAll('[data-metric-info]').forEach(function(btn) {
  btn.addEventListener('click', function(e) {
    e.stopPropagation();
    openMetricInfoModal(this.dataset.metricInfo);
  });
});

// ---------------- play explainer modal (plays page) ----------------
function openPlayExplainerModal(playKey) {
  const source = document.getElementById(`play-explainer-${playKey}`);
  if (!source) return;
  showModal(source.innerHTML);
}
document.querySelectorAll('[data-play-explainer]').forEach(function(btn) {
  btn.addEventListener('click', function(e) {
    e.stopPropagation();
    openPlayExplainerModal(this.dataset.playExplainer);
  });
});

function openClayModal(companyName) {
  const company = escapeHtml(companyName || 'this account');
  showModal(`
    <h3>Exported to outreach</h3>
    <p>Every contact on this page was pushed to the outreach sequence. Contacts we only know by
    title get enriched to the person currently in that role at ${company} and added to the same
    sequence.</p>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Close</button>
    </div>
  `);
}

function openSyncModal(syncType, companyName, contactCount) {
  const company = escapeHtml(companyName || 'this account');
  const n = contactCount || 0;
  const plural = n === 1 ? '' : 's';
  let title, body;
  if (syncType === 'meta_audience') {
    title = 'Synced to Meta Custom Audience';
    body = n > 0
      ? `${n} contact${plural} at ${company} synced to the ad audience.`
      : `${company} has no known contacts to match yet — export to outreach first to enrich them.`;
  } else {
    title = 'Enrolled in HubSpot Nurture';
    body = n > 0
      ? `${n} contact${plural} at ${company} enrolled in the nurture sequence for this play.`
      : `${company} has no known contacts to enroll yet — export to outreach first to enrich them.`;
  }
  showModal(`
    <h3>${title}</h3>
    <p>${body}</p>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal(); window.location.reload();">Close</button>
    </div>
  `);
}

// ---------------- copy button ----------------
function copyBlock(elId, btn) {
  const text = document.getElementById(elId).innerText;
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = original; }, 1500);
  });
}

// ---------------- dashboard: settings ----------------
const autoSprintToggle = document.getElementById('auto-sprint-toggle');
const sprintCadenceInput = document.getElementById('sprint-cadence-input');
const savedNote = document.getElementById('settings-saved-note');

function saveSettings(payload) {
  fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(() => {
    if (savedNote) {
      savedNote.textContent = 'Saved';
      setTimeout(() => { savedNote.textContent = ''; }, 1500);
    }
  });
}

if (autoSprintToggle) {
  autoSprintToggle.addEventListener('change', () => {
    saveSettings({ sprint_auto_enabled: autoSprintToggle.checked });
  });
}
if (sprintCadenceInput) {
  sprintCadenceInput.addEventListener('change', () => {
    saveSettings({ sprint_cadence_days: sprintCadenceInput.value });
  });
}

// ---------------- dashboard: Run Sprint Now ----------------
const runSprintBtn = document.getElementById('run-sprint-btn');
if (runSprintBtn) {
  runSprintBtn.addEventListener('click', triggerSprint);
}

function triggerSprint() {
  runSprintBtn.disabled = true;
  fetch('/api/sprint/run', { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      showModal(`
        <h3>Sprint in progress</h3>
        <div class="progress-note"><span class="spinner"></span> Mutating the active book, scoring accounts, and generating outreach content&hellip;</div>
      `);
      pollSprintStatus(data.sprint_id);
    });
}

function pollSprintStatus(sprintId) {
  const interval = setInterval(() => {
    fetch(`/api/sprint/${sprintId}/status`)
      .then((r) => r.json())
      .then((sprint) => {
        if (sprint.status === 'completed') {
          clearInterval(interval);
          window.location.href = '/plays';
        } else if (sprint.status === 'failed') {
          clearInterval(interval);
          showModal(`
            <h3>Sprint failed</h3>
            <p>${escapeHtml(sprint.error || 'Something went wrong during the sprint.')}</p>
            <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Close</button></div>
          `);
        }
      });
  }, 1200);
}

// Resume polling if a sprint was already in progress when the dashboard loaded.
if (window.__hasRunningSprint) {
  const runningRow = document.querySelector('#sprint-history-body tr');
  if (runningRow) {
    const href = runningRow.getAttribute('onclick') || '';
    const match = href.match(/sprint\/(\d+)/);
    if (match) pollSprintStatus(match[1]);
  }
}
