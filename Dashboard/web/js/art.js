/**
 * Brand mark and illustrations. All original vector art, built from the four
 * Google-style brand colours plus soft tonal shapes.
 */
const Art = {
  logo(size = 44) {
    return `
    <svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="lg-body" x1="24" y1="22" x2="24" y2="38" gradientUnits="userSpaceOnUse"><stop stop-color="#5B9BFF"/><stop offset="1" stop-color="#1D5FD8"/></linearGradient>
        <linearGradient id="lg-tile" x1="0" y1="0" x2="0" y2="48" gradientUnits="userSpaceOnUse"><stop stop-color="var(--surface)"/><stop offset="1" stop-color="var(--container)"/></linearGradient>
      </defs>
      <rect x="1" y="1" width="46" height="46" rx="14" fill="url(#lg-tile)" stroke="var(--outline-soft)" stroke-width="1.2"/>
      <g stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 16v-2.5A4.5 4.5 0 0 1 13.5 9H16" stroke="#4285F4"/>
        <path d="M32 9h2.5A4.5 4.5 0 0 1 39 13.5V16" stroke="#EA4335"/>
        <path d="M39 32v2.5a4.5 4.5 0 0 1-4.5 4.5H32" stroke="#FBBC04"/>
        <path d="M16 39h-2.5A4.5 4.5 0 0 1 9 34.5V32" stroke="#34A853"/>
      </g>
      <path d="M18.8 22.5v-3a5.2 5.2 0 0 1 10.4 0v3" stroke="#2B6BE0" stroke-width="3" stroke-linecap="round"/>
      <rect x="15" y="22" width="18" height="14" rx="4.2" fill="url(#lg-body)"/>
      <path d="M17.5 24.2h13" stroke="#fff" stroke-opacity=".35" stroke-width="1.4" stroke-linecap="round"/>
      <circle cx="24" cy="28.4" r="2.1" fill="#fff"/><path d="M24 29.6v3" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
    </svg>`;
  },

  /** Home hero: a scanning face card orbited by security chips. */
  hero() {
    return `
    <svg class="hero-art" viewBox="0 0 320 260" fill="none" aria-hidden="true">
      <g class="art-blob"><path d="M58 70c10-28 52-42 84-30 34 12 40 46 20 66s-52 24-80 14S48 96 58 70z" fill="#4285F4" opacity=".16"/></g>
      <g class="art-blob" style="animation-delay:-3s"><path d="M200 168c14-22 54-26 74-6s14 52-12 62-62 0-66-24c-1-12 0-22 4-32z" fill="#FBBC04" opacity=".22"/></g>
      <g class="art-blob" style="animation-delay:-6s"><circle cx="262" cy="64" r="26" fill="#EA4335" opacity=".14"/></g>
      <circle cx="40" cy="214" r="18" fill="#34A853" opacity=".18"/>

      <g class="art-orbit"><circle cx="160" cy="130" r="108" stroke="#4285F4" stroke-opacity=".35" stroke-width="2" stroke-dasharray="3 9" stroke-linecap="round"/></g>
      <g class="art-orbit-rev"><circle cx="160" cy="130" r="88" stroke="#34A853" stroke-opacity=".35" stroke-width="2" stroke-dasharray="2 12" stroke-linecap="round"/></g>

      <g class="art-float">
        <rect x="104" y="64" width="112" height="132" rx="28" fill="var(--surface)" stroke="var(--outline-soft)" stroke-width="2"/>
        <g stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M118 90v-6a8 8 0 0 1 8-8h6" stroke="#4285F4"/>
          <path d="M188 76h6a8 8 0 0 1 8 8v6" stroke="#EA4335"/>
          <path d="M202 170v6a8 8 0 0 1-8 8h-6" stroke="#FBBC04"/>
          <path d="M132 184h-6a8 8 0 0 1-8-8v-6" stroke="#34A853"/>
        </g>
        <circle cx="160" cy="114" r="20" fill="#4285F4" opacity=".92"/>
        <path d="M122 168c2-20 18-30 38-30s36 10 38 30z" fill="#4285F4" opacity=".92"/>
        <circle cx="153" cy="112" r="2.2" fill="#fff"/><circle cx="167" cy="112" r="2.2" fill="#fff"/>
        <path d="M154 120c3.5 3 8.5 3 12 0" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
        <rect class="art-scan-line" x="112" y="128" width="96" height="3" rx="1.5" fill="#34A853" opacity=".85"/>
      </g>

      <g class="art-float d1"><circle cx="64" cy="132" r="20" fill="var(--surface)" stroke="var(--outline-soft)" stroke-width="2"/>
        <path d="M56 133v-4a8 8 0 0 1 16 0v4M54 133h20v10a3 3 0 0 1-3 3H57a3 3 0 0 1-3-3z" transform="translate(-0 -3)" stroke="#EA4335" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g>
      <g class="art-float d2"><circle cx="258" cy="118" r="20" fill="var(--g-green)"/><path d="M249 118.5l6 6 11-12" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></g>
      <g class="art-float d3"><circle cx="214" cy="38" r="15" fill="var(--g-yellow)"/><path d="M214 31l7 3v4.5c0 4-3 7-7 8.5-4-1.5-7-4.5-7-8.5V34z" fill="#fff" opacity=".95"/></g>
      <g class="art-float d1"><circle cx="100" cy="228" r="9" fill="#EA4335" opacity=".85"/></g>
      <g class="art-float d2"><circle cx="228" cy="232" r="6" fill="#4285F4" opacity=".85"/></g>
    </svg>`;
  },

  emptyUsers() {
    return `
    <svg viewBox="0 0 168 128" fill="none" aria-hidden="true">
      <ellipse cx="84" cy="112" rx="56" ry="8" fill="currentColor" opacity=".08"/>
      <circle cx="30" cy="44" r="14" fill="#FBBC04" opacity=".25"/><circle cx="144" cy="86" r="10" fill="#EA4335" opacity=".2"/>
      <g class="art-float"><rect x="46" y="14" width="76" height="92" rx="22" fill="var(--surface)" stroke="var(--outline)" stroke-width="2" stroke-dasharray="5 6"/>
      <circle cx="84" cy="48" r="14" fill="#4285F4" opacity=".25"/><path d="M58 90c2-15 13-22 26-22s24 7 26 22" fill="#4285F4" opacity=".25"/>
      <circle cx="116" cy="94" r="14" fill="#34A853"/><path d="M116 87v14M109 94h14" stroke="#fff" stroke-width="3" stroke-linecap="round"/></g>
    </svg>`;
  },

  emptyApps() {
    return `
    <svg viewBox="0 0 168 128" fill="none" aria-hidden="true">
      <ellipse cx="84" cy="114" rx="56" ry="7" fill="currentColor" opacity=".08"/>
      <g class="art-float"><rect x="30" y="20" width="108" height="78" rx="14" fill="var(--surface)" stroke="var(--outline)" stroke-width="2"/>
      <path d="M30 40h108" stroke="var(--outline)" stroke-width="2"/><circle cx="44" cy="30" r="3" fill="#EA4335"/><circle cx="55" cy="30" r="3" fill="#FBBC04"/><circle cx="66" cy="30" r="3" fill="#34A853"/>
      <rect x="44" y="54" width="40" height="8" rx="4" fill="#4285F4" opacity=".25"/><rect x="44" y="70" width="64" height="8" rx="4" fill="currentColor" opacity=".1"/>
      <circle cx="120" cy="86" r="16" fill="#4285F4"/><rect x="113" y="84" width="14" height="10" rx="3" fill="#fff"/><path d="M116 84v-3a4 4 0 0 1 8 0v3" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></g>
    </svg>`;
  },

  emptyLogs() {
    return `
    <svg viewBox="0 0 168 128" fill="none" aria-hidden="true">
      <ellipse cx="84" cy="114" rx="52" ry="7" fill="currentColor" opacity=".08"/>
      <g class="art-float"><rect x="42" y="12" width="84" height="100" rx="16" fill="var(--surface)" stroke="var(--outline)" stroke-width="2"/>
      <circle cx="62" cy="38" r="7" fill="#34A853" opacity=".85"/><rect x="76" y="33" width="34" height="10" rx="5" fill="currentColor" opacity=".12"/>
      <circle cx="62" cy="62" r="7" fill="#4285F4" opacity=".85"/><rect x="76" y="57" width="28" height="10" rx="5" fill="currentColor" opacity=".12"/>
      <circle cx="62" cy="86" r="7" fill="#FBBC04" opacity=".9"/><rect x="76" y="81" width="38" height="10" rx="5" fill="currentColor" opacity=".12"/></g>
    </svg>`;
  },

  /** Material-style four-colour indeterminate spinner. */
  spinner() {
    return `<svg class="gspinner" viewBox="0 0 50 50" aria-label="Loading"><circle cx="25" cy="25" r="20"/></svg>`;
  },

  icon(name, cls = "") {
    return `<svg class="i ${cls}" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  },
};

/* ───── Extra art ───── */
const star = (x, y, r, c, cls) => `<path class="twinkle ${cls}" d="M${x} ${y - r}Q${x} ${y} ${x + r} ${y}Q${x} ${y} ${x} ${y + r}Q${x} ${y} ${x - r} ${y}Q${x} ${y} ${x} ${y - r}z" fill="${c}"/>`;
const sparkles = () => star(26, 24, 8, '#FBBC04', '') + star(146, 18, 6, '#4285F4', 't2') + star(150, 70, 5, '#EA4335', 't3') + star(16, 96, 5, '#34A853', 't2');
for (const k of ['emptyUsers', 'emptyApps', 'emptyLogs']) {
  const base = Art[k].bind(Art);
  Art[k] = () => base().replace('</svg>', sparkles() + '</svg>');
}

/** Animated four-stage recognition flow. */
Art.pipeline = function () {
  const nodes = [
    { x: 95, c: '#4285F4', t: 'Detect', d: 'Finds your face at any angle' },
    { x: 285, c: '#EA4335', t: 'Align', d: '5 landmarks, pose, quality' },
    { x: 475, c: '#FBBC04', t: 'Embed', d: '128-number face signature' },
    { x: 665, c: '#34A853', t: 'Match', d: 'Compared with all your angles' },
  ];
  const icon = [
    c => `<g stroke="${c}" stroke-width="3" stroke-linecap="round" fill="none"><path d="M-12 -4v-6a2 2 0 0 1 2-2h6M4 -12h6a2 2 0 0 1 2 2v6M12 4v6a2 2 0 0 1-2 2H4M-4 12h-6a2 2 0 0 1-2-2V4"/></g><circle r="5" fill="${c}"/>`,
    c => `<g fill="${c}"><circle cx="-8" cy="-5" r="2.6"/><circle cx="8" cy="-5" r="2.6"/><circle cx="0" cy="2" r="2.6"/><circle cx="-6" cy="10" r="2.6"/><circle cx="6" cy="10" r="2.6"/></g>`,
    c => [-12, -6, 0, 6, 12].map((x, i) => `<rect class="eq-bar" style="animation-delay:${i * 0.18}s" x="${x - 2}" y="-12" width="4" height="24" rx="2" fill="${c}"/>`).join(''),
    c => `<path d="M-11 1l7 7 14-15" stroke="${c}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`,
  ];
  const parts = nodes.map((n, i) => `
    <g transform="translate(${n.x} 48)">
      <circle r="32" fill="${n.c}" fill-opacity=".14"/>
      <circle r="32" fill="none" stroke="${n.c}" stroke-opacity=".5" stroke-width="1.5"/>
      ${icon[i](n.c)}
    </g>
    <text x="${n.x}" y="106" text-anchor="middle">${n.t}</text>
    <text class="sub" x="${n.x}" y="123" text-anchor="middle">${n.d}</text>`).join('');
  const lines = [0, 1, 2].map(i => `<line class="flow-line" x1="${nodes[i].x + 40}" y1="48" x2="${nodes[i + 1].x - 40}" y2="48" stroke="var(--outline)" stroke-width="2" stroke-linecap="round"/>`).join('');
  return `<svg class="pipeline" viewBox="0 0 760 132" fill="none" role="img" aria-label="Detect, align, embed, match">
    ${lines}${parts}
    <circle r="5" fill="#4285F4"><animateMotion dur="5s" repeatCount="indefinite" path="M95 48H665"/></circle>
  </svg>`;
};

