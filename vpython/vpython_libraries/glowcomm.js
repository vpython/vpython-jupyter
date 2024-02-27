define(["base/js/utils",
        "nbextensions/vpython_libraries/plotly.min",
        "nbextensions/vpython_libraries/glow.min",
        "nbextensions/vpython_libraries/jquery-ui.custom.min"], function(utils, Plotly) {

var comm
var ws = null
var isopen = false

window.Plotly = Plotly

console.log('START OF GLOWCOMM JS')

IPython.notebook.kernel.comm_manager.register_target('glow',
    function(commChannel, msg) {
        // commChannel is the frontend comm instance
        // msg is the comm_open message, which can carry data
        comm = commChannel
        // Register handlers for later messages:
        comm.on_msg(onmessage);
        comm.on_close(function(msg) {console.log("glow comm channel closed")});
		
        if (msg.content.data.wsport !== undefined) {
           // create websocket instance
           var port = msg.content.data.wsport
           var uri = msg.content.data.wsuri
           var loc = document.location, new_uri, url;
		
           // Get base URL of current notebook server
           var base_url = utils.get_body_data('baseUrl');
           // Construct URL of our proxied service
           var service_url = base_url + 'proxy/' + port + uri;

           if (loc.protocol === "https:") {
              new_uri = "wss:";
           } else {
              new_uri = "ws:";
           }
           if (document.location.hostname.includes("localhost")){
              url = "ws://localhost:" + port + uri;
           }
           else {
              new_uri += '//' + document.location.host + service_url;
              url = new_uri
           }
           ws = new WebSocket(url);
           ws.binaryType = "arraybuffer";
           
            // Handle incoming websocket message callback
            ws.onmessage = function(evt) {
                console.log("WebSocket Message Received: " + evt.data)
            };
 
            // Close Websocket callback
            ws.onclose = function(evt) {
                ws = null
                isopen = false
                console.log("***WebSocket Connection Closed***");
            };
 
            // Open Websocket callback
            ws.onopen = function(evt) {
                isopen = true
                console.log("***WebSocket Connection Opened***");
            };
        }
 });

var datadir = requirejs.s.contexts._.config.paths.nbextensions + '/vpython_data/'
window.Jupyter_VPython = datadir // prefix used by glow.min.js for textures

function fontloading() {
    "use strict";
	// override the fontloading url's in the GlowScript library
	if (window.__font_sans === undefined) {
        var fsans = datadir+'Roboto-Medium.ttf'
        opentype_load(fsans, function(err, fontrefsans) {
            if (err) {
                throw new Error('Font ' + fsans + ' could not be loaded: ' + err)
            } else {
                window.__font_sans = fontrefsans // an opentype.js Font object
                console.log('SANS-SERIF FONT LOADED')
            }
        })
    }
	if (window.__font_serif === undefined) {
        var fserif = datadir+'NimbusRomNo9L-Med.otf'
        opentype_load(fserif, function(err, fontrefserif) {
            if (err) {
                throw new Error('Font ' + fserif + ' could not be loaded: ' + err)
            } else {
                window.__font_serif = fontrefserif // an opentype.js Font object
                console.log('SERIF FONT LOADED')
            }
        })
    }
}
fontloading()

// The following machinery makes sure the fonts are loaded before the user program starts.
// Otherwise there are problems when user program tries to create a 3D text object and
// the fonts aren't yet available. The Python code has to wait for the text object to be
// created before proceeding (because Python needs the size etc. of the object), but
// this file can't create the object until the fonts have been loaded. So both Python and
// JavaScript could end up paralyzed due to lack of the normal messaging back and forth.
var firstcall = true
var firstmsg

function checkloading() {
    "use strict";
    if (window.__font_sans === undefined || window.__font_serif === undefined) {
        setTimeout(checkloading,0)
    } else {
        domessage(firstmsg)
    }
}

function domessage(msg) {
    "use strict";
    if (timer !== null) clearTimeout(timer)
    var t1 = msclock()
    var data = msg.content.data
    if (data != 'trigger') {
        var msg = decode(data)
        handler(msg)
    }
    var t2 = msclock()
    var dt = Math.floor(t1+interval-t2) // attempt to keep the time between renders constant
    if (dt < 15) dt = 0     // becaause setTimeout is inaccurate for small dt's
    timer = setTimeout(send, dt)
}

// vpython.py calls onmessage, which responds through domessage, using send
// Both vpython.py and this file are kept alive by sending messages back and forth.
function onmessage(msg) {
    "use strict";
    if (firstcall) {
        firstcall = false
        firstmsg = msg
        checkloading()
    } else {
        domessage(msg)
    }
}

// The following is necessary to be able to re-run programs.
// Otherwise the repeated execution of update_canvas() causes problems after killing Python.
if (timer !== undefined && timer !== null) clearTimeout(timer)

function send() { // periodically send events and update_canvas and request object update
    "use strict";
	var update = update_canvas()
	if (update !== null) events = events.concat(update)
	if (events.length === 0) events = [{event:'update_canvas', 'trigger':1}]
	if (ws && isopen) {
		var msg = JSON.stringify(events)
		ws.send(msg)
	} else if (comm) {
	     comm.send( events )
    }
	events = []
}

// *************************************************************************************************** //
// THE REST OF THIS FILE IS NEARLY IDENTICAL IN glowcomm.html AND glowcomm.js AND glowcommlab.js //

// Should eventually have glowcomm.html, glowcom.js, and glowcommlab.js all import this common component.

window.__GSlang = "vpython" 

function msclock() {
    "use strict";
    if (performance.now) return performance.now()
    else return new Date().getTime()
}

var tstart = msclock()

var events = [] // collects all events prior to 33 ms (or more) after previous send to server

var timer = null
var lastpos = vec(0,0,0)
var lastray = vec(0,0,0)
var lastforward = vec(0,0,0)
var lastup = vec(0,0,0)
var lastcenter = vec(0,0,0)
var lastrange = 1
var lastautoscale = true
var lastsliders = {}
var lastkeysdown = []
var interval = 17 // milliseconds

function update_canvas() { // mouse location and other stuff
    "use strict";
	var dosend = false
    if (canvas.hasmouse !== null && canvas.hasmouse !== undefined) {
		var evt = {event:'update_canvas'}
		var cvs = canvas.hasmouse  // only way to change these values is with mouse
		var idx = cvs.idx
		evt.canvas = idx
		var pos = cvs.mouse.pos
		if (!pos.equals(lastpos)) {evt.pos = [pos.x,pos.y,pos.z]; dosend=true}
		lastpos = pos
		var ray = cvs.mouse.ray 
		if (!ray.equals(lastray)) {evt.ray = [ray.x,ray.y,ray.z]; dosend=true}
		lastray = ray

		var k = keysdown()
		var test = true // assume keysdown() is same as lastkeysdown
		if (k.length !== lastkeysdown.length) test = false
		else {
			for (var i=0; i<k.length; i++) {
				if (k[i] !== lastkeysdown[i]) {
					test = false
					break
				}
			}
		}
		if (!test) {
			evt.keysdown = lastkeysdown = k
			dosend = true
		}

		// forward and range may be changed by user (and up with touch), and autoscale (by zoom)
		if (cvs.userspin) {
			var forward = cvs.forward
			if (!forward.equals(lastforward)) {
				evt.forward = [forward.x,forward.y,forward.z]
				dosend=true
			}
			lastforward = forward
			var up = cvs.up
			if (!up.equals(lastup)) {
                evt.up = [up.x,up.y,up.z]
                dosend=true
            }
			lastup = up
		}
        if (cvs.userpan) {
            var center = cvs.center
            if (!center.equals(lastcenter)) {
                evt.center = [center.x,center.y,center.z]
                dosend=true
            }
            lastcenter = center
        }
		if (cvs.userzoom) {
			var range = cvs.range
			if (range !== lastrange) {evt.range=range; dosend=true}
			lastrange = range
			var autoscale = cvs.autoscale
			if (autoscale !== lastautoscale) {evt.autoscale = autoscale; dosend=true}
			lastautoscale = autoscale
		}
		if (dosend) evt = [evt]
	}
	var output_sliders = []
    for (var ss in sliders){
		var ev = sliders[ss]
		if (ss in lastsliders && ev.value !== lastsliders[ss].value)
			output_sliders.push(ev) //avoid sending an unchnaged slider value
		lastsliders[ss] = ev
    }
	if (output_sliders.length > 0) {
		if (dosend) evt = evt.concat(output_sliders)
		else evt = output_sliders
		dosend = true
	}
    if (dosend) return evt
	else return null
}

/*
var request = new XMLHttpRequest()

function send_to_server(data, callback) { // send to HTTP server
	var data= JSON.stringify(data)
	request.open('get', data, true)
    request.responseType = 'json'
	request.onload = function() {
		if (request.status !== 200) {
			return callback('Error in requesting data: '+request.statusText)
		}
		callback(request.response)
	}
	request.send()
}

function ok(req) { ; }
*/

function send_pick(cvs, p, seg) {
    "use strict";
    var evt = {event: 'pick', 'canvas': cvs, 'pick': p, 'segment':seg}
	events.push(evt)
}

function send_compound(cvs, pos, size, up) {
    "use strict";
    var evt = {event: '_compound', 'canvas': cvs, 'pos': [pos.x, pos.y, pos.z], 
        'size': [size.x, size.y, size.z], 'up': [up.x, up.y, up.z]}
	events.push(evt)
}

var waitfor_canvas = null
var waitfor_options = null
 // possible event types to bind:
var binds = ['mousedown', 'mouseup', 'mousemove', 'click', 'mouseenter', 'mouseleave',
			 'keydown', 'keyup', 'redraw', 'draw_complete', 'resize']

function process(event) {
	// mouse events:  mouseup, mousedown, mousemove, mouseenter, mouseleave, click
    // key events: keydown, keyup
	// other: resize
    "use strict";
    var etype = event.type
	var evt = {event:etype}
    var idx = event.canvas['idx']
    evt.canvas = idx
	if (etype != 'resize') {
        if (etype.slice(0,3) == 'key') {
            evt.key = event.key
            evt.which = event.which
            evt.alt = event.alt
            evt.ctrl = event.ctrl
            evt.shift = event.shift
        } else {
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
        }
	} else {
		evt.width = event.canvas.width
		evt.height = event.canvas.height
	}
	if ('bind' in event) evt.bind = true
	events.push(evt)
}

function process_pause() {
    "use strict";
    // come here on a pause; must mock up event (pause returns null)
    var cvs = glowObjs[waitfor_canvas]
    var evt = {event:'click'}
    evt.canvas = waitfor_canvas
    var pos = cvs.mouse.pos
    evt.pos = [pos.x, pos.y, pos.z]
    evt.press = false
    evt.release = true
    evt.which = 1
    var ray = cvs.mouse.ray 
    evt.ray = [ ray.x, ray.y, ray.z ]
    evt.alt = cvs.mouse.alt
    evt.ctrl = cvs.mouse.ctrl
    evt.shift = cvs.mouse.shift
    events.push(evt)
}

function process_waitfor(event) {
    "use strict";
    // come here on a waitfor
    glowObjs[waitfor_canvas].unbind(waitfor_options, process_waitfor)
    process(event)
}

function process_binding(event) { // event associated with a previous bind command
	"use strict";
    event.bind = true
	process(event)
}

var sliders = {}

function control_handler(obj) {  // button, menu, slider, radio, checkbox, winput
    "use strict";
    var evt = {idx: obj.idx}
    if (obj.objName === 'button') {
        evt.value = 0 
        evt.widget = 'button'
    } else if (obj.objName === 'slider') {
		// sliders are special; we want to transmit not all changes
		//    but a sample taken at render times
        evt.value = obj.value
        evt.widget = 'slider'
        sliders[obj.idx] = evt
		return
    } else if (obj.objName === 'checkbox') {
        evt.value = obj.checked
        evt.widget = 'checkbox'
    } else if (obj.objName === 'radio') {
        evt.value = obj.checked
        evt.widget = 'radio'
    } else if (obj.objName === 'menu') {
        evt.value = obj.index
        evt.widget = 'menu'
    } else if (obj.objName === 'winput') {
        evt.text = obj.text
        evt.value = obj.number
        evt.widget = 'winput'
    } else {
        console.log('unrecognized control', 'obj=', obj, obj.text)
    }
	//send_to_server(evt, ok)
	events.push(evt)
}

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
         '?':'font', '/':'texture'}
         
// attrsb are X in {'b': '23X....'}; ran out of easily typable one-character codes
var attrsb = {'a':'userzoom', 'b':'userspin', 'c':'range', 'd':'autoscale', 'e':'fov',
              'f':'normal', 'g':'data', 'h':'checked', 'i':'disabled', 'j':'selected',
              'k':'vertical', 'l':'min', 'm':'max', 'n':'step', 'o':'value',
              'p':'left', 'q':'right', 'r':'top', 's':'bottom', 't':'_cloneid',
              'u':'logx', 'v':'logy', 'w':'dot', 'x':'dot_radius', 
              'y':'markers', 'z':'legend', 'A':'label','B':'delta', 'C':'marker_color',
              'D':'size_units', 'E':'userpan', 'F':'scroll', 'G':'choices', 'H':'depth', 'I':'round',
			  'J':'name', 'K':'offset', 'L':'attach_idx', 'M':'ccw'
			}

// methods are X in {'m': '23X....'}
var methods = {'a':'select', 'b':'pos', 'c':'start', 'd':'stop', 'f':'clear', // unused eghijklmnopvxyzCDFAB
			   'q':'plot', 's':'add_to_trail',
               't':'follow', 'u':'_attach_arrow', 'w':'clear_trail',
               'G':'bind', 'H':'unbind', 'I':'waitfor', 'J':'pause', 'K':'pick', 
		       'M':'delete', 'N':'capture'}
         
var vecattrs = ['pos', 'up', 'color', 'trail_color', 'axis', 'size', 'origin', '_attach_arrow',
                'direction', 'linecolor', 'bumpaxis', 'dot_color', 'ambient', 'add_to_trail', 'textcolor',
                'foreground', 'background', 'ray', 'ambient', 'center', 'forward', 'normal',
                'marker_color']
                
var textattrs = ['text', 'align', 'caption', 'title', 'title_align', 'xtitle', 'ytitle', 'selected', 'capture',
                 'label', 'append_to_caption', 'append_to_title', 'bind', 'unbind', 'pause', 'choices']

// patt gets idx and attr code; vpatt gets x,y,z of a vector            
var patt = /(\d+)(.)(.*)/
var vpatt = /([^,]*),([^,]*),(.*)/
var quadpatt = /([^,]*),([^,]*),(.*)/
var plotpatt = /([^,]*),([^,]*)/

function decode(data) { 
    "use strict";
	// data is {'cmds':list of constructors, 'attrs': list of attributes and (time-ordered) methods
	// Attribute and method lists: [ 'XiK0.0,1.0,1.0', .....] X is a or b (attributes) or m (methods)
	// i is object index, K is a key to an attribute or method in the dictionaries above
    var output = [], s, m, idx, attr, val, datatype, out, i, as, ms
	var as = []
	var ms = []
	
	if ('attrs' in data) {
		var c = data['attrs']
		for (i=0; i<c.length; i++) { // step through the encoded attributes and methods
			var d = c[i]
			// constructor or appendcmd not currently compressed
			var whichlist = d[0] // 'a' or 'b' or 'm'
			var datatype = (whichlist == 'm') ? 'method' : 'attr'
			s = d.slice(1)
			m = s.match(patt)
			idx = Number(m[1])
			if (datatype == 'attr') {
				if (whichlist == 'a') attr = attrs[m[2]]
				else attr = attrsb[m[2]]
			} else attr = methods[m[2]]
			if (vecattrs.indexOf(attr) > -1) {
				val = m[3].match(vpatt)
				val = vec(Number(val[1]), Number(val[2]), Number(val[3]))
            } else if (attr == 'vs') {
                var vs
                val = m[3].match(quadpatt)
                if (val === null) {
                    val = m[3].match(vpatt)
                    vs = [Number(val[1]), Number(val[2]), Number(val[3])]
                } else {
                    vs = [Number(val[1]), Number(val[2]), Number(val[3]), Number(val[4])]
                }
			} else if (textattrs.indexOf(attr) > -1) {
				if (attr == 'choices') {          // menu choices are wrapped in a list
					val = m[3].slice(2, -2).split("', '") // choices separated by ', '
                } else {
                    // '\n' doesn't survive JSON transmission, so in vpython.py we replace '\n' with '<br>'
                    val = m[3].replace(/<br>/g, "\n")
                }
			} else if (attr == 'rotate') { // angle,x,y,z,x,y,z
				var temp = m[3]
				val = []
				var first = temp.match(/([^,]*)/)
				val.push(Number(first[1]))
				var v1 = temp.slice(first[1].length+1)
				m = v1.match(/([^,]*),([^,]*),([^,]*)/)
				val.push(vec(Number(m[1]), Number(m[2]), Number(m[3])))
				var v2 = temp.slice(first[1].length + 1 + m[0].length + 1)
				m = v2.match(vpatt)
				val.push(vec(Number(m[1]), Number(m[2]), Number(m[3])))
			} else if (attr == 'plot' || attr == 'data') {
				val = []
				var start = m[1].length+1 // start of arguments
				while (true) {
					m = s.slice(start).match(plotpatt)
					val.push([ Number(m[1]), Number(m[2]) ])
					start += m[1].length+m[2].length+2
					if (start > s.length) break
				}
			} else if (attr == 'waitfor' || attr == 'pause' || attr == 'delete') {
				val = m[3]
            } else if (attr == 'follow') {
                if (m[3] == 'None') val = null
                else val = Number(m[3])
			} else val = Number(m[3])
			out = {'idx':idx, 'attr':attr, 'val':val}
			if (datatype == 'attr') as.push(out)
			else ms.push(out)
		}
	}
	if (as.length > 0) data['attrs'] = as
	else data['attrs'] = []
	if (ms.length > 0) data['methods'] = ms
	return data
}

function fix_location(cfgx) {
    "use strict";
    if ('location' in cfgx) {
        var loc = cfgx['location']
        var id = loc[0]
        if (id == -1) {
            cfgx['pos'] = print_anchor // this doesn't work; throw an error in vpython.py
        } else {
            var cvs = glowObjs[id]
            var where = loc[1]
            if (where === 1) cfgx['pos'] = cvs.title_anchor
            else cfgx['pos'] = cvs.caption_anchor
        }
        delete cfgx['location']
    }
    return cfgx
}

var glowObjs = []

//scene.title.text("fps = frames/sec\n ")
// Display frames per second and render time:
//$("<div id='fps'/>").appendTo(scene.title)

function o2vec3(p) {
    "use strict";
    return vec(p[0], p[1], p[2])
}

function handler(data) {
    "use strict";
	
	/*
	console.log('---------------')
	for (var d in data) {
		for (var i in data[d]) console.log(i, JSON.stringify(data[d][i]))
	}
	*/

	
	if (data.cmds !== undefined && data.cmds.length > 0) handle_cmds(data.cmds)
	if (data.methods !== undefined && data.methods.length > 0) handle_methods(data.methods)
	if (data.attrs !== undefined && data.attrs.length > 0) handle_attrs(data.attrs)
} // end of handler

function handle_cmds(dcmds) {
    "use strict";
	//console.log('CMDS')
	for (var icmds=0; icmds<dcmds.length; icmds++) { // constructors, and special operations such as curve.modify
		var cmd = dcmds[icmds]
		var obj = cmd.cmd
		var idx = cmd.idx
		delete cmd.cmd
		delete cmd.idx
		var construct = (obj !== undefined)
		var method = null
		if ('method' in cmd) {
			method = cmd['method']
			delete cmd['method']
		}
		var triangle_quad = ['v0', 'v1', 'v2', 'v3']

		//assembling cfg
		var vlst = ['pos', 'color', 'size', 'axis', 'up', 'direction', 'center', 'forward', 'foreground',
				 'background', 'ambient', 'linecolor', 'dot_color', 'trail_color', 'textcolor', 'attrval',
				 'origin', 'normal', 'bumpaxis','texpos', 'start_face_color', 'end_face_color', 'marker_color',
				 'start_normal', 'end_normal']
		if ((obj != 'gcurve') && ( obj != 'gdots' ) ) vlst.push( 'size' )
		var cfg = {}
		var objects = []
		var attr
		for (attr in cmd) {
			val = cmd[attr]
			if (attr === "size") {
				if ( (obj == 'gcurve') || ( obj == 'gdots' ) ) {
					cfg[attr] = cmd[attr]   // size is a scalar
				} else {
				   cfg[attr] = o2vec3(val)
				}                            
			} else if ( (attr == 'pos' && (obj == 'curve' || obj == 'points')) ||
						(obj == 'extrusion' && (attr == 'path' || attr == 'color') ) ) { // only occurs in constructor
				let ptlist = []
				if (val[0].length === undefined) { // a single triple [x,y,z] to convert to a vector
					ptlist = o2vec3(val)
				} else {
					for (var kk = 0; kk < val.length; kk++) {
						ptlist.push( o2vec3(val[kk]) )
					}
				}
				cfg[attr] = ptlist
			} else if (vlst.indexOf(attr) !== -1) {
				cfg[attr] = o2vec3(val)
			} else if (triangle_quad.indexOf(attr) !== -1) {
				cfg[attr] = glowObjs[val]
			} else if (attr === "canvas" ) {
				cfg[attr] = glowObjs[val]
			} else if (attr === "graph" ) {
				cfg[attr] = glowObjs[val]
			} else if (attr === "obj_idxs") {
				var len4 = val.length
				if (len4 > 0) {
					for (var k = 0; k < len4; k++) {
						objects[k] = glowObjs[val[k]]
					}
				}
			} else if (attr == "lights") {
				if (val == 'empty_list') val = []
				cfg[attr] = val
			} else {
				cfg[attr] = val
			}
		}
		if (!construct) { // commands such as "center" (for a canvas)
			var parametric = ['splice', 'modify']
			var val = cfg[attr]
			if (attr == 'append_to_caption' || attr == 'append_to_title' ) glowObjs[idx][attr](val)
			else if (method !== null) {
				var npargs = 0
				var info
				if (parametric.indexOf(method) > -1) {
					npargs = val.length - 1
					info = val[npargs]  // a list of dictionaries
				} else {
					info = val
				}
				for (var j=0; j < info.length; j++) {
					var dj = info[j]
					for (var a in dj) {
						if (dj[a] instanceof Array) dj[a] = o2vec3(dj[a])
					} 
				}
				if ( npargs === 0 ) {
					glowObjs[idx][method](info)
				} else if ( method === 'modify' ) { // 1 parameter
					glowObjs[idx][method](val[0], info[0])
				} else if ( method === 'splice' ) {  // 2 parameters
					glowObjs[idx][method](val[0], val[1], info)
				} else {
					throw new Error('Too many parameters in '+method)
				}
			} else glowObjs[idx][attr] = val
			continue
		}
		// creating the objects
		cfg.idx = idx // reinsert idx, having looped thru all other attributes
		// triangle and quad objects should not have a canvas attribute; canvas is provided in the vertex objectsE
		if ((obj == 'triangle' || obj == 'quad') && cfg.canvas !== undefined) delete cfg.canvas
		switch (obj) {
			case 'box':           {glowObjs[idx] = box(cfg); break}
			case 'sphere':        {glowObjs[idx] = sphere(cfg); break}
			case 'simple_sphere': {glowObjs[idx] = simple_sphere(cfg); break}
			case 'arrow':         {glowObjs[idx] = arrow(cfg); break}
			case 'cone':          {glowObjs[idx] = cone(cfg); break}
			case 'cylinder':      {glowObjs[idx] = cylinder(cfg); break}
			case 'helix':         {glowObjs[idx] = helix(cfg); break}
			case 'pyramid':       {glowObjs[idx] = pyramid(cfg); break}
			case 'ring':          {glowObjs[idx] = ring(cfg); break}
			case 'curve':         {glowObjs[idx] = curve(cfg); break}
			case 'points':        {glowObjs[idx] = points(cfg); break}
			case 'vertex':        {glowObjs[idx] = vertex(cfg); break}
			case 'triangle':      {glowObjs[idx] = triangle(cfg); break}
			case 'quad':          {glowObjs[idx] = quad(cfg); break}
			case 'label':         {glowObjs[idx] = label(cfg); break}
			case 'ellipsoid':     {glowObjs[idx] = sphere(cfg); break}
			case 'graph':     { // currently graph gives an error for non-fundamental arguments
				delete cfg.idx
				glowObjs[idx] = graph(cfg)
				break
			}
			case 'gcurve':    { // currently gcurve give an error for non-fundamental arguments
				delete cfg.idx
				glowObjs[idx] = gcurve(cfg)
				break
			}
			case 'gdots':     { // currently gdots give an error for non-fundamental arguments
                delete cfg.idx
				glowObjs[idx] = gdots(cfg)
				break
			}
			case 'gvbars':    { // currently gvbars give an error for non-fundamental arguments
				delete cfg.idx
				glowObjs[idx] = gvbars(cfg)
				break
			}
			case 'ghbars':    { // currently ghbars give an error for non-fundamental arguments
				delete cfg.idx
				glowObjs[idx] = ghbars(cfg)
				break
			}
			case 'compound': {
				if (cfg._cloneid !== undefined) {
					var idoriginal = cfg._cloneid
					delete cfg._cloneid
					glowObjs[idx] = glowObjs[idoriginal].clone(cfg)
				} else {
					var obj = glowObjs[idx] = compound(objects, cfg)
					// Return computed compound pos and size to Python
					send_compound(obj.canvas['idx'], obj.pos, obj.size, obj.up)
				}
				break
			}
			case 'extrusion': {
				var obj = glowObjs[idx] = extrusion(cfg)
				// Return computed compound pos and size to Python
				send_compound(obj.canvas['idx'], obj.pos, obj.size, obj.up)
				break
			}
			case 'text':     {
				if (cfg._cloneid !== undefined) {
					var idoriginal = cfg._cloneid
					delete cfg._cloneid
					glowObjs[idx] = glowObjs[idoriginal].clone(cfg)
				} else {
					// Return text parameters to Python
					var obj = glowObjs[idx] = text(cfg)
					send_compound(obj.canvas['idx'], vec(obj.length, obj.descender, 0), 
                            obj.__comp.size, obj.up)
				}
				break
			}
			case 'local_light':   {glowObjs[idx] = local_light(cfg); break}
			case 'distant_light': {glowObjs[idx] = distant_light(cfg); break}
			case 'canvas':        {
				if ((typeof isjupyterlab_vpython !== 'undefined') && (isjupyterlab_vpython === true)) {
					var container = document.getElementById("glowscript");
					if (container !== null) {
						window.__context = { glowscript_container: $("#glowscript").removeAttr("id")}
					}
					glowObjs[idx] = canvas(cfg)
					glowObjs[idx]['idx'] = idx
					try{
						glowObjs[idx].wrapper[0].addEventListener("contextmenu", function(event){
							event.preventDefault(); 
							event.stopPropagation(); 
						});
					}
					catch(err) {
						console.log("glowcomm canvas contextmenu event : ",err.message);
					}
				} else {
					glowObjs[idx] = canvas(cfg)
					glowObjs[idx]['idx'] = idx
				}
				break
					// Display frames per second and render time:
					//$("<div id='fps'/>").appendTo(glowObjs[idx].title)
			}
			case 'attach_arrow':  {
                var attrs = ['pos', 'size', 'axis', 'up', 'color']
				var o = glowObjs[cfg['obj']]
				delete cfg['obj']
				var attr = cfg['attr']
				delete cfg['attr']
                var val = cfg['attrval']
                delete cfg['attrval']
                if (attrs.indexOf(attr) < 0) attr = '_attach_arrow'
                o.attr = val
				glowObjs[idx] = attach_arrow( o, attr, cfg )
				break
			}
			case 'attach_trail': {
				if ( typeof cfg['_obj'] === 'string' ) {
					var o = cfg['_obj'] // the string '_func'
				} else {
					var o = glowObjs[cfg['_obj']]
				}
				delete cfg['_obj'] 
				glowObjs[idx] = attach_trail(o, cfg)
				break
			}
            case 'wtext': {
				cfg.objName = obj
				cfg = fix_location(cfg)
				glowObjs[idx] = wtext(cfg)
				break
            }
            case 'winput': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = winput(cfg)
				break
            }
			case 'checkbox': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = checkbox(cfg)
				break
			}
			case 'radio': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = radio(cfg)
				break
			}
			case 'button': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = button(cfg)
				break
			}
			case 'slider': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = slider(cfg)
				break
			}
			case 'menu': {
				cfg.objName = obj
				cfg.bind = control_handler
				cfg = fix_location(cfg)
				glowObjs[idx] = menu(cfg)
				if (cfg['selected'] === 'None') {
					cfg['selected'] = null                              
				} 
				break
			}
			default:
				console.log("Unable to create object")
		}
	} // end of cmds (constructors and special data)
}

