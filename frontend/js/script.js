document.addEventListener('DOMContentLoaded', () => {

  // ===== STATE =====
  let candidates = [];
  let uploadedFileId = null;
  let isLiveData = false;

  // ===== DOM REFS =====
  const $ = id => document.getElementById(id);
  const uploadZone = $('uploadZone');
  const fileInput = $('fileInput');
  const fileInfo = $('fileInfo');
  const fileName = $('fileName');
  const fileRemove = $('fileRemove');
  const jdInput = $('jdInput');
  const runBtn = $('runPipelineBtn');
  const statusDot = $('statusDot');
  const engineStatus = $('engineStatus');
  const tableBody = $('tableBody');
  const candidateSelect = $('candidateSelect');
  const inspectorCard = $('inspectorCard');
  const loadingOverlay = $('loadingOverlay');
  const toast = $('toast');
  const sidebar = $('sidebar');
  const sidebarToggle = $('sidebarToggle');

  // metric refs
  const metricScanned = $('metricScanned');
  const metricPurged = $('metricPurged');
  const metricDefused = $('metricDefused');
  const metricNet = $('metricNet');
  const downloadBtn = $('downloadBtn');

  // inspector refs
  const inspectorName = $('inspectorName');
  const inspectorBadge = $('inspectorBadge');
  const inspectorRank = $('inspectorRank');
  const inspectorScore = $('inspectorScore');
  const inspectorStatus = $('inspectorStatus');
  const inspectorExp = $('inspectorExp');
  const inspectorReasoning = $('inspectorReasoning');

  // ===== HELPERS =====
  const API_BASE = '';

  function toastMsg(msg, type = 'info') {
    const iconMap = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${iconMap[type] || iconMap.info}"></i> ${msg}`;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), 3500);
  }

  function setLoading(on) {
    loadingOverlay.style.display = on ? 'flex' : 'none';
    runBtn.disabled = on;
    if (on) runBtn.classList.add('loading');
    else runBtn.classList.remove('loading');
  }

  function setEngineStatus(ok) {
    statusDot.className = 'status-dot ' + (ok ? 'online' : 'offline');
    engineStatus.textContent = ok ? 'Online' : 'Offline';
  }

  function formatScore(score) {
    const s = parseFloat(score);
    if (s >= 90) return `<span class="score-high">${s.toFixed(2)}%</span>`;
    if (s >= 80) return `<span class="score-mid">${s.toFixed(2)}%</span>`;
    return `<span class="score-low">${s.toFixed(2)}%</span>`;
  }

  function formatSecurity(status) {
    const s = (status || '').toUpperCase();
    if (s === 'CLEARED' || s.includes('🟢')) return '<span class="status-cleared"><i class="fas fa-shield-halved"></i> CLEARED</span>';
    if (s === 'FLAGGED' || s.includes('🟡')) return '<span class="status-flagged"><i class="fas fa-triangle-exclamation"></i> FLAGGED</span>';
    return `<span class="status-blocked"><i class="fas fa-ban"></i> ${status}</span>`;
  }

  function rankClass(rank) {
    if (rank === 1) return 'rank-gold';
    if (rank === 2) return 'rank-silver';
    if (rank === 3) return 'rank-bronze';
    return '';
  }

  function getApiUrl(path) {
    return API_BASE + path;
  }

  // ===== FILE UPLOAD =====
  uploadZone.addEventListener('click', () => fileInput.click());

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
  });
  fileRemove.addEventListener('click', (e) => {
    e.stopPropagation();
    resetUpload();
  });

  function resetUpload() {
    uploadedFileId = null;
    fileInfo.hidden = true;
    fileInput.value = '';
    uploadZone.hidden = false;
  }

  async function handleFile(file) {
    const validTypes = ['.json', '.jsonl'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validTypes.includes(ext)) {
      toastMsg('Please upload a .json or .jsonl file', 'error');
      return;
    }

    fileName.textContent = file.name;
    fileInfo.hidden = false;
    uploadZone.hidden = true;

    const form = new FormData();
    form.append('file', file);

    try {
      const res = await fetch(getApiUrl('/api/upload'), { method: 'POST', body: form });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      uploadedFileId = data.file_id;
      toastMsg(`File "${file.name}" uploaded (${(data.size / 1024).toFixed(1)} KB)`, 'success');
    } catch (err) {
      toastMsg('Upload failed, will use mock data mode', 'error');
      resetUpload();
      uploadedFileId = null;
    }
  }

  // ===== CHECK ENGINE STATUS =====
  async function checkEngine() {
    try {
      const res = await fetch(getApiUrl('/api/mock'));
      if (res.ok) {
        setEngineStatus(true);
        return;
      }
    } catch (_) {}
    setEngineStatus(false);
  }
  checkEngine();

  // ===== RUN PIPELINE =====
  runBtn.addEventListener('click', runPipeline);

  async function runPipeline() {
    if (runBtn.disabled) return;
    setLoading(true);

    try {
      const jdText = jdInput.value.trim() || 'Looking for Core Software Engineers, NLP systems expert, Rust/Python production exp.';

      let data;

      if (uploadedFileId) {
        const res = await fetch(getApiUrl('/api/rank'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_id: uploadedFileId, jd_text: jdText })
        });
        if (!res.ok) throw new Error('Ranking failed');
        data = await res.json();
      } else {
        const res = await fetch(getApiUrl('/api/mock'));
        if (!res.ok) throw new Error('Mock data unavailable');
        data = await res.json();
      }

      applyResults(data);
      toastMsg(isLiveData ? 'Analysis Complete! Live engine metrics mapped below.' : 'Using Mock Environment Data (Upload file to live-test)', isLiveData ? 'success' : 'info');

    } catch (err) {
      toastMsg('Engine unavailable — loading mock data', 'info');
      // fallback to client-side mock
      applyResults(null);
    } finally {
      setLoading(false);
    }
  }

  // ===== APPLY RESULTS =====
  function applyResults(data) {
    if (data && data.metrics) {
      isLiveData = data.metrics.live_data;
      metricScanned.textContent = data.metrics.total_scanned || '100,000';
      metricPurged.textContent = data.metrics.purged || '1,412';
      metricDefused.textContent = data.metrics.honeypots_defused || '76';
      metricNet.textContent = data.metrics.net_elite || '98,512';
    } else {
      isLiveData = false;
      metricScanned.textContent = '100,000';
      metricPurged.textContent = '1,412';
      metricDefused.textContent = '76';
      metricNet.textContent = '98,512';
    }

    if (data && data.results && data.results.length) {
      candidates = data.results;
    } else {
      candidates = generateMockData();
    }

    renderTable(candidates);
    populateSelect(candidates);
    downloadBtn.disabled = false;
  }

  // ===== CLIENT-SIDE MOCK GENERATOR =====
  function generateMockData() {
    const names = [
      'Candidate_UX_01', 'Candidate_FS_99', 'Candidate_DE_42',
      'Candidate_AI_07', 'Candidate_SYS_11', 'Candidate_ML_33',
      'Candidate_BD_88', 'Candidate_SEC_21', 'Candidate_QA_55',
      'Candidate_DEVOPS_77'
    ];
    const reasoning = [
      'Boasts 4+ years of verified production-level Rust experience matching the JD perfectly. Cleared all timeline overlapping checks.',
      'Exceptional alignment with core NLP requirements; open-source contributions to major libraries verified.',
      'Strong fundamental architecture background. System caught a mild keyword-stuffing attempt but core competence is genuine.',
      'Top tier matching parameters for specialized ML Ops pipeline. Interview highly recommended.',
      'Solid distributed systems experience. All background timelines and graduation details cross-referenced and cleared.',
      'Deep expertise in Python-based data pipelines with proven track record in production environments.',
      'Strong full-stack capabilities with modern framework experience. Security signals all nominal.',
      'Excellent system design knowledge with emphasis on scalable architectures. Open to work flag active.',
      'Verified contributions to major open-source NLP projects. Response rate above 85% indicating high engagement.',
      'Robust backend engineering background with database optimization expertise. All integrity checks passed.'
    ];

    const data = [];
    for (let i = 1; i <= 100; i++) {
      const n = names[(i + 3) % names.length];
      const r = reasoning[(i + 7) % reasoning.length];
      data.push({
        Rank: i,
        'Candidate ID': `CR-2026-${1000 + i}`,
        'Fit Score (%)': parseFloat((78.5 + Math.random() * 20.7).toFixed(2)),
        'Experience (Yrs)': parseFloat((2.0 + Math.random() * 6.5).toFixed(1)),
        'Security Status': 'CLEARED',
        Reasoning: r,
        Name: n
      });
    }
    return data;
  }

  // ===== RENDER TABLE =====
  function renderTable(data) {
    if (!data.length) {
      tableBody.innerHTML = '<tr><td colspan="6" class="table-placeholder">No results to display</td></tr>';
      return;
    }

    tableBody.innerHTML = data.map(c => {
      const rank = c.Rank;
      const score = c['Fit Score (%)'];
      const exp = c['Experience (Yrs)'];
      const sec = c['Security Status'] || 'CLEARED';
      const reason = c.Reasoning || '';
      const id = c['Candidate ID'];

      return `<tr>
        <td class="${rankClass(rank)}">${rank}</td>
        <td>${id}</td>
        <td>${formatScore(score)}</td>
        <td>${exp}</td>
        <td>${formatSecurity(sec)}</td>
        <td>${reason}</td>
      </tr>`;
    }).join('');
  }

  // ===== TABLE SORTING =====
  document.querySelectorAll('.data-table th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      const isAsc = th.classList.contains('asc');

      document.querySelectorAll('.data-table th.sortable').forEach(h => {
        h.classList.remove('active', 'asc', 'desc');
      });

      th.classList.add('active', isAsc ? 'desc' : 'asc');

      candidates.sort((a, b) => {
        let va, vb;
        switch (key) {
          case 'Rank': va = a.Rank; vb = b.Rank; break;
          case 'CandidateID': va = a['Candidate ID']; vb = b['Candidate ID']; break;
          case 'FitScore': va = a['Fit Score (%)']; vb = b['Fit Score (%)']; break;
          case 'Experience': va = a['Experience (Yrs)']; vb = b['Experience (Yrs)']; break;
          case 'Security': va = a['Security Status'] || ''; vb = b['Security Status'] || ''; break;
          default: return 0;
        }
        if (typeof va === 'string') {
          return isAsc ? va.localeCompare(vb) : vb.localeCompare(va);
        }
        return isAsc ? va - vb : vb - va;
      });

      // Reassign ranks
      candidates.forEach((c, i) => c.Rank = i + 1);
      renderTable(candidates);
    });
  });

  // ===== POPULATE SELECT =====
  function populateSelect(data) {
    candidateSelect.innerHTML = '<option value="">— Select a candidate —</option>' +
      data.map(c => `<option value="${c['Candidate ID']}">${c['Candidate ID']} (Rank #${c.Rank})</option>`).join('');
    candidateSelect.disabled = false;
    inspectorCard.hidden = true;
  }

  // ===== CANDIDATE INSPECTOR =====
  candidateSelect.addEventListener('change', () => {
    const id = candidateSelect.value;
    if (!id) { inspectorCard.hidden = true; return; }

    const c = candidates.find(x => x['Candidate ID'] === id);
    if (!c) { inspectorCard.hidden = true; return; }

    inspectorName.textContent = `Profile Summary: ${c['Candidate ID']}`;
    inspectorBadge.textContent = `#${c.Rank}`;
    inspectorRank.textContent = `#${c.Rank}`;
    inspectorScore.textContent = `${c['Fit Score (%)']}%`;
    inspectorExp.textContent = c['Experience (Yrs)'] != null ? `${c['Experience (Yrs)']} yrs` : 'N/A';
    inspectorStatus.textContent = c['Security Status'] || 'CLEARED';
    inspectorStatus.className = 'stat-value ' + ((c['Security Status'] || '').toUpperCase() === 'CLEARED' ? 'status-cleared' : 'status-flagged');

    const p = inspectorReasoning.querySelector('p');
    p.textContent = c.Reasoning || 'No detailed reasoning available for this candidate.';
    inspectorCard.hidden = false;
  });

  // ===== DOWNLOAD CSV =====
  downloadBtn.addEventListener('click', () => {
    if (!candidates.length) return;

    const headers = ['candidate_id', 'rank', 'score', 'reasoning'];
    const rows = candidates.map(c => [
      c['Candidate ID'],
      c.Rank,
      c['Fit Score (%)'],
      `"${(c.Reasoning || '').replace(/"/g, '""')}"`
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'submission.csv';
    link.click();
    URL.revokeObjectURL(link.href);
    toastMsg('submission.csv downloaded', 'success');
  });

  // ===== SIDEBAR TOGGLE (MOBILE) =====
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 900 &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });

  // ===== LOAD DEFAULT MOCK ON START =====
  setTimeout(() => {
    candidates = generateMockData();
    renderTable(candidates);
    populateSelect(candidates);
    downloadBtn.disabled = false;
    setLoading(false);
  }, 300);
});
