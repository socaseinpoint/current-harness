/* ============================================================================
   shell-client.js — the CONTENT side (any page: dashboard, game).
   Pairs with shell.ts (protocol deck-v1). Loaded by a plain <script>, no build:
     <script src="shell-client.js?b=1"></script>
   The content does NOT know where it runs:
     · inside the Tauri shell (iframe) → requests go up via postMessage
     · standalone in a browser        → web fallback (Fullscreen API / reload)
   window.ShellKit: .framed · .fullscreen(on?) · .reload() · .title(str)
   ========================================================================== */
(function () {
  if (window.ShellKit) return;
  var framed = (function () {
    try { return !!window.parent && window.parent !== window; } catch (_) { return true; }
  })();

  function post(msg) {
    try { window.parent.postMessage(Object.assign({ shell: 'deck-v1' }, msg), '*'); return true; }
    catch (_) { return false; }
  }

  function webFullscreen(on) {
    var d = document, el = d.documentElement;
    var isOn = !!(d.fullscreenElement || d.webkitFullscreenElement);
    var want = on === undefined ? !isOn : on;
    if (want === isOn) return;
    if (want) (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el);
    else (d.exitFullscreen || d.webkitExitFullscreen || function () {}).call(d);
  }

  window.ShellKit = {
    version: 1,
    framed: framed,
    fullscreen: function (on) { if (framed) post({ cmd: 'fullscreen', on: on }); else webFullscreen(on); },
    reload: function () { if (framed) post({ cmd: 'reload' }); else location.reload(); },
    title: function (v) { if (framed) post({ cmd: 'title', value: String(v) }); else document.title = String(v); }
  };
})();
