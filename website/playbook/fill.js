/* Turn what someone typed in the browser into the designed 12-page Playbook PDF.
   Runs entirely on their device: the template is fetched once (and cached), filled with pdf-lib,
   and handed back as a download. Nothing is uploaded. */
(function (root) {
  'use strict';

  // web key -> PDF field. Straight renames first.
  var DIRECT = {
    name: 'name', worth: 'worth',
    k_step1: 'k_step_1', k_step2: 'k_step_2', k_step3: 'k_step_3',
    k_block: 'k_block', k_block_change: 'k_change', k_block_know: 'k_know', k_block_who: 'k_ask',
    k_edge: 'k_edge',
    k_ml_said: 'k_ml_said', k_ml_mine: 'k_ml_mine', k_vs_said: 'k_vs_said', k_vs_mine: 'k_vs_mine',
    k_cm_said: 'k_cm_said', k_cm_mine: 'k_cm_mine',
    kd_purchase: 'kd_purchase', kd_reno: 'kd_reno', kd_hold: 'kd_hold', kd_loan: 'kd_loan',
    kd_cash: 'kd_cash', kd_grant: 'kd_grant',
    kr_rent: 'kr_rent', kr_opex: 'kr_opex', kr_cap: 'kr_cap',
    n_start: 'n_start', n_katie: 'n_katie', n_panel: 'n_panel', n_room: 'n_room',
    n_cam: 'n_cam', n_ben: 'n_ben', n_ask: 'n_ask',
    atr_n_1: 'atr_n_1', atr_n_2: 'atr_n_2', atr_n_3: 'atr_n_3',
    atr_n_4: 'atr_n_4', atr_n_5: 'atr_n_5', atr_n_6: 'atr_n_6',
    p_where: 'p_where', p_size: 'p_size',
    p_q1: 'p_q_1', p_q2: 'p_q_2', p_q3: 'p_q_3',
    c_missing: 'c_missing', c_missing_how: 'c_missing_how',
    c_net: 'c_net', c_hours: 'c_hours',
    c_trade_what: 'c_trade_what', c_trade_cost: 'c_trade_cost', c_trade_hrs: 'c_trade_hrs',
    c_first: 'c_first', c_who: 'c_who', c_loop: 'c_loop', c_fail: 'c_fail',
    c_chaos: 'c_chaos', c_system: 'c_system', c_system_who: 'c_system_who',
    c_bb_arv: 'c_bb_arv', c_bb_coc: 'c_bb_coc', c_bb_refi: 'c_bb_refi',
    c_kpi: 'c_kpi', c_fear: 'c_fear', c_creep: 'c_creep', c_rule: 'c_rule',
    b_tuesday: 'b_tuesday', b_ego: 'b_ego', b_why: 'b_why',
    b_npd: 'b_npd', b_moh: 'b_moh', b_move: 'b_move', b_move_step: 'b_move_step',
    atr_q: 'atr_q', m_did: 'm_did', m_one: 'm_one',
    b_true1: 'b_true_1', b_true2: 'b_true_2', b_true3: 'b_true_3',
    ss_h_r: 'b_health_r', ss_h_c: 'b_health_c',
    ss_r_r: 'b_rel_r', ss_r_c: 'b_rel_c',
    ss_m_r: 'b_mind_r', ss_m_c: 'b_mind_c'
  };

  // checkbox groups, in the PDF's numbered order
  var CHECKS = {
    inv: ['type_new', 'type_flip', 'type_hold', 'type_wholesale', 'type_build', 'type_agent', 'type_capital'],
    p_what: ['p_new', 'p_rehab', 'p_rent', 'p_flip', 'p_home', 'p_unsure'],
    lev: ['lev_uv', 'lev_cash', 'lev_mktg', 'lev_debt', 'lev_ppl', 'lev_brand', 'lev_sys', 'lev_ai']
  };

  // repeated table rows: pdfPrefix -> [webSuffix per column], rows
  var TABLES = [
    { pdf: 'prog', web: 'prog', cols: ['name', 'lvl', 'why', 'next'], rows: 5 },
    { pdf: 'call', web: 'call', cols: ['name', 'org', 'ask'], rows: 4 },
    { pdf: 'ppl', web: 'ppl', cols: ['name', 'what', 'why'], rows: 8 },
    { pdf: 'act', web: 'act', cols: ['1', '2', '3'], rows: 3 },
    { pdf: 'task', web: 'task', cols: ['what', 'hrs', 'do'], rows: 8 },
    { pdf: 'oh', web: 'oh', cols: ['what', 'cost', 'made', 'do'], rows: 8 }
  ];

  /* The PDF's form fields use Helvetica/WinAnsi, which cannot encode arrows, emoji, or anything
     else outside its set — pdf-lib throws rather than dropping them. Swap the ones we generate,
     and strip anything else exotic a person might paste in. */
  var SWAP = { '\u2192': '->', '\u2190': '<-', '\u2194': '<->', '\u21d2': '=>',
               '\u2713': 'x', '\u2714': 'x', '\u2717': 'x', '\u00a0': ' ',
               '\u2212': '-', '\u2044': '/', '\u2032': "'", '\u2033': '"' };
  var WINANSI_EXTRA = [0x20AC,0x201A,0x0192,0x201E,0x2026,0x2020,0x2021,0x02C6,0x2030,0x0160,
                       0x2039,0x0152,0x017D,0x2018,0x2019,0x201C,0x201D,0x2022,0x2013,0x2014,
                       0x02DC,0x2122,0x0161,0x203A,0x0153,0x017E,0x0178];
  function safe(str, report) {
    var out = '', i, ch, cp, lost = 0;
    for (i = 0; i < str.length; i++) {
      ch = str[i];
      if (SWAP[ch] != null) { out += SWAP[ch]; continue; }
      cp = str.codePointAt(i);
      if (ch === '\n' || ch === '\r') { out += ch; continue; }
      if (ch === '\t') { out += ' '; continue; }
      if ((cp >= 0x20 && cp <= 0x7E) || (cp >= 0xA0 && cp <= 0xFF) || WINANSI_EXTRA.indexOf(cp) !== -1) {
        out += ch;
        continue;
      }
      lost++;
      if (cp > 0xFFFF) i++;   // skip the low surrogate of an astral pair (emoji)
    }
    if (lost && report) report.lost += lost;
    return out;
  }

  function v(d, k) {
    var x = d[k];
    if (x == null || typeof x === 'object' || typeof x === 'boolean') return '';
    return String(x).trim();
  }
  /* People type "$180,000" and "1,800". The page and the PDF must read that the same way, or the
     screen says one rate and the downloaded PDF says another. Anything that isn't a plain number
     (with optional $, commas, decimals) reads as 0 rather than being silently coerced. */
  function parseNum(raw) {
    if (raw == null || typeof raw === 'object' || typeof raw === 'boolean') return 0;
    var s = String(raw).replace(/[$\s]/g, '');
    if (!/\d/.test(s)) return 0;
    if (!/^-?(\d{1,3}(,\d{3})+|\d*)(\.\d+)?$/.test(s)) return 0;
    var x = parseFloat(s.replace(/,/g, ''));
    return isFinite(x) ? x : 0;
  }
  function n(d, k) { return parseNum(d[k]); }
  function money(x) { return '$' + Math.round(x).toLocaleString('en-US'); }

  /* Everything the web page works out on the fly — the hourly rate, the trade verdict,
     the Monday summary cards — has to be written into the PDF as plain text. */
  function derived(d) {
    var out = {};
    var rate = 0, net = n(d, 'c_net'), hrs = n(d, 'c_hours');
    if (net > 0 && hrs > 0) { rate = net / hrs; out.c_rate = money(rate) + ' /hr'; }

    var th = n(d, 'c_trade_hrs'), tc = n(d, 'c_trade_cost'), mine = rate * th;
    if (rate > 0 && th > 0) {
      out.c_trade_mine = money(mine) + ' /mo';
      if (tc) { out[mine > tc ? 'c_trade_verdict_1' : 'c_trade_verdict_2'] = true; }
    }

    for (var i = 1; i <= 6; i++) {
      var pos = v(d, 'sw_' + i);
      if (pos === 'Old way') out['sw_' + i + '_old'] = true;
      else if (pos === 'New way') out['sw_' + i + '_new'] = true;
    }

    /* the overhead totals the page shows live, written into the PDF as text */
    var ohT = 0, ohC = 0;
    for (i = 1; i <= 8; i++) {
      var c2 = n(d, 'oh_' + i + '_cost');
      ohT += c2;
      if (v(d, 'oh_' + i + '_do') === 'Cut') ohC += c2;
    }
    if (ohT > 0) out.b_oh_total = money(ohT) + '/mo';
    if (ohC > 0) { out.b_oh_cut = money(ohC) + '/mo'; out.b_oh_year = money(ohC * 12) + ' a year'; }

    var kAll = n(d,'kd_purchase') + n(d,'kd_reno') + n(d,'kd_hold');
    if (kAll > 0) out.kd_allin = money(kAll);
    if (n(d,'kd_cash') > 0) out.kd_left = money(n(d,'kd_cash') - n(d,'kd_grant'));
    var kNoi = n(d,'kr_rent') - n(d,'kr_opex'), kCap = n(d,'kr_cap');
    if (n(d,'kr_rent') > 0) out.kr_noi = money(kNoi) + '/mo';
    if (kNoi > 0 && kCap > 0) {
      var kVal = (kNoi * 12) / (kCap / 100);
      out.kr_value = money(kVal);
      if (n(d,'kd_loan') > 0) out.kr_equity = money(kVal - n(d,'kd_loan'));
    }

    // the Monday page, written out the way the web version assembles it
    out.m_life = v(d, 'b_tuesday');
    out.m_lev = v(d, 'c_missing');
    out.m_block = v(d, 'k_block');
    out.m_kpi = v(d, 'c_kpi');
    out.m_worth_echo = v(d, 'worth');

    var cut = [], cutT = 0;
    for (i = 1; i <= 8; i++) {
      if (v(d, 'oh_' + i + '_do') === 'Cut') {
        var c = n(d, 'oh_' + i + '_cost'); cutT += c;
        cut.push('• ' + (v(d, 'oh_' + i + '_what') || 'Unnamed cost') + (c ? ' (' + money(c) + '/mo)' : ''));
      }
    }
    if (cut.length) out.m_cut = cut.join('\n') + (cutT ? '\n= ' + money(cutT * 12) + ' a year' : '');

    var hand = [];
    if (v(d, 'c_first')) hand.push('• ' + v(d, 'c_first') + (v(d, 'c_who') ? ' → ' + v(d, 'c_who') : ''));
    var off = 0;
    for (i = 1; i <= 8; i++) if (/Delegate|Automate/.test(v(d, 'task_' + i + '_do'))) off += n(d, 'task_' + i + '_hrs');
    if (off) hand.push('• ' + (+off.toFixed(1)) + ' hrs/week to hand off');
    if (hand.length) out.m_hand = hand.join('\n');

    var pr = [];
    for (i = 1; i <= 5; i++) if (v(d, 'prog_' + i + '_name'))
      pr.push('• ' + v(d, 'prog_' + i + '_name') + (v(d, 'prog_' + i + '_lvl') ? ' (' + v(d, 'prog_' + i + '_lvl') + ')' : ''));
    if (pr.length) out.m_prog = pr.join('\n');

    var pp = [];
    for (i = 1; i <= 8; i++) if (v(d, 'ppl_' + i + '_name'))
      pp.push('• ' + v(d, 'ppl_' + i + '_name') + (v(d, 'ppl_' + i + '_why') ? ' — ' + v(d, 'ppl_' + i + '_why') : ''));
    if (pp.length) out.m_ppl = pp.join('\n');

    return out;
  }

  /** data (the saved answers) -> {text:{pdfField:value}, checks:{pdfField:true}} */
  function mapFields(data) {
    var text = {}, checks = {}, k;
    for (k in DIRECT) if (v(data, k)) text[DIRECT[k]] = v(data, k);

    Object.keys(CHECKS).forEach(function (group) {
      CHECKS[group].forEach(function (webKey, i) {
        if (data[webKey] === true) checks[group + '_' + (i + 1)] = true;
      });
    });

    TABLES.forEach(function (t) {
      for (var r = 1; r <= t.rows; r++) {
        t.cols.forEach(function (col, ci) {
          var val = v(data, t.web + '_' + r + '_' + col);
          if (val) text[t.pdf + '_' + r + '_' + (ci + 1)] = val;
        });
      }
    });

    var extra = derived(data);
    for (k in extra) {
      if (extra[k] === true) checks[k] = true;
      else if (extra[k]) text[k] = extra[k];
    }
    return { text: text, checks: checks };
  }

  async function buildPdf(templateBytes, data, PDFLib) {
    var pdf = await PDFLib.PDFDocument.load(templateBytes);
    var form = pdf.getForm();
    var mapped = mapFields(data), missing = [], truncated = [], report = { lost: 0 };

    Object.keys(mapped.text).forEach(function (name) {
      try {
        var f = form.getTextField(name), val = safe(mapped.text[name], report);
        /* Belt and braces: if a field still carries a length cap, trim to it rather than let
           pdf-lib throw and drop the whole answer. Losing the tail beats losing the lot. */
        var cap = f.getMaxLength && f.getMaxLength();
        if (cap && val.length > cap) { val = val.slice(0, cap); truncated.push(name); }
        /* Long answers: step the type down so more of it stays inside the box. */
        if (val.length > 420) f.setFontSize(7);
        else if (val.length > 200) f.setFontSize(8);
        f.setText(val);
      }
      catch (e) { missing.push(name + ' (' + (e && e.message ? e.message.slice(0, 60) : 'error') + ')'); }
    });
    Object.keys(mapped.checks).forEach(function (name) {
      try { form.getCheckBox(name).check(); }
      catch (e) { missing.push(name); }
    });

    if (missing.length && root.console) console.warn('Playbook: fields that failed', missing);
    if (truncated.length && root.console) console.warn('Playbook: truncated to field cap', truncated);
    return { bytes: await pdf.save(), filled: Object.keys(mapped.text).length, missing: missing,
             truncated: truncated, lostChars: report.lost };
  }

  root.PlaybookFill = { mapFields: mapFields, buildPdf: buildPdf, parseNum: parseNum,
                        DIRECT: DIRECT, TABLES: TABLES, CHECKS: CHECKS };
})(typeof window !== 'undefined' ? window : globalThis);
