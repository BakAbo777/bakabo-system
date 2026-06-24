/* BKS Verse — Frontend JS v1
   Gestisce: submit form, counter, result display, lineage card, leaderboard */

(function () {
  'use strict';

  const VERSE_API = window.BKS_VERSE_API_URL || 'https://verse.bakabo.club';
  const MIN_CHARS = 80;
  const MAX_CHARS = 280;

  // ── SUBMIT FORM ───────────────────────────────────────────────────────────
  function initSubmitForm() {
    const form      = document.getElementById('bks-verse-form');
    const textarea  = document.getElementById('bks-verse-text');
    const counter   = document.getElementById('bks-verse-counter');
    const btn       = document.getElementById('bks-verse-submit');
    const resultBox = document.getElementById('bks-verse-result');
    const lineageBox= document.getElementById('bks-verse-lineage');

    if (!form || !textarea) return;

    textarea.addEventListener('input', () => {
      const n = textarea.value.trim().length;
      counter.textContent = `${n} / ${MAX_CHARS}`;
      counter.className = 'bks-verse-counter';
      if (n < MIN_CHARS) {
        counter.classList.add('under');
        btn.disabled = true;
      } else if (n > MAX_CHARS) {
        counter.classList.add('over');
        btn.disabled = true;
      } else {
        counter.classList.add('ready');
        btn.disabled = false;
      }
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      btn.disabled = true;
      btn.textContent = 'Il Giudice sta leggendo...';

      const collection = document.getElementById('bks-verse-collection')?.value || null;
      const payload = {
        member_email:  window.BKS_MEMBER_EMAIL || '',
        poem_text:     textarea.value.trim(),
        collection_slug: collection,
        lang:          'it',
        member_id:     window.BKS_MEMBER_ID || null,
        member_display: window.BKS_MEMBER_DISPLAY || null,
      };

      try {
        const resp = await fetch(`${VERSE_API}/verse/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();

        if (!resp.ok) {
          showError(resultBox, data.detail || 'Errore durante la valutazione.');
          return;
        }

        showResult(resultBox, data);
        if (data.lineage_card) showLineage(lineageBox, data.lineage_card);
        textarea.value = '';
        counter.textContent = `0 / ${MAX_CHARS}`;

      } catch (err) {
        showError(resultBox, 'Connessione al Giudice non riuscita. Riprova tra qualche minuto.');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Presenta al Giudice';
      }
    });
  }

  function showResult(box, data) {
    if (!box) return;
    const v = data.verdict;
    const verdictLabel = v === 'hall' ? '⬛ 25/25 — HALL OF FAME' :
                          v === 'approved' ? 'APPROVATO' : 'NON APPROVATO';
    const s = data.scores || {};

    box.innerHTML = `
      <div class="bks-verse-score-total">${data.score_total}/25</div>
      <div class="bks-verse-verdict ${v}">${verdictLabel}</div>
      <div class="bks-verse-axes-result">
        ${[['image','Image'],['voice','Voice'],['tension','Tension'],['bks_resonance','BKS'],['body','Body']]
          .map(([k,l]) => `
            <div class="bks-verse-axis-result">
              <div class="bks-verse-axis-result-name">${l}</div>
              <div class="bks-verse-axis-result-score">${s[k] || '–'}</div>
            </div>`).join('')}
      </div>
      ${data.approval_message ? `<div class="bks-verse-message">${data.approval_message}</div>` : ''}
    `;
    box.classList.add('visible');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function showLineage(box, card) {
    if (!box || !card) return;
    const p = card.poet;
    const m = card.member;
    const l = card.lineage;

    box.innerHTML = `
      <div class="bks-lineage-card">
        <div class="bks-lineage-header">
          <div>
            <div class="bks-lineage-poet-name">${p.name}</div>
            <div class="bks-lineage-poet-era">${p.era} · ${p.city || ''} · ${p.score_total}/25</div>
          </div>
        </div>
        <div class="bks-lineage-poem-excerpt">"${p.rep_poem_excerpt}"<br>
          <small style="color:var(--verse-muted);font-size:11px;">${p.rep_poem_title}</small>
        </div>
        <div class="bks-lineage-arrow">↓ ${l.il_filo_message || ''}</div>
        <div class="bks-lineage-member-poem">${m.poem_text}</div>
        ${l.lineage_note ? `<div class="bks-lineage-note">${l.lineage_note}</div>` : ''}
      </div>
    `;
  }

  function showError(box, msg) {
    if (!box) return;
    box.innerHTML = `<p style="color:#ff6b6b;text-align:center;padding:20px;">${msg}</p>`;
    box.classList.add('visible');
  }

  // ── LEADERBOARD ────────────────────────────────────────────────────────────
  async function initLeaderboard() {
    const container = document.getElementById('bks-verse-leaderboard');
    if (!container) return;

    container.innerHTML = '<p style="color:var(--verse-muted);text-align:center;">Caricamento classifica...</p>';

    try {
      const resp = await fetch(`${VERSE_API}/leaderboard/global`);
      const data = await resp.json();
      renderLeaderboard(container, data.ranking);
    } catch (e) {
      container.innerHTML = '<p style="color:var(--verse-muted);text-align:center;">Classifica non disponibile</p>';
    }
  }

  function renderLeaderboard(container, ranking) {
    const axes = [
      ['score_image','I'],['score_voice','V'],['score_tension','T'],
      ['score_bks','B'],['score_body','W']
    ];
    const rows = ranking.map(item => {
      const isMember = item.type === 'member';
      const isHall   = item.total === 25;
      const cls      = isHall ? 'hall-row' : isMember ? 'member-row' : '';
      const axPips   = axes.map(([k, l]) =>
        `<div class="bks-lb-axis-pip ${item[k] === 5 ? 'pip-5' : ''}">${l}${item[k]}</div>`
      ).join('');
      return `
        <div class="bks-verse-leaderboard-row ${cls}">
          <div class="bks-lb-rank">${item.rank}</div>
          <div class="bks-lb-name">
            ${item.display_name}
            <small>${isMember ? 'Member BKS' : (item.era || '')} · ${item.poem_title || ''}</small>
          </div>
          <div class="bks-lb-score">${item.total}</div>
          <div class="bks-lb-axes">${axPips}</div>
        </div>`;
    }).join('');

    container.innerHTML = `
      <div class="bks-verse-leaderboard-row" style="opacity:.5;font-size:10px;letter-spacing:2px;">
        <div></div>
        <div style="color:var(--verse-muted);">AUTORE</div>
        <div style="color:var(--verse-muted);text-align:center;">SCORE</div>
        <div style="color:var(--verse-muted);">I · V · T · B · W</div>
      </div>
      ${rows}`;
  }

  // ── INIT ───────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    initSubmitForm();
    initLeaderboard();
  });

})();
