// glowcomm_host.js — host-agnostic browser front-end for the VPython wire protocol.
//
// Ported from glowcomm.js, which is the Jupyter-notebook front end: it owns a
// Comm/WebSocket, loads fonts out of the nbextensions data directory, paces
// itself with a setTimeout loop, and calls GlowScript constructors that Jupyter
// happens to have put on `window`. Everything in that list is the *host's* job.
//
// What is left after removing it is the part that is actually the protocol: turn
// a decoded {cmds, methods, attrs} package into GlowScript objects. That is this
// file. It knows nothing about Jupyter, websockets, Pyodide, or any particular
// embedding page; the host supplies the GlowScript constructor registry, a
// container element, and a send() for the event channel.
//
//   var fe = createGlowFrontend({container: el, send: fn, glow: window})
//   fe.handle(ops)   // ops is the parsed {cmds, methods, attrs} package, or 'trigger'
//   fe.tick()        // one pacing tick: sample the canvas, drain queued events
//   fe.reset()       // forget every object (new scene generation)
//   fe.destroy()     // reset + ask the objects to remove themselves
//
// Mouse/key event capture IS ported (see "the event channel" below). Widgets,
// pause and waitfor are not: those are deferred by design (spec V5, they raise
// NotImplementedError on the Python side) and their call sites warn and drop.

'use strict';