/** Semicircular strictness gauge; call Art.setGauge(el, pct) to animate it. */
Art.gauge = function (frac = .33) {
  return `<svg class="gauge" id="gauge" viewBox="0 0 280 176" fill="none" aria-hidden="true">
    <defs><linearGradient id="gg" x1="30" y1="0" x2="250" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#34A853"/><stop offset=".45" stop-color="#FBBC04"/><stop offset="1" stop-color="#EA4335"/></linearGradient></defs>
    <path d="M30 140A110 110 0 0 1 250 140" stroke="var(--container-high)" stroke-width="18" stroke-linecap="round"/>
    <path class="arc" d="M30 140A110 110 0 0 1 250 140" stroke="url(#gg)" stroke-width="18" stroke-linecap="round" stroke-dasharray="346" stroke-dashoffset="${346 * (1 - frac)}"/>
    ${Array.from({ length: 7 }, (_, i) => { const a = Math.PI * (1 - i / 6), x1 = 140 + 92 * Math.cos(a), y1 = 140 - 92 * Math.sin(a), x2 = 140 + 84 * Math.cos(a), y2 = 140 - 84 * Math.sin(a);
      return `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="var(--outline)" stroke-width="2" stroke-linecap="round"/>`; }).join('')}
    <g class="needle" style="transform:rotate(${-90 + frac * 180}deg)"><path d="M140 140L140 62" stroke="var(--text)" stroke-width="4" stroke-linecap="round"/><circle cx="140" cy="140" r="9" fill="var(--text)"/><circle cx="140" cy="140" r="3.5" fill="var(--surface)"/></g>
    <text x="30" y="166" font-size="11" fill="var(--text-3)" text-anchor="middle">Easier</text>
    <text x="250" y="166" font-size="11" fill="var(--text-3)" text-anchor="middle">Stricter</text>
  </svg>`;
};
Art.setGauge = function (frac) {
  const g = document.getElementById('gauge'); if (!g) return;
  g.querySelector('.arc').setAttribute('stroke-dashoffset', 346 * (1 - frac));
  g.querySelector('.needle').style.transform = `rotate(${-90 + frac * 180}deg)`;
};

