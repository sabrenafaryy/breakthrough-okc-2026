"""2026-09-23 — Rebuild the Playbook's Cameron section from his ACTUAL deck ("Leverage.", 64 slides,
received 2026-09-20). The old section was built from a published talk title only, because no deck had
arrived. Keys that the Monday page mirrors (c_first, c_who, c_kpi, task_*) are preserved."""
import re, sys
P = '/Users/sabrena/Safary Business/web/breakthrough-okc-2026/website/playbook/index.html'
h = open(P, encoding='utf-8').read()
n0 = len(h)

FORMS = [('uv','Unique value'),('cash','Cash'),('mktg','Marketing'),('debt','Debt'),
         ('ppl','People'),('brand','Brand'),('sys','Systems'),('ai','AI')]
chips = ''.join(
  f'<label><input type="checkbox" data-k="lev_{k}"><span>{n}</span></label>' for k,n in FORMS)

NEW = '''<section class="s" id="cameron">
  <div class="s-head">
    <img src="../assets/cameron.webp" alt="Cameron Burke">
    <div>
      <span class="mono when">1:45 PM &middot; Keynote</span>
      <h2>Cameron Burke</h2>
      <div class="talk">Leverage: Marketing, Systems &amp; Delegation To Scale</div>
    </div>
  </div>
  <p class="stand">Cameron started at 18 with a license, a little saved cash and no leverage &mdash;
  and went nine months without a closing. What changed was not effort. It was finding one piece of
  real leverage, then stacking another on top of it, and another. This section is where you find
  yours.</p>
  <blockquote class="quote">Small force or resource to gain a larger advantage.<cite>Cameron Burke &middot; what leverage actually means</cite></blockquote>

  <div class="card">
    <h3>The eight forms &mdash; which one are you missing?</h3>
    <p class="hint">He walks all eight. Some get you in the door; some multiply what you already have.
    Tick the ones genuinely working in your business today. The blank ones are the point.</p>
    <div class="chips">''' + chips + '''</div>
    <label class="f">The one I'm missing that would change the most</label><input type="text" data-k="c_missing">
    <label class="f">What it would actually take to put it in place</label><textarea data-k="c_missing_how" rows="2"></textarea>
  </div>

  <div class="card">
    <h3>Your number</h3>
    <p class="hint">His litmus test before hiring anyone: know your dollar per hour. <b>Net, not
    gross.</b> Last 12 months' net, divided by the hours you actually worked.</p>
    <label class="f">Your net, last 12 months</label><input type="number" min="0" step="1000" inputmode="numeric" data-k="c_net">
    <label class="f">Hours you actually worked in those 12 months</label><input type="number" min="0" step="10" inputmode="numeric" data-k="c_hours">
    <div class="totals">
      <div class="tot hot"><span class="mono">Your dollar per hour</span><b id="camRate">&mdash;</b><small>Every hour you spend on low-value work costs you this.</small></div>
    </div>
  </div>

  <div class="card">
    <h3>The trade</h3>
    <p class="hint">His example: a transaction coordinator at $3,500 a month, against $6,000 a month
    of his own time doing admin. Easy trade. Run yours.</p>
    <label class="f">The work you'd hand off</label><input type="text" data-k="c_trade_what">
    <label class="f">What it would cost to hire out, per month</label><input type="number" min="0" step="100" inputmode="numeric" data-k="c_trade_cost">
    <label class="f">Hours a month that work takes you</label><input type="number" min="0" step="1" inputmode="numeric" data-k="c_trade_hrs">
    <div class="totals">
      <div class="tot"><span class="mono">What those hours cost you</span><b id="camCost">&mdash;</b></div>
      <div class="tot hot"><span class="mono">The verdict</span><b id="camVerdict">&mdash;</b><small id="camVerdictNote">Fill in your number above first.</small></div>
    </div>
  </div>

  <div class="card">
    <h3>Your week, honestly</h3>
    <p class="hint">Income-producing work is high leverage &mdash; finding deals, making offers,
    talking to sellers. Everything else is a candidate to hand off. List your week, then decide.</p>
    <div class="tw"><table class="t">
      <thead><tr><th>Task I do every week</th><th style="width:16%">Hours / week</th><th style="width:24%">Keep, delegate, or automate?</th></tr></thead>
      <tbody data-repeat="8" data-prefix="task">
        <template><tr><td><input type="text" data-k="task_{i}_what"></td><td><input type="number" min="0" step="0.5" inputmode="decimal" data-k="task_{i}_hrs"></td>
        <td><select data-k="task_{i}_do"><option value=""></option><option>Keep</option><option>Delegate</option><option>Automate</option></select></td></tr></template>
      </tbody>
    </table></div>
    <div class="totals">
      <div class="tot"><span class="mono">Hours a week, total</span><b id="hrsTotal">0</b></div>
      <div class="tot hot"><span class="mono">Hours you could hand off</span><b id="hrsOff">0</b><small>That's time back.</small></div>
    </div>
  </div>

  <div class="card">
    <h3>Hand one thing off properly</h3>
    <p class="hint">He hired a transaction coordinator before he had systems, and called the result
    chaos. Handing work over is not the same as handing over a closed loop.</p>
    <label class="f">The first thing you'd hand over</label><input type="text" data-k="c_first">
    <label class="f">Who would own it?</label><input type="text" data-k="c_who">
    <label class="f">How will you know it got done, without checking yourself?</label><textarea data-k="c_loop" rows="2"></textarea>
    <label class="f">What happens when it doesn't?</label><textarea data-k="c_fail" rows="2"></textarea>
  </div>

  <div class="card">
    <h3>Start where the chaos is</h3>
    <p class="hint">His answer to "which system do I build first" is whatever feels like chaos right
    now. His own contract-to-close system fits on one page: who does what, in what order.</p>
    <label class="f">What feels like chaos in my business right now</label><textarea data-k="c_chaos" rows="2"></textarea>
    <label class="f">The first system I'll write down</label><input type="text" data-k="c_system">
    <label class="f">Who runs it once it exists?</label><input type="text" data-k="c_system_who">
  </div>

  <div class="card">
    <h3>Your buy box, in three numbers</h3>
    <p class="hint">Every deal he buys runs through the same three. Write yours &mdash; and if you
    don't have them yet, that's the takeaway.</p>
    <div class="tw"><table class="t">
      <thead><tr><th style="width:26%">The number</th><th style="width:28%">His</th><th>Yours</th></tr></thead>
      <tbody>
        <tr><td class="lbl">All-in cost</td><td class="his">Under 70% of ARV</td><td><input type="text" data-k="c_bb_arv"></td></tr>
        <tr><td class="lbl">Cash-on-cash</td><td class="his">25% minimum</td><td><input type="text" data-k="c_bb_coc"></td></tr>
        <tr><td class="lbl">Exit</td><td class="his">Has to be refinanceable</td><td><input type="text" data-k="c_bb_refi"></td></tr>
      </tbody>
    </table></div>
  </div>

  <div class="card">
    <h3>Data is leverage</h3>
    <p class="hint">His words: it shows you the pulse of the business, so you know which lever to
    pull. Pick the one number you'll actually watch every week.</p>
    <label class="f">The one number you'll watch</label><input type="text" data-k="c_kpi">
  </div>

  <div class="card">
    <h3>Two things that stop people</h3>
    <p class="hint">He names both: fear that outweighs your goals, and lifestyle creep that eats the
    leverage you just built. Be honest on one line each.</p>
    <label class="f">The fear that's currently bigger than my goal</label><textarea data-k="c_fear" rows="2"></textarea>
    <label class="f">Where lifestyle creep is showing up for me</label><textarea data-k="c_creep" rows="2"></textarea>
  </div>

  <div class="card">
    <h3>The line you're writing down</h3>
    <textarea data-k="c_rule" rows="2"></textarea>
  </div>
</section>'''

