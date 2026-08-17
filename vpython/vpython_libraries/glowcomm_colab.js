// glowcomm_colab.js — browser side of the Colab (comm-only) VPython frontend.
//
// Injected inline by with_colab.py via display(HTML). Loads GlowScript from
// a CDN (Colab output frames may load external scripts; jsDelivr serves the
// vpython/vscode-vpython repo's media/ directory), then registers a Jupyter
// comm target through Colab's shim (google.colab.kernel.comms) and drives
// glowcomm_host.js:
//
//   downlink:  comm message (msg.data = package | 'trigger') -> fe.handle
//   uplink:    pacer -> fe.tick() -> send(events) -> comm.send(events)
//
// Colab comm API (probed 2026-08): registerTarget(name, cb); the comm object
// is {send, close, messages} with messages an async iterator. The kernel may
// retry the comm open (it can't know when this script has run), so every
// open is acked and the LATEST comm becomes the active channel.
//
// Adaptive pacing: 33 ms while the kernel is answering, easing off to 500 ms
// when nothing has come back for 2 s (kernel blocked in a long computation
// or between cells) — bounds the message backlog a blocked kernel must
// swallow when it wakes.

window.__VPYTHON_COLAB_BOOT = function (opts) {
  'use strict';
  var CDN = opts.cdn;     // ends with '/'
  var NONCE = opts.nonce; // this session's token; stale saved frames have an old one
  var TICK_MS = 33, SLOW_MS = 500, EASE_AFTER_MS = 2000;

  var root = document.getElementById('vpython-colab-root');
  var status = document.createElement('div');
  status.style.cssText = 'font-family:monospace;font-size:12px;opacity:.8';
  var container = document.createElement('div');
  root.appendChild(status);
  root.appendChild(container);

  function setStatus(m) { status.textContent = m; }
  function fail(m) {
    var line = document.createElement('pre');
    line.textContent = 'VPython (Colab): ' + m;
    line.style.cssText = 'color:#c00;white-space:pre-wrap';
    root.appendChild(line);
  }

  function loadScript(name) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = CDN + name;
      s.onload = resolve;
      s.onerror = function () { reject(new Error('failed to load ' + CDN + name)); };
      document.head.appendChild(s);
    });
  }

  // Hide any AMD loader while classic UMD scripts execute (else jQuery UI
  // registers as a module and never patches $.fn — learned in VS Code).
  var hadDefine = Object.prototype.hasOwnProperty.call(window, 'define');
  var savedDefine = window.define;
  try { window.define = undefined; } catch (e) { }
  function restoreAmd() {
    if (hadDefine) { window.define = savedDefine; }
    else { try { delete window.define; } catch (e) { } }
  }

  setStatus('VPython: loading GlowScript from CDN…');
  loadScript('jquery.min.js')
    .then(function () { return loadScript('jquery-ui.custom.min.js'); })
    .then(function () { return loadScript('glow.min.js'); })
    .then(function () {
      window.Jupyter_VPython = CDN + 'data/'; // texture prefix for glow
      function loadFont(file, slot) {
        return new Promise(function (resolve, reject) {
          window.opentype_load(window.Jupyter_VPython + file, function (err, font) {
            if (err) { reject(new Error('font ' + file + ': ' + err)); return; }
            window[slot] = font;
            resolve();
          });
        });
      }
      return Promise.all([
        loadFont('Roboto-Medium.ttf', '__font_sans'),
        loadFont('NimbusRomNo9L-Med.otf', '__font_serif')
      ]);
    })
    .then(function () { return loadScript('glowcomm_host.js?v=' + NONCE); })
    .then(function () {
      restoreAmd();
      var jq = window.$ || window.jQuery;
      if (!jq || !jq.fn || typeof jq.fn.resizable !== 'function') {
        throw new Error('jQuery UI did not attach ($.fn.resizable missing)');
      }
      if (typeof window.createGlowFrontend !== 'function') {
        throw new Error('glowcomm_host loaded but createGlowFrontend missing');
      }

      var active = null, fe = null, lastReply = Date.now();

      function startPacer() {
        (function tickLoop() {
          var idle = Date.now() - lastReply > EASE_AFTER_MS;
          try { fe.tick(); } catch (e) { fail('tick: ' + e); }
          setTimeout(tickLoop, idle ? SLOW_MS : TICK_MS);
        })();
      }

      // Shared by both handshake directions: bind a live comm as the active
      // channel, create the frontend on first use, and pump its messages.
      function useComm(comm, ackFirst) {
        active = comm; // latest wins on both sides
        if (ackFirst) { comm.send({ ack: 1 }); }
        if (!fe) {
          fe = window.createGlowFrontend({
            container: container,
            glow: window,
            send: function (events) { if (active) { active.send(events); } }
          });
          startPacer();
          setStatus('');
        }
        (async function () {
          try {
            for await (var m of comm.messages) {
              lastReply = Date.now();
              var d = (m && m.data !== undefined) ? m.data : m;
              fe.handle(d === 'trigger' ? 'trigger' : d);
            }
          } catch (e) { /* iterator ends when comm closes; a newer comm takes over */ }
        })();
      }

      var comms = google.colab.kernel.comms;

      // Fallback: kernel-initiated opens (retried from the kernel idle loop).
      comms.registerTarget('vpython-glow', function (comm, openMsg) {
        // Ignore kernel-initiated opens meant for a different session's frame.
        var d = openMsg && (openMsg.data || (openMsg.content && openMsg.content.data));
        if (d && d.nonce && d.nonce !== NONCE) { return; }
        useComm(comm, true); // ack tells the kernel which comm to attach
      });

      // Preferred: WE open the comm, because only we know when this script
      // has actually finished loading. The kernel registered the target
      // before displaying this bootstrap, so it always exists by now. The
      // kernel processes the open at its next idle moment and flushes the
      // buffered scene. No races, no retries.
      if (typeof comms.open === 'function') {
        Promise.resolve(comms.open('vpython-glow-kernel', { nonce: NONCE }))
          .then(function (comm) {
            if (comm && comm.send && comm.messages) { useComm(comm, true); }
            else { setStatus('VPython: comms.open returned unusable comm; ' +
                             'waiting for kernel-initiated connect…'); }
          })
          .catch(function (e) {
            setStatus('VPython: comms.open failed (' + e + '); ' +
                      'waiting for kernel-initiated connect…');
          });
        setStatus('VPython: ready — connecting to the kernel…');
      } else {
        setStatus('VPython: ready — waiting for the kernel to connect ' +
                  '(run the next cell if this lingers)…');
      }
    })
    .catch(function (e) { restoreAmd(); fail((e && e.stack) || String(e)); });
};