async function handle_methods(dmeth) {
    "use strict";
	//console.log('METHODS')
	for (var idmeth=0; idmeth<dmeth.length; idmeth++) { // methods; cmd is ['idx':idx, 'attr':method, 'val':val]
		var cmd = dmeth[idmeth]
		var idx = cmd.idx
		var method = cmd.attr
		var val = cmd.val
		var obj = glowObjs[idx]

		ifif (val == 'None') {
			if (method == 'delete') obj['remove']()
			else obj[method]()
		} else if (method === 'rotate') {
			obj.rotate({angle:val[0], axis:val[1], origin:val[2]})
		} else if (method === 'pos') {
			glowObjs[idx]['pos'] = val
		} else if (method === 'add_to_trail') {
			obj['_func'] = val
		} else if (method === '_attach_arrow') {
            obj.obj._attach_arrow = val
		} else if (method === 'bind') {
			var evts = val.split(' ')
			for (var evt in evts) {
				var e = evts[evt]
				if (binds.indexOf(e) == -1) 
					throw new Error('There is no error type "'+e+'"')
			}
			obj.bind(val, process_binding)
		} else if (method === 'unbind') {
			var evts = val.split(' ')
			for (var evt in evts) {
				var e = evts[evt]
				if (binds.indexOf(e) == -1) 
					throw new Error('There is no error type "'+e+'"')
			}
			obj.unbind(val, process_binding)
		} else if (method === "follow") {
            if (val === null) obj.camera.follow(null)
			else obj.camera.follow(glowObjs[val])
		} else if (method === "capture") {
			// val has the form "Tname.png" (display labels) or "Fname.png" (do not display labels)
			let TF =  (val[0] == 'T') ? true: false
			await obj.capture(val.slice(1), TF)
		} else if (method === 'waitfor') {
			waitfor_canvas = idx
			waitfor_options = val
			obj.bind(waitfor_options, process_waitfor)
		} else if (method === 'pause') {
			waitfor_canvas = idx
			waitfor_options = 'click'
			if (val.length > 0) {
			   await obj.pause(val)
			} else {
			   await obj.pause()
			}
			process_pause()
		} else if (method === 'pick') {
			var p = glowObjs[val].mouse.pick()  // wait for pick render; val is canvas
			var seg = null
			if (p !== null) {
				if (p instanceof curve) seg = p.segment
				p = p.idx                                
			}
			send_pick(val, p, seg)
		} else obj[method](val)
	}
}

