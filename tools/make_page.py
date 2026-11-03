#!/usr/bin/env python3
"""Turn the published Curio artifact page into the Android app's page.

Usage: python3 tools/make_page.py path/to/curio.html app/src/main/assets/index.html

Changes made for the app:
- Google Fonts links replaced by bundled fonts (assets/fonts)
- cards come from the public feed (feed/latest.json) via the CurioAndroid bridge
- preferences are stored by the app instead of the claude.ai database
- a "Morning reminder" setting, Android back button and resume handling
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()


def sub(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit("pattern not found: " + old[:80])
    s = s.replace(old, new, count)


FONTS = [("Bricolage Grotesque", w, f"bricolage-grotesque-latin-{w}-normal.woff2") for w in (500, 700, 800)] + \
        [("Atkinson Hyperlegible", w, f"atkinson-hyperlegible-latin-{w}-normal.woff2") for w in (400, 700)] + \
        [("IBM Plex Mono", w, f"ibm-plex-mono-latin-{w}-normal.woff2") for w in (400, 500)]
faces = "".join(f'@font-face{{font-family:"{n}";font-weight:{w};font-style:normal;font-display:block;src:url(fonts/{f}) format("woff2")}}\n' for n, w, f in FONTS)

s = re.sub(r'<link rel="preconnect"[^\n]*\n', "", s)
s = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^\n]*\n', "", s)
s = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<style>:root{color-scheme:dark}html,body{margin:0}img{max-width:100%}[hidden]{display:none!important}body{font:14px system-ui,sans-serif}</style>\n' + s

sub("<style>\n/* Layout:", "<style>\n" + faces + "/* Layout:")

# Reminder styles
sub(".note{font-size:14px;", """.remind{display:flex;align-items:center;gap:12px;background:var(--ink-2);border:1px solid var(--line);border-radius:12px;padding:10px 12px 10px 16px}
.remind label{flex:1;color:var(--paper-dim);font-size:15px}
.remind input{font-family:var(--mono);font-size:18px;color:var(--paper);background:transparent;border:1px solid var(--line);border-radius:8px;padding:6px 8px;color-scheme:dark}
.tog{width:48px;height:28px;border-radius:999px;background:var(--paper-faint);position:relative;flex:none;transition:background .2s}
.tog i{position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;background:var(--paper);transition:transform .2s}
.tog.on{background:#8BE3AA}
.tog.on i{transform:translateX(20px);background:var(--ink)}
.rnote{font-size:13px;color:var(--paper-dim);margin:8px 0 0;line-height:1.4}
.note{font-size:14px;""")

# Reminder markup, below the time picker
sub('    <p class="note" id="status">', """    <div id="remindBox" hidden>
      <div class="sec"><span>Morning reminder</span><button id="rtest">Send a test</button></div>
      <div class="remind"><label for="rtime">Notify me at</label><input type="time" id="rtime" value="07:30"><button class="tog on" id="rtog" role="switch" aria-checked="true" aria-label="Morning reminder"><i></i></button></div>
      <p class="rnote" id="rnote"></p>
    </div>
    <p class="note" id="status">""")

# Preferences live in the app
sub("""try{ const raw = localStorage.getItem("curio.prefs"); if(raw) P = Object.assign({}, DEFAULTS, JSON.parse(raw)); }catch(e){}""",
    """try{ const raw = localStorage.getItem("curio.prefs"); if(raw) P = Object.assign({}, DEFAULTS, JSON.parse(raw)); }catch(e){}
try{ if(window.CurioAndroid){ const r = CurioAndroid.getPrefs(); if(r) P = Object.assign({}, DEFAULTS, JSON.parse(r)); } }catch(e){}""")
sub("""  try{ localStorage.setItem("curio.prefs", JSON.stringify(P)); }catch(e){}
  if(!prefsRef) return;""", """  try{ localStorage.setItem("curio.prefs", JSON.stringify(P)); }catch(e){}
  try{ if(window.CurioAndroid) CurioAndroid.setPrefs(JSON.stringify(P)); }catch(e){}
  if(!prefsRef) return;""")

# Images come from the feed's img/ folder
sub("""  if(typeof im.url==="string" && /^\\/_blob\\/[0-9a-f]{32}$/.test(im.url)) return im.url;""",
    """  if(typeof im.file==="string" && /^[\\w.-]+$/.test(im.file)) return FEED_BASE+"img/"+im.file;
  if(typeof im.url==="string" && /^\\/_blob\\/[0-9a-f]{32}$/.test(im.url)) return im.url;""")
sub("""function imgSrc(c){""", """const FEED_BASE = (window.CurioAndroid && CurioAndroid.feedBase()) || "__FEED_BASE__";
function imgSrc(c){""")

# Copy through the app's clipboard
sub("""  try{ await navigator.clipboard.writeText(text); toast("Copied"); }catch(e){ toast("Copy isn't available here"); }""",
    """  if(window.CurioAndroid){ CurioAndroid.copy(text); toast("Copied"); return; }
  try{ await navigator.clipboard.writeText(text); toast("Copied"); }catch(e){ toast("Copy isn't available here"); }""")

# Replace the claude.ai data loading with the feed
start = s.index("async function boot(){")
end = s.index("boot();\n})();")
s = s[:start] + r"""let lastFetch = 0;
const bootDay = today;
function feedProblem(){
  dataReady = true; prefsLoaded = true; renderCTA();
  $("#status").textContent = "Can't reach today's cards. Check your connection, then reopen Curio.";
}
function loadFeedText(txt){
  try{
    const f = JSON.parse(txt);
    const days = (Array.isArray(f.days) ? f.days : []).filter(d => d && typeof d.date === "string" && Array.isArray(d.cards));
    ingest(days); return true;
  }catch(e){ return false; }
}
window.__feed = function(txt){ lastFetch = Date.now(); if(!loadFeedText(txt) && !pool.length) feedProblem(); };
window.__feedFail = function(){ lastFetch = Date.now(); if(!pool.length) feedProblem(); else if(!$("#setup").hidden) $("#status").textContent = "Offline. Showing the cards saved on your phone."; };
window.__back = function(){
  if($("#sheet").classList.contains("show")){ closeSheet(); return true; }
  if($("#setup").hidden){ showSetup(); return true; }
  return false;
};
window.__resume = function(){
  const d = new Date(); const now = d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  if(now !== bootDay){ location.reload(); return; }
  renderReminder();
  if(window.CurioAndroid && Date.now() - lastFetch > 20*60*1000) CurioAndroid.fetchFeed();
};

function fmtTime(h,m){ try{ return new Date(2000,0,1,h,m).toLocaleTimeString([], {hour:"numeric", minute:"2-digit"}); }catch(e){ return h+":"+String(m).padStart(2,"0"); } }
function setTog(on){ const t=$("#rtog"); t.classList.toggle("on", on); t.setAttribute("aria-checked", on); }
function renderReminder(){
  const N = window.CurioAndroid, box = $("#remindBox");
  if(!N){ box.hidden = true; return; }
  box.hidden = false;
  let r = {enabled:true, hour:7, minute:30, allowed:true};
  try{ r = Object.assign(r, JSON.parse(N.getReminder())); }catch(e){}
  $("#rtime").value = String(r.hour).padStart(2,"0")+":"+String(r.minute).padStart(2,"0");
  setTog(!!r.enabled);
  $("#rnote").textContent = !r.enabled ? "The reminder is off." :
    r.allowed ? "You'll get a nudge at "+fmtTime(r.hour, r.minute)+" every morning." :
    "Notifications are blocked. Allow them for Curio in Android settings to get the reminder.";
}
function saveReminder(){
  const N = window.CurioAndroid; if(!N) return;
  const on = $("#rtog").classList.contains("on");
  const parts = ($("#rtime").value || "07:30").split(":").map(Number);
  const h = parts[0] || 0, m = parts[1] || 0;
  N.setReminder(on, h, m);
  toast(on ? "Reminder set for "+fmtTime(h,m) : "Reminder off");
  setTimeout(renderReminder, 500);
}
$("#rtog").onclick = () => { setTog(!$("#rtog").classList.contains("on")); saveReminder(); };
$("#rtime").onchange = saveReminder;
$("#rtest").onclick = () => { if(window.CurioAndroid){ CurioAndroid.testNotification(); toast("Test notification sent"); } };

function boot(){
  prefsLoaded = true;
  renderChips(); renderSeg(); renderCTA(); renderReminder();
  const N = window.CurioAndroid;
  if(N){
    const cached = N.cachedFeed();
    if(cached) loadFeedText(cached);
    N.fetchFeed();
  } else {
    fetch(FEED_BASE + "latest.json").then(r => r.ok ? r.text() : Promise.reject()).then(window.__feed).catch(window.__feedFail);
  }
}
""" + s[end:]

open(out, "w", encoding="utf-8").write(s)
print("wrote", out, len(s), "bytes")
