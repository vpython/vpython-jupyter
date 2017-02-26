define(["nbextensions/vpython_libraries/jquery-ui.custom.min",
        "nbextensions/vpython_libraries/glow.min"], function() {

// The following is necessary to be able to re-run programs.
// Otherwise the repeated execution of update_canvas() causes problems after klling Python.
if (timer !== undefined && timer !== null) clearTimeout(timer)

function msclock() {
    if (performance.now) return performance.now()
    else return new Date().getTime()
}
var tstart = msclock()

window.Jupyter_VPython = requirejs.s.contexts._.config.paths.nbextensions + '/vpython_data/'

function fontloading() {
    var fsans = requirejs.s.contexts._.config.paths.nbextensions + '/vpython_data/Roboto-Medium.ttf'
    opentype_load(fsans, function(err, fontrefsans) {
        if (err) throw new Error('Font ' + fsans + ' could not be loaded: ' + err)
        window.__font_sans = fontrefsans // an opentype.js Font object
        console.log('SANS-SERIF FONT LOADED')
    })
    var fserif = requirejs.s.contexts._.config.paths.nbextensions + '/vpython_data/NimbusRomNo9L-Med.otf'
    opentype_load(fserif, function(err, fontrefserif) {
        if (err) throw new Error('Font ' + fserif + ' could not be loaded: ' + err)
        window.__font_serif = fontrefserif // an opentype.js Font object
        console.log('SERIF FONT LOADED')
    })
}
fontloading()

var glowObjs = []

//scene.title.text("fps = frames/sec\n ")
// Display frames per second and render time:
//$("<div id='fps'/>").appendTo(scene.title)

function o2vec3(p) {
    "use strict";
    return vec(p[0], p[1], p[2])
}

comm = IPython.notebook.kernel.comm_manager.new_comm('glow')
comm.on_msg(handler)
console.log("comm created for glow target", comm)

var sliders = {}

function process(event) {  // mouse events:  mouseup, mousedown, mousemove, mouseenter, mouseleave, click, pause, waitfor
    "use strict";
    var evt = {event:event.event}
    var idx = event.canvas['idx']
    evt.canvas = idx
    var pos = event.pos
    evt.pos = [pos.x, pos.y, pos.z]
    evt.press = event.press
    evt.release = event.release
    evt.which = event.which
    var ray = event.canvas.mouse.ray 
    evt.ray = [ ray.x, ray.y, ray.z ]
    evt.alt = event.canvas.mouse.alt
    evt.ctrl = event.canvas.mouse.ctrl
    evt.shift = event.canvas.mouse.shift
    comm.send( {arguments: [evt]} )
}

function process_pause(event) {
    "use strict";
    return // ignore return from pause; a regular click event will follow
}

function control_handler(obj) {  // button, menu, slider, radio, checkbox
    "use strict";
    var evt = { idx: obj.idx}
    if (obj.objName === 'button') {
        evt.value = 0 
        evt.widget = 'button'
    } else if (obj.objName === 'slider') {
        evt.value = obj.value
        evt.widget = 'slider'
        sliders[obj.idx] = evt
        return
//        console.log('slider', evt.value)
    } else if (obj.objName === 'checkbox') {
        evt.value = obj.checked
        evt.widget = 'checkbox'
    } else if (obj.objName === 'radio') {
        evt.value = obj.checked
        evt.widget = 'radio'
    } else if (obj.objName === 'menu') {
        evt.value = obj.index
        evt.widget = 'menu'
    } else {
        console.log('unrecognized control', 'obj=', obj, obj.text)
    }
    comm.send( {arguments: [evt]} )
}

var timer = null
var lastpos = vec(0,0,0)
var lastray = vec(0,0,0)
var lastforward = vec(0,0,0)
var lastup = vec(0,0,0)
var lastrange = 1
var lastautoscale = true
var interval = 30 // milliseconds

function update_canvas() { // mouse location and other stuff
    "use strict";
    //var t = msclock()
    //console.log(t-tstart)
    //tstart = t
    for (var ss in sliders){
        comm.send( { arguments: [ sliders[ss] ] } )
    }
    sliders = {}
    var dosend = false
    var evt = {event:'update_canvas'}
    if (canvas.hasmouse === null || canvas.hasmouse === undefined) {
        comm.send( {arguments: [{event:'update_canvas', 'trigger':1}]} )
        return
    } 
    var cvs = canvas.hasmouse  // only way to change these values is with mouse
    var idx = cvs.idx
    evt.canvas = idx
    var pos = cvs.mouse.pos
    if (!pos.equals(lastpos)) {evt.pos = [pos.x, pos.y, pos.z]; dosend=true}
    lastpos = pos
    var ray = cvs.mouse.ray 
    if (!ray.equals(lastray)) {evt.ray = [ ray.x, ray.y, ray.z ]; dosend=true}
    lastray = ray
    // forward and range may be changed by user (and up with touch), and autoscale (by zoom)
    if (cvs.userspin) {
        var forward = cvs.forward
        if (!forward.equals(lastforward)) {
            evt.forward = [forward.x, forward.y, forward.z]
            dosend=true
        }
        lastforward = forward
        var up = cvs.up
        if (!up.equals(lastup)) {evt.up = [up.x, up.y, up.z]; dosend=true}
        lastup = up
    }
    if (cvs.userzoom) {
        var range = cvs.range
        if (range !== lastrange) {evt.range = range; dosend=true}
        lastrange = range
        var autoscale = cvs.autoscale
        if (autoscale !== lastautoscale) {evt.autoscale = autoscale; dosend=true}
        lastautoscale = autoscale
    }
    if (dosend) comm.send( {arguments: [evt]} )
    else comm.send( {arguments: [{event:'update_canvas', 'trigger':1}]} )
}

function send_pick(cvs, p, seg) {
    "use strict";
    var evt = {event: 'pick', 'canvas': cvs, 'pick': p, 'segment':seg}
    comm.send( {arguments: [evt]} ) 
}

function send_compound(cvs, pos, size) {
    "use strict";
    var evt = {event: '_compound', 'canvas': cvs, 'pos': [pos.x, pos.y, pos.z], 'size': [size.x, size.y, size.z]}
    comm.send( {arguments: [evt]} )
}

// attrs are X in {'a': '23X....'}
var attrs = {'a':'pos', 'b':'up', 'c':'color', 'd':'trail_color', // don't use single and double quotes; available: +-, 
         'e':'ambient', 'f':'axis', 'g':'size', 'h':'origin', 'i':'textcolor',
         'j':'direction', 'k':'linecolor', 'l':'bumpaxis', 'm':'dotcolor',
         'n':'foreground', 'o':'background', 'p':'ray', 'E':'center', '#':'forward',
         
         // scalar attributes
         'q':'graph', 'r':'canvas', 's':'trail_radius', 
         't':'visible', 'u':'opacity', 'v':'shininess', 'w':'emissive',  
         'x':'make_trail', 'y':'trail_type', 'z':'interval', 'A':'pps', 'B':'retain',  
         'C':'red', 'D':'green', 'F':'blue', 'G':'length', 'H':'width', 'I':'height', 'J':'radius',
         'K':'thickness', 'L':'shaftwidth', 'M':'headwidth', 'N':'headlength', 'O':'pickable',
         'P':'coils', 'Q':'xoffset', 'R':'yoffset',
         'S':'border', 'T':'line', 'U':'box', 'V':'space', 'W':'linewidth',
         'X':'xmin', 'Y':'xmax', 'Z':'ymin', '`':'ymax',
         '~':'ctrl', '!':'shift', '@':'alt',
         
         // text attributes: 
         '$':'text', '%':'align', '^':'caption', '&':'title', '*':'xtitle', '(':'ytitle',
         
         // Miscellany:
         ')':'lights', '_':'objects', '=':'bind',
         '[':'pixel_pos', ']':'texpos', 
         '{':'v0', '}':'v1', ';':'v2', ':':'v3', '<':'vs', '>':'type',
         '?':'font', '/':'texture'}
         
// attrsb are X in {'b': '23X....'}; ran out of easily typable one-character codes
var attrsb = {'a':'userzoom', 'b':'userspin', 'c':'range', 'd':'autoscale', 'e':'fov',
              'f':'normal', 'g':'data', 'h':'checked', 'i':'disabled', 'j':'selected',
              'k':'vertical', 'l':'min', 'm':'max', 'n':'step', 'o':'value',
              'p':'left', 'q':'right', 'r':'top', 's':'bottom', 't':'_cloneid'}

// methods are X in {'m': '23X....'}
var methods = {'a':'select', 'c':'start', 'd':'stop', 'f':'clear', // unused bsxyCDFghzAB
           'i':'append', 'j':'npoints', 'k':'pop', 'l':'shift', 'm':'unshift',
           'n':'slice', 'o':'splice', 'p':'modify', 'q':'plot', 's':'add_to_trail',
           't':'follow', 'u':'append_to_caption', 'v':'append_to_title', 'w':'clear_trail',
           'G':'bind', 'H':'unbind', 'I':'waitfor', 'J':'pause', 'K':'pick', 'L':'GSprint'}
         
var vecattrs = ['pos', 'up', 'color', 'trail_color', 'axis', 'size', 'origin', 'textcolor',
                'direction', 'linecolor', 'bumpaxis', 'dotcolor', 'ambient', 'add_to_trail',
                'foreground', 'background', 'ray', 'ambient', 'center', 'forward', 'normal']
                
var textattrs = ['text', 'align', 'caption', 'title', 'xtitle', 'ytitle', 'selected',
                 'append_to_caption', 'append_to_title', 'bind', 'unbind', 'pause', 'GSprint']

// patt gets idx and attr code; vpatt gets x,y,z of a vector            
var patt = /(\d+)(.)(.*)/
var vpatt = /([^,]*),([^,]*),(.*)/
var plotpatt = /([^,]*),([^,]*)/

function decode(data) { // [ [{'a': '3c0.0,1.0,1.0'}], .....] or can be a method 'm'
    "use strict";
    var output = [], s, m, idx, attr, val, datatype, out
    for (var i in data) { // step through the list of dictionaries
        var d = data[i]
        // constructor or appendcmd not currently compressed; complex methods or attributes:
        if (d['_pass'] !== undefined) {
            delete d['_pass']
            output.push(d)
            continue
        } else if (d['a'] !== undefined) { // attribute setter (attrs)
            s = d['a']
            datatype = 'attr'
        } else if (d['b'] !== undefined) { // attribute setter (attrsb)
            s = d['b']
            datatype = 'attr'
        } else if (d['m'] !== undefined) { // method
            s = d['m']
            datatype = 'method'
        }
        m = s.match(patt)
        idx = Number(m[1])
        if (datatype == 'attr') {
            if (d['a'] !== undefined) attr = attrs[m[2]]
            else attr = attrsb[m[2]]
        } else attr = methods[m[2]]
        if (vecattrs.indexOf(attr) > -1) {
            val = m[3].match(vpatt)
            val = [Number(val[1]), Number(val[2]), Number(val[3])]
        } else if (textattrs.indexOf(attr) > -1) {
            val = m[3]
        } else if (attr == 'plot' || attr == 'data') {
            val = []
            var start = m[1].length+1 // start of arguments
            while (true) {
                m = s.slice(start).match(plotpatt)
                val.push([ Number(m[1]), Number(m[2]) ])
                start += m[1].length+m[2].length+2
                if (start > s.length) break
            }
        } else val = Number(m[3])
        out = {'idx':idx, 'val':val}
        out[datatype] = attr
        //console.log('---- out ----')
        //for (var a in out) console.log(a, out[a])
        output.push(out)
    }
    return output
}

function fix_location(cfgx) {
    "use strict";
    if ('location' in cfgx) {
        if (cfgx['location'] === 1) {cfgx['pos'] = cfgx['canvas'].title_anchor}
        else if (cfgx['location'] === 2) {cfgx['pos'] = cfgx['canvas'].caption_anchor}
        else if (cfgx['location'] === 3) {cfgx['pos'] = print_anchor}
        delete cfgx['location']
    }
    return cfgx
}

function handler(msg) {
    "use strict";
    var data = msg.content.data
    //console.log('glow msg', msg, msg.content)
    //console.log('glow', data, data.length)
    //console.log(data)
    data = decode(data)
    //console.log('JSON ' + JSON.stringify(data))
    if (data[0]['trigger'] !== undefined) {
        if (timer !== null) clearTimeout(timer)
        timer = setTimeout(update_canvas, interval)
        return
    }

    if (data.length > 0) {
        var i, j, k, cmd, attr, cfg, cfg2, vertdata, len2, len3, attr2, elems, elen, len4, S, b, vlst
        var triangle_quad, objects, cvsParams
        var len = data.length
        triangle_quad = ['v0', 'v1', 'v2', 'v3']
        for (i = 0; i < len; i++) {
            cmd = data.shift()
//            console.log('\n\n-------------------')
//            console.log('glowwidget0', cmd.idx, cmd.attr, cmd.val, cmd.cmd, cmd.method)
            if (cmd.cmd === undefined) { //  not a constructor
                if (cmd.idx !== undefined) {
                    if (cmd.attr !== undefined) {      
//  vector attrs in attach_arrow have arbitrary names, so check for length 3 array instead
                        if (cmd.val instanceof Array && cmd.val.length === 3) {
                            if (cmd.attr === 'pos' && (cmd.cmd === 'points' || cmd.cmd === 'curve')) {
                                var ptlist = []
                                for (var kk = 0; kk < cmd.val.length; kk++) {
                                    ptlist.push( o2vec3(cmd.val[kk]) )
                                }
                                glowObjs[cmd.idx][cmd.attr] = ptlist                                
                            } else {
                                var v = o2vec3(cmd.val)
                                // VPython interactions between axis and size are dealt with in vpython.py
                                if (cmd.attr === 'axis') {
                                    if (glowObjs[cmd.idx] instanceof arrow) {
                                        glowObjs[cmd.idx]['axis_and_length'] = v
                                    } else {
                                        glowObjs[cmd.idx][cmd.attr] = v
                                    }
                                } else if (cmd.attr === 'size') {
                                    glowObjs[cmd.idx][cmd.attr] = v
                                } else {
                                    glowObjs[cmd.idx][cmd.attr] = v
                                }
                            }
                        } else if (cmd.attr == 'lights') {
                            if (cmd.val == 'empty_list') cmd.val = []
                            glowObjs[cmd.idx][cmd.attr] = cmd.val
                        } else {
                            if (triangle_quad.indexOf(cmd.attr) !== -1) {
                                glowObjs[cmd.idx][cmd.attr] = glowObjs[cmd.val]
                            } else { 
                                glowObjs[cmd.idx][cmd.attr] = cmd.val
                            }
                        }
                    }
                    if (cmd.method !== undefined) {
                        //console.log('cmd.method', cmd.idx, cmd.method, cmd.val)
                        var parametric = ['splice', 'modify']
                        var val = cmd.val
                        if (cmd.method == 'GSprint') {
                            GSprint(cmd.val)
                        } else if (val == 'None') {
                            if (cmd.method == 'delete') glowObjs[cmd.idx]['remove']()
                            else glowObjs[cmd.idx][cmd.method]()
                        } else if ((cmd.method === 'title' || cmd.method === 'caption') && glowObjs[cmd.idx] instanceof canvas) {
                            glowObjs[cmd.idx][cmd.method] = cmd.val
                        } else if ((cmd.method === 'append_to_title' || cmd.method === 'append_to_caption') && glowObjs[cmd.idx] instanceof canvas) {
                            glowObjs[cmd.idx][cmd.method](cmd.val)
                        } else if (cmd.method === 'add_to_trail') {
                            glowObjs[cmd.idx].pos = o2vec3(cmd.val)
                        } else if (cmd.method === 'bind') {
                            glowObjs[cmd.idx].bind(cmd.val, process)
                        } else if (cmd.method === 'unbind') {
                            glowObjs[cmd.idx].unbind(cmd.val, process)                     
                        } else if (cmd.method === "follow") {
                            glowObjs[cmd.idx].camera.follow(glowObjs[cmd.val])
                        } else if (cmd.method === 'pause') {
                            if (cmd.val.length > 0) {
                               glowObjs[cmd.idx].pause(cmd.val, process_pause) 
                            } else {
                               glowObjs[cmd.idx].pause(process_pause) 
                            }
                        } else if (cmd.method === 'pick') {
                            var p = glowObjs[cmd.val].mouse.pick()   // wait for pick render; cmd.val is canvas
                            var seg = null
                            if (p !== null) {
                                if (p instanceof curve) seg = p.segment
                                p = p.idx                                
                            }
                            send_pick(cmd.val, p, seg)
                        } else {
                            var npargs = 0
                            var info
                            if (parametric.indexOf(cmd.method) > -1) {
                                npargs = val.length - 1
                                info = val[npargs]  // a list of dictionaries
                            } else {
                                info = val
                            }
                            for (var j=0; j < info.length; j++) {
                                var d = info[j]
                                for (var a in d) {
                                    if (d[a] instanceof Array) d[a] = o2vec3(d[a])
                                } 
                            }
                            if ( npargs === 0 ) {
                                glowObjs[cmd.idx][cmd.method](info)
                            } else if ( cmd.method === 'modify' ) { // 1 parameter
                                glowObjs[cmd.idx][cmd.method](val[0], info[0])
                            } else if ( cmd.method === 'splice' ) {  // 2 parameters
                                glowObjs[cmd.idx][cmd.method](val[0], val[1], info)
                            } else {
                                throw new Error('Too many parameters in '+cmd.method)
                            }
                        }                         
                    }
                }
            } else { // processing a constructor           
                /*
                if (cmd.cmd !== 'heartbeat') {
                    console.log('glow', data, data.length)
                    console.log('JSON ' + JSON.stringify(data))
                }
                */
                //assembling cfg
//                console.log('assembling cfg', cmd.cmd, typeof cmd.attrs, cmd.attrs) //**************
//                for (var i in cmd.attrs) { console.log(cmd.attrs[i]) }
                if (cmd.attrs !== undefined) {
                     vlst = ['pos', 'color', 'axis', 'up', 'direction', 'center', 'forward', 'foreground',
                             'background', 'ambient', 'linecolor', 'dot_color', 'trail_color', 'textcolor',
                             'origin', 'normal', 'bumpaxis','texpos', 'start_face_color', 'end_face_color']
                    if ((cmd.cmd != 'gcurve') && ( cmd.cmd != 'gdots' ) ) {
                        vlst.push( 'size' )
                    }

                    len2 = cmd.attrs.length
                    cfg = {}
                    objects = []
                    for (j = 0; j < len2; j++) {
                        attr = cmd.attrs.shift()
                        if (attr.attr === "size") {
                            if ( (cmd.cmd == 'gcurve') || ( cmd.cmd == 'gdots' ) ) {
                                cfg[attr.attr] = attr.value   // size is a scalar
                            } else {
                               cfg[attr.attr] = o2vec3(attr.value)
                            }                            
                        } else if ( (attr.attr == 'pos' && (cmd.cmd == 'curve' || cmd.cmd == 'points')) ||
                                    (attr.attr == 'path' && cmd.cmd == 'extrusion') ) {
                            var ptlist = []
                            for (var kk = 0; kk < attr.value.length; kk++) {
                                ptlist.push( o2vec3(attr.value[kk]) )
                            }
                            cfg[attr.attr] = ptlist                          
                        } else if (attr.attr === "axis" && cmd.cmd == 'arrow') {
                            cfg['axis_and_length'] = o2vec3(attr.value) 
                        } else if (vlst.indexOf(attr.attr) !== -1) {
                            cfg[attr.attr] = o2vec3(attr.value)
                        } else if (triangle_quad.indexOf(attr.attr) !== -1) {
                            cfg[attr.attr] = glowObjs[attr.value]
                        } else if (attr.attr === "canvas" ) {
                            cfg[attr.attr] = glowObjs[attr.value]
                        } else if (attr.attr === "graph" ) {
                            cfg[attr.attr] = glowObjs[attr.value]
                        } else if (attr.attr === "obj_idxs") {
                            len4 = attr.value.length
                            if (len4 > 0) {
                                for (k = 0; k < len4; k++) {
                                    objects[k] = glowObjs[attr.value[k]]
                                }
                            }
                        } else if (attr.attr == "lights") {
                            if (attr.value == 'empty_list') attr.value = []
                            cfg[attr.attr] = attr.value
                        } else {
                            cfg[attr.attr] = attr.value
                            // console.log(attr.attr, attr.value)
                        }
                    }
                    //making the objects
                    if (cmd.idx !== undefined) {
                        cfg.idx = cmd.idx
                        if (cmd.cmd === 'box') {
                            glowObjs[cmd.idx] = box(cfg)
                        } else if (cmd.cmd === 'sphere') {
                            glowObjs[cmd.idx] = sphere(cfg)
                        } else if (cmd.cmd === 'arrow') {
                            glowObjs[cmd.idx] = arrow(cfg)
                        } else if (cmd.cmd === 'cone') {
                            glowObjs[cmd.idx] = cone(cfg)
                        } else if (cmd.cmd === 'cylinder') {
                            glowObjs[cmd.idx] = cylinder(cfg)
                        } else if (cmd.cmd === 'helix') {
                            glowObjs[cmd.idx] = helix(cfg)
                        } else if (cmd.cmd === 'pyramid') {
                            glowObjs[cmd.idx] = pyramid(cfg)
                        } else if (cmd.cmd === 'ring') {
                            glowObjs[cmd.idx] = ring(cfg)
						} else if  (cmd.cmd === 'gcurve') {
                            delete cfg.idx // currently gcurve give an error for non-fundamental arguments
							glowObjs[cmd.idx] = gcurve(cfg)
						} else if  (cmd.cmd === 'gdots') {
                            delete cfg.idx // currently gdots give an error for non-fundamental arguments
							glowObjs[cmd.idx] = gdots(cfg)
						} else if  (cmd.cmd === 'gvbars') {
                            delete cfg.idx // currently gvbars give an error for non-fundamental arguments
							glowObjs[cmd.idx] = gvbars(cfg)
						} else if  (cmd.cmd === 'ghbars') {
                            delete cfg.idx // currently ghbars give an error for non-fundamental arguments
							glowObjs[cmd.idx] = ghbars(cfg)
                        } else if (cmd.cmd == 'graph') {
                            delete cfg.idx // currently graph give an error for non-fundamental arguments
                            glowObjs[cmd.idx] = vp_graph(cfg)
                            //glowObjs[cmd.idx]['idx'] = cmd.idx // should handle this in a more principled way
                        } else if (cmd.cmd === 'curve') {
                            glowObjs[cmd.idx] = curve(cfg)
                            glowObjs[cmd.idx]['idx'] = cmd.idx // should handle this in a more principled way
                        } else if (cmd.cmd === 'points') {
                            glowObjs[cmd.idx] = points(cfg)
                            glowObjs[cmd.idx]['idx'] = cmd.idx // should handle this in a more principled way
                        } else if (cmd.cmd === 'vertex') {
                            glowObjs[cmd.idx] = vertex(cfg)
                        } else if (cmd.cmd === 'triangle') {
                            glowObjs[cmd.idx] = triangle(cfg)
                        } else if (cmd.cmd === 'quad') {
                            glowObjs[cmd.idx] = quad(cfg)
                        } else if (cmd.cmd === 'push') {
                            glowObjs[cmd.idx].push(cfg)
                        } else if (cmd.cmd === 'label') {
                            glowObjs[cmd.idx] = label(cfg)
                        } else if (cmd.cmd === 'ellipsoid') {
                            glowObjs[cmd.idx] = sphere(cfg)
                        } else if (cmd.cmd === 'extrusion') {
                            var obj = glowObjs[cmd.idx] = extrusion(cfg)
                            // Return computed compound pos and size to Python
                            send_compound(obj.canvas['idx'], obj.pos, obj.size)
                        } else if (cmd.cmd === 'text') {
                            if (cfg._cloneid !== undefined) {
                                var idoriginal = cfg._cloneid
                                delete cfg._cloneid
                                glowObjs[cmd.idx] = glowObjs[idoriginal].clone(cfg)
                            } else {
                                var obj = glowObjs[cmd.idx] = text(cfg)
                                send_compound(obj.canvas['idx'], vec(obj.length, obj.descender, 0), vec(0,0,0))
                            }
                        } else if (cmd.cmd === 'rotate') {
                            glowObjs[cmd.idx].rotate(cfg)
                        } else if (cmd.cmd === 'local_light') {
                            glowObjs[cmd.idx] = local_light(cfg)
                        } else if (cmd.cmd === 'distant_light') {
                            glowObjs[cmd.idx] = distant_light(cfg)
                        } else if (cmd.cmd === 'compound') {
                            if (cfg._cloneid !== undefined) {
                                var idoriginal = cfg._cloneid
                                delete cfg._cloneid
                                obj = glowObjs[cmd.idx] = glowObjs[idoriginal].clone(cfg)
                            } else {
                                glowObjs[cmd.idx] = compound(objects, cfg)
                                var obj = glowObjs[cmd.idx]
                                // Return computed compound pos and size to Python
                                send_compound(obj.canvas['idx'], obj.pos, obj.size)
                            }
                        } else if (cmd.cmd === 'canvas') {
                            glowObjs[cmd.idx] = canvas(cfg)
                            glowObjs[cmd.idx]['idx'] = cmd.idx
                                // Display frames per second and render time:
                                //$("<div id='fps'/>").appendTo(glowObjs[cmd.idx].title)
                        } else if (cmd.cmd === 'attach_arrow') {
                            var obj = glowObjs[cfg['_obj']]
                            delete cfg['_obj']
                            var attr = cfg['_attr']
                            delete cfg['_attr']
                            glowObjs[cmd.idx] = attach_arrow( obj, attr, cfg )
                        } else if (cmd.cmd === 'attach_trail') {
                            if ( typeof cfg['_obj'] === 'string' ) {
                                var obj = cfg['_obj']
                            } else {
                                var obj = glowObjs[cfg['_obj']]
                            }
                            delete cfg['_obj'] 
                            glowObjs[cmd.idx] = attach_trail(obj, cfg)
                        } else if (cmd.cmd === 'checkbox') {
                            cfg.objName = cmd.cmd
                            cfg.bind = control_handler
                            cfg = fix_location(cfg)
                            glowObjs[cmd.idx] = checkbox(cfg)
                        } else if (cmd.cmd === 'radio') {
                            cfg.objName = cmd.cmd
                            cfg.bind = control_handler
                            cfg = fix_location(cfg)
                            glowObjs[cmd.idx] = radio(cfg)
                        } else if (cmd.cmd === 'button') {
                            cfg.objName = cmd.cmd
                            cfg.bind = control_handler
                            cfg = fix_location(cfg)
                            glowObjs[cmd.idx] = button(cfg) 
                        } else if (cmd.cmd === 'menu') {
                            cfg.objName = cmd.cmd
                            cfg.bind = control_handler
                            cfg = fix_location(cfg)
                            if (cfg['selected'] === 'None') {
                                cfg['selected'] = null                              
                            } 
                            glowObjs[cmd.idx] = menu(cfg)
                        } else if (cmd.cmd === 'slider') {
                            cfg.objName = cmd.cmd
                            cfg.bind = control_handler
                            cfg = fix_location(cfg)
                            glowObjs[cmd.idx] = slider(cfg)

                        } else {
                            console.log("Unrecognized Object")
                        }
                    } else {
                        console.log("Unable to create object, idx attribute is not provided")
                    }
                }
                if (cmd.cmd === 'redisplay') {
                    var c = document.getElementById(cmd.sceneId)
                    if (c !== null) {
                        var scn = "#" + cmd.sceneId
                        glowObjs[cmd.idx].sceneclone = $(scn).clone(true,true)
                        //document.getElementById('glowscript2').appendChild(c)
                        //document.getElementById('glowscript2').replaceWith(c)
                        $('#glowscript2').replaceWith(c)
                        c = document.getElementById(cmd.sceneId)
                        var cont = scn + " .glowscript"
                        window.__context = { glowscript_container:    $(cont) }
                    } else {
                        window.__context = { glowscript_container: $("#glowscript").removeAttr("id") }                    
                        var newcnvs = canvas()
                        for (var obj in glowObjs[cmd.idx].objects) {
                            var o = glowObjs[cmd.idx].objects[obj]
                            if ((o.constructor.name !== 'curve') && (o.constructor.name !== 'points')) {
                                glowObjs[o.gidx] = o.clone({canvas: newcnvs})
                                var olen = newcnvs.objects.length
                                if (olen > 0) {
                                    newcnvs.objects[olen - 1].gidx = o.gidx
                                }
                            }
                        }
                        glowObjs[cmd.idx] = newcnvs
                        $("#glowscript2").attr("id",cmd.sceneId)
                    }
                } else if (cmd.cmd === 'delete') {
                    b = glowObjs[cmd.idx]
                    //console.log("delete : ",cmd.idx)
                    if ((b !== null) || (b.visible !== undefined)) {
                        b.visible = false
                    }
                    glowObjs[cmd.idx] = null
                } else if (cmd.cmd === 'heartbeat') {
                    //console.log("heartbeat")
                } else if (cmd.cmd === 'debug') {
                    console.log("debug : ", cmd)
                }
            }
        }
    }
    if (timer === null) update_canvas()
};
console.log("end of glowcomm");

});