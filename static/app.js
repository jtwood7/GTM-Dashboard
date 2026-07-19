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
    <h3>Export to Outreach Tool</h3>
    <p>This would create a row in a Clay table for every contact on this page and drop them
    into your outreach sequence. Known contacts go in as-is, ready to sequence. For the ones
    tagged &ldquo;Search on Clay / LinkedIn&rdquo; &mdash; where we only know the title, not the
    person &mdash; Clay's enrichment would automatically find who currently holds that role at
    ${company}, pull their contact info, and add them to the same sequence, no manual research
    needed.</p>
    <p class="muted" style="margin-top:10px">No real export happens in this demo.</p>
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
      ? `This would upload ${n} known contact${plural}' hashed emails to a Meta Custom Audience
         scoped to ${company}, ready to target with TRACTIAN ads. Unknown titles at this account
         aren't email-matchable yet &mdash; Clay enrichment (see &ldquo;Export to Outreach
         Tool&rdquo; above) would need to identify them first, or they'd need a company-level
         LinkedIn Matched Audience instead, which doesn't require an individual email.`
      : `${company} doesn't have any known contacts yet, so there's nothing to email-match into a
         Meta Custom Audience. Run &ldquo;Export to Outreach Tool&rdquo; first to enrich the
         unknown titles, or fall back to a company-level LinkedIn Matched Audience.`;
  } else {
    title = 'Enrolled in HubSpot Nurture';
    body = n > 0
      ? `This would add ${n} known contact${plural} at ${company} to a HubSpot nurture sequence
         matched to this account's play, so follow-up emails stay consistent with the outreach
         already drafted below.`
      : `${company} doesn't have any known contacts yet, so there's nothing to enroll in a HubSpot
         nurture sequence. Run &ldquo;Export to Outreach Tool&rdquo; first to enrich the unknown
         titles.`;
  }
  showModal(`
    <h3>${title}</h3>
    <p>${body}</p>
    <p class="muted" style="margin-top:10px">No real sync happens in this demo.</p>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal(); window.location.reload();">Close</button>
    </div>
  `);
}

// ---------------- technical flow diagrams (Mermaid) ----------------
function openFlowModal(flowKey) {
  fetch(`/api/flow-diagram/${flowKey}`)
    .then((r) => r.json())
    .then((data) => {
      showModal(`
        <h3>${escapeHtml(data.title)}</h3>
        <div class="mermaid-container"><pre class="mermaid">${data.mermaid}</pre></div>
        <p class="muted" style="margin-top:10px">This is the integration flow it would actually follow &mdash;
        nothing real happens in this demo.</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" onclick="closeModal(); window.location.reload();">Close</button>
        </div>
      `);
      if (window.mermaid) {
        window.mermaid.run({ querySelector: '.mermaid-container .mermaid' });
      }
    });
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