m = re.search(r'<section class="s" id="cameron">.*?</section>', h, re.S)
assert m and len(m.group(0)) < 6000, m and len(m.group(0))
h = h[:m.start()] + NEW + h[m.end():]

# Monday: surface the missing form of leverage
old_card = ('<div class="mcard"><span class="mono">The number you\'ll watch</span>'
            '<span class="mono from">Cameron</span><div class="v" data-mirror="c_kpi"></div></div>')
assert h.count(old_card) == 1
h = h.replace(old_card, old_card +
    '\n    <div class="mcard"><span class="mono">The leverage you\'re missing</span>'
    '<span class="mono from">Cameron</span><div class="v" data-mirror="c_missing"></div></div>')

# JS: dollar-per-hour + the trade verdict
anchor = "    document.getElementById('hrsTotal').textContent=+tot.toFixed(1);"
assert h.count(anchor) == 1
h = h.replace(anchor, anchor + '''

    var rate=0, net=num('c_net'), hrs=num('c_hours');
    if(net>0 && hrs>0){ rate=net/hrs; document.getElementById('camRate').textContent=money(rate)+'/hr'; }
    else document.getElementById('camRate').textContent='\\u2014';
    var tHrs=num('c_trade_hrs'), tCost=num('c_trade_cost'), yourCost=rate*tHrs;
    document.getElementById('camCost').textContent = (rate&&tHrs) ? money(yourCost)+'/mo' : '\\u2014';
    var vEl=document.getElementById('camVerdict'), nEl=document.getElementById('camVerdictNote');
    if(rate&&tHrs&&tCost){
      if(yourCost>tCost){ vEl.textContent='Easy trade';
        nEl.textContent='Hiring it out costs '+money(tCost)+'. Doing it yourself costs '+money(yourCost)+'. You buy back '+(+tHrs.toFixed(1))+' hours.'; }
      else { vEl.textContent='Not yet';
        nEl.textContent='At '+money(rate)+'/hr those hours cost you '+money(yourCost)+' \\u2014 less than the '+money(tCost)+' to hire out. Raise your number or hand off something bigger.'; }
    } else { vEl.textContent='\\u2014'; nEl.textContent='Fill in your number above first.'; }''')

assert 0 < len(h) - n0 < 9000, len(h) - n0
open(P, 'w', encoding='utf-8').write(h)
print('ok +', len(h) - n0)