function createGlowFrontend(opts) {
    opts = opts || {};

    // The GlowScript constructor registry. glowcomm.js called `sphere(cfg)` and
    // friends as bare globals; here they come off `glow` so a test (or a second
    // scene) can supply its own.
    var glow = opts.glow || globalThis;
    // Where the host wants the canvas to appear (may be null; see 'canvas' below).
    var container = opts.container || null;
    // Host's outbound channel for events. Only the deferred stubs use it today.
    var send = opts.send || null;

    // Every object Python has created, indexed by the idx Python assigned.
    var glowObjs = [];

    // glowcomm.js could rely on `vec`/`curve`/`points` being real constructors on
    // the page, so it used a bare `instanceof`. Here the registry is injected and
    // may not be constructible (the unit tests pass plain functions), which makes
    // `instanceof` throw. Same answer as `instanceof` for real GlowScript classes.
    function is_a(value, Ctor) {
        try { return typeof Ctor === 'function' && value instanceof Ctor; }
        catch (e) { return false; }
    }

    // glowcomm.js decoded and consumed the Comm payload in place (it owned that
    // object and threw it away afterwards). Here the package belongs to the
    // caller and may be replayed or inspected, so the two mutating paths —
    // decode() rewriting data.attrs, and handle_cmds() deleting cmd/idx/method —
    // work on shallow copies instead.
    function shallow_copy(obj) {
        var copy = {}, k;
        for (k in obj) {
            if (Object.prototype.hasOwnProperty.call(obj, k)) copy[k] = obj[k];
        }
        return copy;
    }

    // ---------------------------------------------------------------------------
    // The event channel back to Python.
    //
    // glowcomm.js pushed events onto a module-global list and drained it from a
    // free-running setTimeout loop that also owned the render pacing. Here the
    // HOST owns when a tick happens (it calls tick() off its own clock) and this
    // file owns what goes in it. The event objects themselves are byte-faithful
    // to glowcomm.js, because those shapes ARE the wire contract that
    // vpython.py's handle_msg (:394-425) and canvas.handle_event (:3287) read.
    // ---------------------------------------------------------------------------

    var events = [];              // queued outbound events, drained by tick()/flush()
    var last_tick = -Infinity;    // when the host last called tick()

    // How long after a tick() we keep assuming the host's clock is running.
    // Hosts pace at glowcomm.js's ~33 ms `interval`, so this is three misses.
    var PACING_GRACE_MS = 100;

    function now_ms() {
        if (typeof performance !== 'undefined' && performance.now) return performance.now();
        return Date.now();
    }

    function flush() {
        if (events.length === 0) return;
        var out = events;
        events = [];
        if (send) send(out);
    }

    // Queue one event for Python. While the host is ticking, tick() drains this
    // within a frame and the events coalesce — that batching is the only reason
    // glowcomm.js has a queue at all. When the host is NOT ticking, nothing will
    // ever drain the queue, so the event goes out on its own.
    //
    // That second case is not a corner: a host whose pacing clock belongs to the
    // RUN (trinket's does) has no clock at all by the time the user clicks, and
    // `scene.bind('click', f)` followed by the end of the program is exactly
    // what an interactive VPython example looks like. The click has to carry
    // itself.
    function queue(evt) {
        events.push(evt);
        if (now_ms() - last_tick > PACING_GRACE_MS) flush();
    }

    // pick and compound/text/extrusion are synchronous barriers: Python is
    // blocked inside _wait() until the answer comes back. They never wait for a
    // tick, even when one is due — but they go out with anything already queued,
    // so ordering is preserved.

    function send_pick(cvs, p, seg) {
        var evt = {event: 'pick', 'canvas': cvs, 'pick': p, 'segment':seg};
        events.push(evt);
        flush();
    }

    function send_compound(cvs, pos, size, up) {
        var evt = {event: '_compound', 'canvas': cvs, 'pos': [pos.x, pos.y, pos.z],
            'size': [size.x, size.y, size.z], 'up': [up.x, up.y, up.z]};
        events.push(evt);
        flush();
    }

    // glowcomm.js process() (:311-346): one browser event, in the shape
    // canvas.handle_event() destructures. `event` is GlowScript's event object.
    function process(event) {
        // mouse events: mouseup, mousedown, mousemove, mouseenter, mouseleave, click
        // key events: keydown, keyup
        // other: resize
        var etype = event.type;
        var evt = {event:etype};
        var idx = event.canvas['idx'];
        evt.canvas = idx;
        if (etype != 'resize') {
            if (etype.slice(0,3) == 'key') {
                evt.key = event.key;
                evt.which = event.which;
                evt.alt = event.alt;
                evt.ctrl = event.ctrl;
                evt.shift = event.shift;
            } else {
                var pos = event.pos;
                evt.pos = [pos.x, pos.y, pos.z];
                evt.press = event.press;
                evt.release = event.release;
                evt.which = event.which;
                var ray = event.canvas.mouse.ray;
                evt.ray = [ ray.x, ray.y, ray.z ];
                evt.alt = event.canvas.mouse.alt;
                evt.ctrl = event.canvas.mouse.ctrl;
                evt.shift = event.canvas.mouse.shift;
            }
        } else {
            evt.width = event.canvas.width;
            evt.height = event.canvas.height;
        }
        if ('bind' in event) evt.bind = true;
        queue(evt);
    }

    function process_binding(event) {  // event associated with a previous bind command
        event.bind = true;
        process(event);
    }

    // These three must NOT forward anything. pause, waitfor and widgets are
    // deferred by design (spec V5): the Python side raises NotImplementedError
    // before any of them can reach the browser, so these handlers are reachable
    // only if that deferral is lifted without porting them. Anything this file
    // could synthesize would be a PARTIAL event, and a partial event does not
    // fail politely: handle_msg indexes object_registry by evt['idx'] and reads
    // evt['value']/evt['text'] for widgets (vpython.py:400-415), and
    // handle_event reads evt['alt']/['shift']/['ctrl'] for a mouse event
    // (vpython.py:3335) — a stub raises KeyError inside the kernel's message
    // loop. Warning and dropping is the honest behaviour.

    function not_wired(feature) {
        if (typeof console !== 'undefined') console.warn('glowcomm_host: ' + feature + ' not wired yet');
    }

    function process_waitfor(event) {
        not_wired('waitfor');
    }

    function process_pause() {
        not_wired('pause');
    }

    function control_handler(obj) {  // button, menu, slider, radio, checkbox, winput
        not_wired('widgets');
    }

    var waitfor_canvas = null;
    var waitfor_options = null;
    // possible event types to bind:
    var binds = ['mousedown', 'mouseup', 'mousemove', 'click', 'mouseenter', 'mouseleave',
                 'keydown', 'keyup', 'redraw', 'draw_complete', 'resize'];

    // ---------------------------------------------------------------------------
    // Canvas polling: the half of the state only the BROWSER knows.
    // ---------------------------------------------------------------------------

    // The previous sample, so a still scene sends nothing. glowcomm.js kept these
    // as module globals seeded with vec(0,0,0); here they are per-front-end and
    // re-seeded by reset(), because a new scene generation starts from scratch.
    var lastpos, lastray, lastforward, lastup, lastcenter;
    var lastrange, lastautoscale, lastsliders, lastkeysdown;
    // glowcomm.js's control_handler() samples slider values in here so a drag
    // reports once per render instead of once per pixel. Widgets are deferred
    // (see control_handler above) so it stays empty, but update_canvas' half of
    // that mechanism is ported whole rather than left as a hole to re-derive.
    var sliders;

    function vzero() { return (typeof glow.vec === 'function') ? glow.vec(0, 0, 0) : null; }

    function reset_canvas_state() {
        lastpos = vzero(); lastray = vzero(); lastforward = vzero();
        lastup = vzero(); lastcenter = vzero();
        lastrange = 1;
        lastautoscale = true;
        lastsliders = {};
        lastkeysdown = [];
        sliders = {};
    }
    reset_canvas_state();

    // glowcomm.js update_canvas() (:193-275). Mouse position and camera state
    // for the canvas the mouse is over, diffed against the last sample; returns
    // an array of events, or null when nothing changed.
    function update_canvas() {
        var dosend = false;
        var evt = null;
        // `canvas.hasmouse` is a static on GlowScript's canvas class — the only
        // way it changes is with the mouse.
        var cvs = glow.canvas ? glow.canvas.hasmouse : null;
        // ...and being a class static, it OUTLIVES a scene: after reset() it can
        // still point at a canvas from a torn-down generation, whose idx now
        // means something else (or nothing) in Python's object_registry. Only
        // report a canvas this front-end still owns.
        if (cvs && glowObjs[cvs.idx] !== cvs) cvs = null;

        if (cvs !== null && cvs !== undefined) {
            evt = {event:'update_canvas'};
            var idx = cvs.idx;
            evt.canvas = idx;
            var pos = cvs.mouse.pos;
            if (!lastpos || !pos.equals(lastpos)) {evt.pos = [pos.x,pos.y,pos.z]; dosend=true;}
            lastpos = pos;
            var ray = cvs.mouse.ray;
            if (!lastray || !ray.equals(lastray)) {evt.ray = [ray.x,ray.y,ray.z]; dosend=true;}
            lastray = ray;

            // glowcomm.js calls the bare global keysdown(); a host that supplied
            // its own registry may not have it, in which case report no change.
            var k = (typeof glow.keysdown === 'function') ? glow.keysdown() : lastkeysdown;
            var test = true; // assume keysdown() is same as lastkeysdown
            if (k.length !== lastkeysdown.length) test = false;
            else {
                for (var i=0; i<k.length; i++) {
                    if (k[i] !== lastkeysdown[i]) {
                        test = false;
                        break;
                    }
                }
            }
            if (!test) {
                evt.keysdown = lastkeysdown = k;
                dosend = true;
            }

            // forward and range may be changed by user (and up with touch), and autoscale (by zoom)
            if (cvs.userspin) {
                var forward = cvs.forward;
                if (!lastforward || !forward.equals(lastforward)) {
                    evt.forward = [forward.x,forward.y,forward.z];
                    dosend=true;
                }
                lastforward = forward;
                var up = cvs.up;
                if (!lastup || !up.equals(lastup)) {
                    evt.up = [up.x,up.y,up.z];
                    dosend=true;
                }
                lastup = up;
            }
            if (cvs.userpan) {
                var center = cvs.center;
                if (!lastcenter || !center.equals(lastcenter)) {
                    evt.center = [center.x,center.y,center.z];
                    dosend=true;
                }
                lastcenter = center;
            }
            if (cvs.userzoom) {
                var range = cvs.range;
                if (range !== lastrange) {evt.range=range; dosend=true;}
                lastrange = range;
                var autoscale = cvs.autoscale;
                if (autoscale !== lastautoscale) {evt.autoscale = autoscale; dosend=true;}
                lastautoscale = autoscale;
            }
            if (dosend) evt = [evt];
        }
        var output_sliders = [];
        for (var ss in sliders) {
            var ev = sliders[ss];
            if (ss in lastsliders && ev.value !== lastsliders[ss].value)
                output_sliders.push(ev); // avoid sending an unchanged slider value
            lastsliders[ss] = ev;
        }
        if (output_sliders.length > 0) {
            if (dosend) evt = evt.concat(output_sliders);
            else evt = output_sliders;
            dosend = true;
        }
        if (dosend) return evt;
        else return null;
    }

    // glowcomm.js send() (:150-170) — the WHAT of one pacing tick. Upstream's
    // send() also owned the WHEN (it re-armed its own setTimeout); that half is
    // the host's, which is why this is a method it calls rather than a loop.
    //
    // Note the fallback. An empty tick still sends {event:'update_canvas',
    // trigger:1}: the transport treats a 'trigger' entry as pacing and processes
    // nothing, but the MESSAGE is the request half of a request/reply — it is
    // what makes the kernel flush the updates it has buffered. A tick that sent
    // nothing would stall a program that never calls rate().
    function tick() {
        last_tick = now_ms();
        var update = update_canvas();
        var out = events;
        events = [];
        if (update !== null) out = out.concat(update);
        if (out.length === 0) out = [{event:'update_canvas', 'trigger':1}];
        if (send) send(out);
        return out;
    }

    // ---------------------------------------------------------------------------
    // The wire format. Ported verbatim from glowcomm.js.
    // ---------------------------------------------------------------------------

    // attrs are X in {'a': '23X....'} available: none
    var attrs = {'a':'pos', 'b':'up', 'c':'color', 'd':'trail_color', // don't use single and double quotes; available: comma, but maybe that would cause trouble
             'e':'ambient', 'f':'axis', 'g':'size', 'h':'origin', 'i':'textcolor',
             'j':'direction', 'k':'linecolor', 'l':'bumpaxis', 'm':'dot_color',
             'n':'foreground', 'o':'background', 'p':'ray', 'E':'center', '#':'forward', '+':'resizable',

             // scalar attributes
             'q':'graph', 'r':'canvas', 's':'trail_radius',
             't':'visible', 'u':'opacity', 'v':'shininess', 'w':'emissive',
             'x':'make_trail', 'y':'trail_type', 'z':'interval', 'A':'pps', 'B':'retain',
             'C':'red', 'D':'green', 'E':'ccw', 'F':'blue', 'G':'length', 'H':'width', 'I':'height', 'J':'radius',
             'K':'thickness', 'L':'shaftwidth', 'M':'headwidth', 'N':'headlength', 'O':'pickable',
             'P':'coils', 'Q':'xoffset', 'R':'yoffset',
             'S':'border', 'T':'line', 'U':'box', 'V':'space', 'W':'linewidth',
             'X':'xmin', 'Y':'xmax', 'Z':'ymin', '`':'ymax',
             '~':'ctrl', '!':'shift', '@':'alt',

             // text attributes:
             '$':'text', '%':'align', '^':'caption',
             '-':'fast','&':'title', '*':'xtitle', '(':'ytitle',

             // Miscellany:
             ')':'lights', '_':'objects', '=':'bind',
             '[':'pixel_pos', ']':'texpos',
             '{':'v0', '}':'v1', ';':'v2', ':':'v3', '<':'vs', '>':'type',
             '?':'font', '/':'texture'};

    // attrsb are X in {'b': '23X....'}; ran out of easily typable one-character codes
    var attrsb = {'a':'userzoom', 'b':'userspin', 'c':'range', 'd':'autoscale', 'e':'fov',
                  'f':'normal', 'g':'data', 'h':'checked', 'i':'disabled', 'j':'selected',
                  'k':'vertical', 'l':'min', 'm':'max', 'n':'step', 'o':'value',
                  'p':'left', 'q':'right', 'r':'top', 's':'bottom', 't':'_cloneid',
                  'u':'logx', 'v':'logy', 'w':'dot', 'x':'dot_radius',
                  'y':'markers', 'z':'legend', 'A':'label','B':'delta', 'C':'marker_color',
                  'D':'size_units', 'E':'userpan', 'F':'scroll', 'G':'choices', 'H':'depth', 'I':'round',
                  'J':'name', 'K':'offset', 'L':'attach_idx', 'M':'ccw'
                };

    // methods are X in {'m': '23X....'}
    var methods = {'a':'select', 'b':'pos', 'c':'start', 'd':'stop', 'f':'clear', // unused eghijklmnopvxyzCDFAB
                   'q':'plot', 's':'add_to_trail',
                   't':'follow', 'u':'_attach_arrow', 'w':'clear_trail',
                   'G':'bind', 'H':'unbind', 'I':'waitfor', 'J':'pause', 'K':'pick',
                   'M':'delete', 'N':'capture'};

    var vecattrs = ['pos', 'up', 'color', 'trail_color', 'axis', 'size', 'origin', '_attach_arrow',
                    'direction', 'linecolor', 'bumpaxis', 'dot_color', 'ambient', 'add_to_trail', 'textcolor',
                    'foreground', 'background', 'ray', 'ambient', 'center', 'forward', 'normal',
                    'marker_color'];

    var textattrs = ['text', 'align', 'caption', 'title', 'title_align', 'xtitle', 'ytitle', 'selected', 'capture',
                     'label', 'append_to_caption', 'append_to_title', 'bind', 'unbind', 'pause', 'choices'];

    // patt gets idx and attr code; vpatt gets x,y,z of a vector
    var patt = /(\d+)(.)(.*)/;
    var vpatt = /([^,]*),([^,]*),(.*)/;
    var quadpatt = /([^,]*),([^,]*),(.*)/;
    var plotpatt = /([^,]*),([^,]*)/;

    function decode(data) {
        // data is {'cmds':list of constructors, 'attrs': list of attributes and (time-ordered) methods
        // Attribute and method lists: [ 'XiK0.0,1.0,1.0', .....] X is a or b (attributes) or m (methods)
        // i is object index, K is a key to an attribute or method in the dictionaries above
        var output = [], s, m, idx, attr, val, datatype, out, i, as, ms;
        var as = [];
        var ms = [];

        if ('attrs' in data) {
            var c = data['attrs'];
            for (i=0; i<c.length; i++) { // step through the encoded attributes and methods
                var d = c[i];
                // constructor or appendcmd not currently compressed
                var whichlist = d[0]; // 'a' or 'b' or 'm'
                var datatype = (whichlist == 'm') ? 'method' : 'attr';
                s = d.slice(1);
                m = s.match(patt);
                idx = Number(m[1]);
                if (datatype == 'attr') {
                    if (whichlist == 'a') attr = attrs[m[2]];
                    else attr = attrsb[m[2]];
                } else attr = methods[m[2]];
                if (vecattrs.indexOf(attr) > -1) {
                    val = m[3].match(vpatt);
                    val = glow.vec(Number(val[1]), Number(val[2]), Number(val[3]));
                } else if (attr == 'vs') {
                    var vs;
                    val = m[3].match(quadpatt);
                    if (val === null) {
                        val = m[3].match(vpatt);
                        vs = [Number(val[1]), Number(val[2]), Number(val[3])];
                    } else {
                        vs = [Number(val[1]), Number(val[2]), Number(val[3]), Number(val[4])];
                    }
                } else if (textattrs.indexOf(attr) > -1) {
                    if (attr == 'choices') {          // menu choices are wrapped in a list
                        val = m[3].slice(2, -2).split("', '"); // choices separated by ', '
                    } else {
                        // '\n' doesn't survive JSON transmission, so in vpython.py we replace '\n' with '<br>'
                        val = m[3].replace(/<br>/g, "\n");
                    }
                } else if (attr == 'rotate') { // angle,x,y,z,x,y,z
                    var temp = m[3];
                    val = [];
                    var first = temp.match(/([^,]*)/);
                    val.push(Number(first[1]));
                    var v1 = temp.slice(first[1].length+1);
                    m = v1.match(/([^,]*),([^,]*),([^,]*)/);
                    val.push(glow.vec(Number(m[1]), Number(m[2]), Number(m[3])));
                    var v2 = temp.slice(first[1].length + 1 + m[0].length + 1);
                    m = v2.match(vpatt);
                    val.push(glow.vec(Number(m[1]), Number(m[2]), Number(m[3])));
                } else if (attr == 'plot' || attr == 'data') {
                    val = [];
                    var start = m[1].length+1; // start of arguments
                    while (true) {
                        m = s.slice(start).match(plotpatt);
                        val.push([ Number(m[1]), Number(m[2]) ]);
                        start += m[1].length+m[2].length+2;
                        if (start > s.length) break;
                    }
                } else if (attr == 'waitfor' || attr == 'pause' || attr == 'delete') {
                    val = m[3];
                } else if (attr == 'follow') {
                    if (m[3] == 'None') val = null;
                    else val = Number(m[3]);
                } else val = Number(m[3]);
                out = {'idx':idx, 'attr':attr, 'val':val};
                if (datatype == 'attr') as.push(out);
                else ms.push(out);
            }
        }
        if (as.length > 0) data['attrs'] = as;
        else data['attrs'] = [];
        if (ms.length > 0) data['methods'] = ms;
        return data;
    }

    function fix_location(cfgx) {
        if ('location' in cfgx) {
            var loc = cfgx['location'];
            var id = loc[0];
            if (id == -1) {
                cfgx['pos'] = glow.print_anchor; // this doesn't work; throw an error in vpython.py
            } else {
                var cvs = glowObjs[id];
                var where = loc[1];
                if (where === 1) cfgx['pos'] = cvs.title_anchor;
                else cfgx['pos'] = cvs.caption_anchor;
            }
            delete cfgx['location'];
        }
        return cfgx;
    }

    function o2vec3(p) {
        return glow.vec(p[0], p[1], p[2]);
    }

    function handle_cmds(dcmds) {
        //console.log('CMDS')
        for (var icmds=0; icmds<dcmds.length; icmds++) { // constructors, and special operations such as curve.modify
            var cmd = shallow_copy(dcmds[icmds]); // copy: the caller keeps its package (see shallow_copy)
            var obj = cmd.cmd;
            var idx = cmd.idx;
            delete cmd.cmd;
            delete cmd.idx;
            var construct = (obj !== undefined);
            var method = null;
            if ('method' in cmd) {
                method = cmd['method'];
                delete cmd['method'];
            }
            var triangle_quad = ['v0', 'v1', 'v2', 'v3'];

            //assembling cfg
            var vlst = ['pos', 'color', 'size', 'axis', 'up', 'direction', 'center', 'forward', 'foreground',
                     'background', 'ambient', 'linecolor', 'dot_color', 'trail_color', 'textcolor', 'attrval',
                     'origin', 'normal', 'bumpaxis','texpos', 'start_face_color', 'end_face_color', 'marker_color',
                     'start_normal', 'end_normal'];
            if ((obj != 'gcurve') && ( obj != 'gdots' ) ) vlst.push( 'size' );
            var cfg = {};
            var objects = [];
            var attr;
            for (attr in cmd) {
                val = cmd[attr];
                if (attr === "size") {
                    if ( (obj == 'gcurve') || ( obj == 'gdots' ) ) {
                        cfg[attr] = cmd[attr];   // size is a scalar
                    } else {
                       cfg[attr] = o2vec3(val);
                    }
                } else if ( (attr == 'pos' && (obj == 'curve' || obj == 'points')) ||
                            (obj == 'extrusion' && (attr == 'path' || attr == 'color') ) ) { // only occurs in constructor
                    let ptlist = [];
                    if (val[0].length === undefined) { // a single triple [x,y,z] to convert to a vector
                        ptlist = o2vec3(val);
                    } else {
                        for (var kk = 0; kk < val.length; kk++) {
                            ptlist.push( o2vec3(val[kk]) );
                        }
                    }
                    cfg[attr] = ptlist;
                } else if (vlst.indexOf(attr) !== -1) {
                    cfg[attr] = o2vec3(val);
                } else if (triangle_quad.indexOf(attr) !== -1) {
                    cfg[attr] = glowObjs[val];
                } else if (attr === "canvas" ) {
                    cfg[attr] = glowObjs[val];
                } else if (attr === "graph" ) {
                    cfg[attr] = glowObjs[val];
                } else if (attr === "obj_idxs") {
                    var len4 = val.length;
                    if (len4 > 0) {
                        for (var k = 0; k < len4; k++) {
                            objects[k] = glowObjs[val[k]];
                        }
                    }
                } else if (attr == "lights") {
                    if (val == 'empty_list') val = [];
                    cfg[attr] = val;
                } else {
                    cfg[attr] = val;
                }
            }
            if (!construct) { // commands such as "center" (for a canvas)
                var parametric = ['splice', 'modify'];
                var val = cfg[attr];
                if (attr == 'append_to_caption' || attr == 'append_to_title' ) glowObjs[idx][attr](val);
                else if (method !== null) {
                    var npargs = 0;
                    var info;
                    if (parametric.indexOf(method) > -1) {
                        npargs = val.length - 1;
                        info = val[npargs];  // a list of dictionaries
                    } else {
                        info = val;
                    }
                    for (var j=0; j < info.length; j++) {
                        var dj = info[j];
                        for (var a in dj) {
                            if (dj[a] instanceof Array) dj[a] = o2vec3(dj[a]);
                        }
                    }
                    if ( npargs === 0 ) {
                        glowObjs[idx][method](info);
                    } else if ( method === 'modify' ) { // 1 parameter
                        glowObjs[idx][method](val[0], info[0]);
                    } else if ( method === 'splice' ) {  // 2 parameters
                        glowObjs[idx][method](val[0], val[1], info);
                    } else {
                        throw new Error('Too many parameters in '+method);
                    }
                } else glowObjs[idx][attr] = val;
                continue;
            }
            // creating the objects
            cfg.idx = idx; // reinsert idx, having looped thru all other attributes
            // triangle and quad objects should not have a canvas attribute; canvas is provided in the vertex objectsE
            if ((obj == 'triangle' || obj == 'quad') && cfg.canvas !== undefined) delete cfg.canvas;
            switch (obj) {
                case 'box':           {glowObjs[idx] = glow.box(cfg); break}
                case 'sphere':        {glowObjs[idx] = glow.sphere(cfg); break}
                case 'simple_sphere': {glowObjs[idx] = glow.simple_sphere(cfg); break}
                case 'arrow':         {glowObjs[idx] = glow.arrow(cfg); break}
                case 'cone':          {glowObjs[idx] = glow.cone(cfg); break}
                case 'cylinder':      {glowObjs[idx] = glow.cylinder(cfg); break}
                case 'helix':         {glowObjs[idx] = glow.helix(cfg); break}
                case 'pyramid':       {glowObjs[idx] = glow.pyramid(cfg); break}
                case 'ring':          {glowObjs[idx] = glow.ring(cfg); break}
                case 'curve':         {glowObjs[idx] = glow.curve(cfg); break}
                case 'points':        {glowObjs[idx] = glow.points(cfg); break}
                case 'vertex':        {glowObjs[idx] = glow.vertex(cfg); break}
                case 'triangle':      {glowObjs[idx] = glow.triangle(cfg); break}
                case 'quad':          {glowObjs[idx] = glow.quad(cfg); break}
                case 'label':         {glowObjs[idx] = glow.label(cfg); break}
                case 'ellipsoid':     {glowObjs[idx] = glow.sphere(cfg); break}
                case 'graph':     { // currently graph gives an error for non-fundamental arguments
                    delete cfg.idx;
                    glowObjs[idx] = glow.graph(cfg);
                    break
                }
                case 'gcurve':    { // currently gcurve give an error for non-fundamental arguments
                    delete cfg.idx;
                    glowObjs[idx] = glow.gcurve(cfg);
                    break
                }
                case 'gdots':     { // currently gdots give an error for non-fundamental arguments
                    delete cfg.idx;
                    glowObjs[idx] = glow.gdots(cfg);
                    break
                }
                case 'gvbars':    { // currently gvbars give an error for non-fundamental arguments
                    delete cfg.idx;
                    glowObjs[idx] = glow.gvbars(cfg);
                    break
                }
                case 'ghbars':    { // currently ghbars give an error for non-fundamental arguments
                    delete cfg.idx;
                    glowObjs[idx] = glow.ghbars(cfg);
                    break
                }
                case 'compound': {
                    if (cfg._cloneid !== undefined) {
                        var idoriginal = cfg._cloneid;
                        delete cfg._cloneid;
                        glowObjs[idx] = glowObjs[idoriginal].clone(cfg);
                    } else {
                        var obj = glowObjs[idx] = glow.compound(objects, cfg);
                        // Return computed compound pos and size to Python
                        send_compound(obj.canvas['idx'], obj.pos, obj.size, obj.up);
                    }
                    break
                }
                case 'extrusion': {
                    var obj = glowObjs[idx] = glow.extrusion(cfg);
                    // Return computed compound pos and size to Python
                    send_compound(obj.canvas['idx'], obj.pos, obj.size, obj.up);
                    break
                }
                case 'text':     {
                    if (cfg._cloneid !== undefined) {
                        var idoriginal = cfg._cloneid;
                        delete cfg._cloneid;
                        glowObjs[idx] = glowObjs[idoriginal].clone(cfg);
                    } else {
                        // Return text parameters to Python
                        var obj = glowObjs[idx] = glow.text(cfg);
                        send_compound(obj.canvas['idx'], glow.vec(obj.length, obj.descender, 0),
                                obj.__comp.size, obj.up);
                    }
                    break
                }
                case 'local_light':   {glowObjs[idx] = glow.local_light(cfg); break}
                case 'distant_light': {glowObjs[idx] = glow.distant_light(cfg); break}
                case 'canvas':        {
                    // glowcomm.js looked up Jupyter's '#glowscript' div here. The
                    // host tells us where its scene goes instead; GlowScript reads
                    // the mount point off the global __context.
                    //
                    // Two things matter. (1) __context is GlowScript's own scratch
                    // space — canvas_selected, canvas_all, print_container — so
                    // merge into it; replacing it wipes state belonging to canvases
                    // already on the page (upstream did the lookup at most once,
                    // this runs on every canvas cmd). (2) glow stores a *jQuery*
                    // object (`glowscript_container` set does $(value), and the
                    // print-area path calls container.css(...)), so a raw element
                    // has to be wrapped or the first print() throws.
                    if (container !== null) {
                        var jq = glow.$ || globalThis.$ || globalThis.jQuery;
                        var ctx = globalThis.__context || (globalThis.__context = {});
                        if (jq) ctx.glowscript_container = jq(container);
                        else {
                            if (typeof console !== 'undefined') console.warn(
                                'glowcomm_host: no jQuery found to wrap the container; ' +
                                'GlowScript expects $(container) and print() will fail');
                            ctx.glowscript_container = container;
                        }
                    }
                    glowObjs[idx] = glow.canvas(cfg);
                    glowObjs[idx]['idx'] = idx;
                    break
                }
                case 'attach_arrow':  {
                    var attrs = ['pos', 'size', 'axis', 'up', 'color'];
                    var o = glowObjs[cfg['obj']];
                    delete cfg['obj'];
                    var attr = cfg['attr'];
                    delete cfg['attr'];
                    var val = cfg['attrval'];
                    delete cfg['attrval'];
                    if (attrs.indexOf(attr) < 0) attr = '_attach_arrow';
                    o.attr = val;
                    glowObjs[idx] = glow.attach_arrow( o, attr, cfg );
                    break
                }
                case 'attach_trail': {
                    if ( typeof cfg['_obj'] === 'string' ) {
                        var o = cfg['_obj']; // the string '_func'
                    } else {
                        var o = glowObjs[cfg['_obj']];
                    }
                    delete cfg['_obj'];
                    glowObjs[idx] = glow.attach_trail(o, cfg);
                    break
                }
                case 'wtext': {
                    cfg.objName = obj;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.wtext(cfg);
                    break
                }
                case 'winput': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.winput(cfg);
                    break
                }
                case 'checkbox': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.checkbox(cfg);
                    break
                }
                case 'radio': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.radio(cfg);
                    break
                }
                case 'button': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.button(cfg);
                    break
                }
                case 'slider': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.slider(cfg);
                    break
                }
                case 'menu': {
                    cfg.objName = obj;
                    cfg.bind = control_handler;
                    cfg = fix_location(cfg);
                    glowObjs[idx] = glow.menu(cfg);
                    if (cfg['selected'] === 'None') {
                        cfg['selected'] = null;
                    }
                    break
                }
                default:
                    console.log("Unable to create object");
            }
        } // end of cmds (constructors and special data)
    }

    async function handle_methods(dmeth) {
        //console.log('METHODS')
        for (var idmeth=0; idmeth<dmeth.length; idmeth++) { // methods; cmd is ['idx':idx, 'attr':method, 'val':val]
            var cmd = dmeth[idmeth];
            var idx = cmd.idx;
            var method = cmd.attr;
            var val = cmd.val;
            var obj = glowObjs[idx];

            // glowcomm.js reads "ifif (val == 'None')" here — an upstream typo that
            // makes that file unparseable; glowcomm.html has the same line as "if".
            if (val == 'None') {
                if (method == 'delete') obj['remove']();
                else obj[method]();
            } else if (method === 'rotate') {
                obj.rotate({angle:val[0], axis:val[1], origin:val[2]});
            } else if (method === 'pos') {
                glowObjs[idx]['pos'] = val;
            } else if (method === 'add_to_trail') {
                obj['_func'] = val;
            } else if (method === '_attach_arrow') {
                obj.obj._attach_arrow = val;
            } else if (method === 'bind') {
                var evts = val.split(' ');
                for (var evt in evts) {
                    var e = evts[evt];
                    if (binds.indexOf(e) == -1)
                        throw new Error('There is no error type "'+e+'"');
                }
                obj.bind(val, process_binding);
            } else if (method === 'unbind') {
                var evts = val.split(' ');
                for (var evt in evts) {
                    var e = evts[evt];
                    if (binds.indexOf(e) == -1)
                        throw new Error('There is no error type "'+e+'"');
                }
                obj.unbind(val, process_binding);
            } else if (method === "follow") {
                if (val === null) obj.camera.follow(null);
                else obj.camera.follow(glowObjs[val]);
            } else if (method === "capture") {
                // val has the form "Tname.png" (display labels) or "Fname.png" (do not display labels)
                let TF =  (val[0] == 'T') ? true: false;
                await obj.capture(val.slice(1), TF);
            } else if (method === 'waitfor') {
                waitfor_canvas = idx;
                waitfor_options = val;
                obj.bind(waitfor_options, process_waitfor);
            } else if (method === 'pause') {
                waitfor_canvas = idx;
                waitfor_options = 'click';
                if (val.length > 0) {
                   await obj.pause(val);
                } else {
                   await obj.pause();
                }
                process_pause();
            } else if (method === 'pick') {
                var p = glowObjs[val].mouse.pick();  // wait for pick render; val is canvas
                var seg = null;
                if (p !== null) {
                    if (is_a(p, glow.curve)) seg = p.segment;
                    p = p.idx;
                }
                send_pick(val, p, seg);
            } else obj[method](val);
        }
    }

    function handle_attrs(dattrs) {
        //console.log('ATTRS')
        for (var idattrs=0; idattrs<dattrs.length; idattrs++) { // attributes; cmd is {'idx':idx, 'attr':attr, 'val':val}
            var cmd = dattrs[idattrs];
            var idx = cmd.idx;
            var obj = glowObjs[idx];
            var attr = cmd['attr'];
            var val = cmd['val'];
            var triangle_quad = ['v0', 'v1', 'v2', 'v3'];
            // vector attrs in attach_arrow have arbitrary names, so check for length 3 array instead
            if (is_a(val, glow.vec)) {
                if (attr === 'pos' && (is_a(obj, glow.points) || is_a(obj, glow.curve))) {
                    var ptlist = [];
                    for (var kk = 0; kk < val.length; kk++) {
                        ptlist.push( val[kk] );
                    }
                    obj[attr] = ptlist;
                } else {
                    obj[attr] = val;
                }
            } else if (attr == 'lights') {
                if (val == 'empty_list') val = [];
                obj[attr] = val;
            } else {
                if (triangle_quad.indexOf(attr) !== -1) {
                    obj[attr] = glowObjs[val];
                } else if (attr == 'vs') {
                    if (val.length == 3) obj['vs'] = [ glowObjs[val[0]], glowObjs[val[1]], glowObjs[val[2]] ];
                    else obj['vs'] = [ glowObjs[val[0]], glowObjs[val[1]], glowObjs[val[2]], glowObjs[val[3]] ];
                } else {
                    obj[attr] = val;
                }
            }
        } // end of attributes
    }

    // ---------------------------------------------------------------------------
    // Public surface
    // ---------------------------------------------------------------------------

    // glowcomm.js's handler(), preceded by the decode() that domessage() used to
    // do: 'trigger' is the bare keepalive handshake and carries no work.
    function handle(ops) {
        if (ops === 'trigger' || !ops) return;
        var data = decode(shallow_copy(ops));
        if (data.cmds !== undefined && data.cmds.length > 0) handle_cmds(data.cmds);
        if (data.methods !== undefined && data.methods.length > 0) handle_methods(data.methods);
        if (data.attrs !== undefined && data.attrs.length > 0) handle_attrs(data.attrs);
    }

    // Forget every object: the next scene generation reuses idx 0, 1, 2, ...
    // Queued events go with them — they name idxs that no longer mean anything —
    // and the canvas diff starts over, so the new scene's first tick reports its
    // own state rather than a delta against the old one.
    function reset() {
        glowObjs = [];
        waitfor_canvas = null;
        waitfor_options = null;
        events = [];
        last_tick = -Infinity;
        reset_canvas_state();
    }

    // reset(), plus a best-effort ask for the objects to take themselves off the
    // page. GlowScript objects use remove(); a canvas uses delete().
    function destroy() {
        for (var i = 0; i < glowObjs.length; i++) {
            var o = glowObjs[i];
            if (!o) continue;
            try {
                if (typeof o.remove === 'function') o.remove();
                else if (typeof o['delete'] === 'function') o['delete']();
            } catch (e) { /* already gone, or not removable */ }
        }
        reset();
    }

    // Test-only accessor: the internal glowObjs registry (idx -> GlowScript object).
    // Not part of the host contract — do not use it from page code.
    function _objs() { return glowObjs; }

    return { handle: handle, tick: tick, reset: reset, destroy: destroy, _objs: _objs };
}

var api = { createGlowFrontend: createGlowFrontend };
if (typeof module !== 'undefined' && module.exports) module.exports = api;
if (typeof self !== 'undefined') self.createGlowFrontend = createGlowFrontend;