/** Ideal framing guide: dashed face oval inside a camera frame. */
Art.framing = function () {
  return `<svg viewBox="0 0 320 190" fill="none" aria-hidden="true" style="width:100%;height:auto">
    <rect x="6" y="6" width="308" height="178" rx="22" fill="var(--container)" stroke="var(--outline-soft)" stroke-width="2"/>
    <g stroke-width="5" stroke-linecap="round"><path d="M26 44v-8a10 10 0 0 1 10-10h8" stroke="#4285F4"/><path d="M276 26h8a10 10 0 0 1 10 10v8" stroke="#EA4335"/><path d="M294 146v8a10 10 0 0 1-10 10h-8" stroke="#FBBC04"/><path d="M44 164h-8a10 10 0 0 1-10-10v-8" stroke="#34A853"/></g>
    <path d="M70 184c4-38 40-52 90-52s86 14 90 52z" fill="#4285F4" opacity=".16"/>
    <ellipse class="frame-oval" cx="160" cy="88" rx="44" ry="56" stroke="#34A853" stroke-width="3"/>
    <circle cx="160" cy="88" r="38" fill="#4285F4" opacity=".0"/>
    <circle cx="144" cy="82" r="3" fill="var(--text-2)"/><circle cx="176" cy="82" r="3" fill="var(--text-2)"/>
    <path d="M148 106c7 6 17 6 24 0" stroke="var(--text-2)" stroke-width="3" stroke-linecap="round"/>
    <g transform="translate(262 150)"><circle r="14" fill="#34A853"/><path d="M-6 0l4.5 4.5L7 -4.5" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></g>
  </svg>`;
};

window.Art = Art;