function handle_attrs(dattrs) {
    "use strict";
	//console.log('ATTRS')
	for (var idattrs=0; idattrs<dattrs.length; idattrs++) { // attributes; cmd is {'idx':idx, 'attr':attr, 'val':val}
		var cmd = dattrs[idattrs]
		var idx = cmd.idx
		var obj = glowObjs[idx]
		var attr = cmd['attr']
		var val = cmd['val']
		var triangle_quad = ['v0', 'v1', 'v2', 'v3']
		// vector attrs in attach_arrow have arbitrary names, so check for length 3 array instead
		if (val instanceof vec) {
			if (attr === 'pos' && (obj instanceof points || obj instanceof curve)) {
				var ptlist = []
				for (var kk = 0; kk < val.length; kk++) {
					ptlist.push( val[kk] )
				}
				obj[attr] = ptlist
			} else {
				obj[attr] = val
			}
		} else if (attr == 'lights') {
			if (val == 'empty_list') val = []
			obj[attr] = val
		} else {
			if (triangle_quad.indexOf(attr) !== -1) {
				obj[attr] = glowObjs[val]
            } else if (attr == 'vs') {
                if (val.length == 3) obj['vs'] = [ glowObjs[val[0]], glowObjs[val[1]], glowObjs[val[2]] ]
                else obj['vs'] = [ glowObjs[val[0]], glowObjs[val[1]], glowObjs[val[2]], glowObjs[val[3]] ]
			} else {
				obj[attr] = val
			}
		}
	} // end of attributes
}
console.log("END OF GLOWCOMM")

});
