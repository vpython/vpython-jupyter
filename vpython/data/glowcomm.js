// MAKE SURE THE GLOW LIBRARY HAS THE CORRECT VERSION NUMBER:
define(["nbextensions/jquery-ui.custom.min","nbextensions/glow.2.1.min","nbextensions/pako.min","nbextensions/pako_inflate.min","nbextensions/pako_deflate.min"], function() {
/*jslint plusplus: true */
console.log("glowscript loading");

var glowObjs = []

var pako = require('nbextensions/pako.min')

//scene.title.text("fps = frames/sec\n ")
// Display frames per second and render time:
//$("<div id='fps'/>").appendTo(scene.title)

function o2vec3(p) {
    "use strict";
    return vec(p[0], p[1], p[2])
}

function decode_base64_zipped_json(b64Data) {

    // Decode base64 (convert ascii to binary)
    var strData     = atob(b64Data)

    // Convert binary string to character-number array
    var charData    = strData.split('').map(function(x){return x.charCodeAt(0);});

    // Turn number array into byte-array
    var binData     = new Uint8Array(charData)

    // Pako magic
    var pdata        = pako.inflate(binData)

    // Convert gunzipped byteArray back to ascii string:
    strData     = String.fromCharCode.apply(null, new Uint16Array(pdata))
    
    return JSON.parse(strData)
}

comm = IPython.notebook.kernel.comm_manager.new_comm('glow')
comm.on_msg(handler)
console.log("Comm created for glow target", comm)

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
    return // ignore return from pause; a regular click event will follow
}

function update_canvas() {    // mouse location and other stuff updated every render
    "use strict";
    var evt = {event:'update_canvas'}
    if (canvas.hasmouse === null || canvas.hasmouse === undefined) { return } 
    var cvs = canvas.hasmouse  // only way to change these values is with mouse
    var idx = cvs.idx
    evt.canvas = idx
    var ray = cvs.mouse.ray 
    evt.ray = [ ray.x, ray.y, ray.z ]
    var pos = cvs.mouse.pos
    evt.pos = [pos.x, pos.y, pos.z] 
    // forward and range may be changed by user (and up with touch), and autoscale (by zoom)
    if (cvs.userspin) {
        var forward = cvs.forward
        var up = cvs.up
        evt.forward = [forward.x, forward.y, forward.z]
        evt.up = [up.x, up.y, up.z]
    }
    if (cvs.userzoom) {
        evt.range = cvs.range
        evt.autoscale = cvs.autoscale 
    }
    comm.send( {arguments: [evt]} )    
}

function send_pick(cvs, p, seg) {
    var evt = {event: 'pick', canvas: cvs, pick: p}
    if (glowObjs[p] instanceof curve) {
        evt.segment = seg
    }
    comm.send( {arguments: [evt]} ) 
}

function handler(msg) {
    "use strict";
    var data = msg.content.data

    if (typeof data.zipped !== 'undefined') {        
        data = decode_base64_zipped_json(data.zipped)        
    }

    //console.log('glow msg', msg, msg.content)
    //console.log('glow', data, data.length)
    //console.log('JSON ' + JSON.stringify(data))

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
                                if (cmd.attr === 'axis') {
                                    if (glowObjs[cmd.idx] instanceof arrow) {
                                        glowObjs[cmd.idx]['axis_and_length'] = v
                                    } else {
                                        glowObjs[cmd.idx][cmd.attr] = v
                                        glowObjs[cmd.idx]['size'].x = mag(v)
                                    }
                                } else if (cmd.attr === 'size') {
                                    glowObjs[cmd.idx][cmd.attr] = v
                                    glowObjs[cmd.idx]['axis'] = norm(glowObjs[cmd.idx]['axis']).multiply(v.x)
                                } else {
                                    glowObjs[cmd.idx][cmd.attr] = v
                                }
                            }
                        } else {
                            if (triangle_quad.indexOf(cmd.attr) !== -1) {
                                glowObjs[cmd.idx][cmd.attr] = glowObjs[cmd.val]
                            } else { 
                                glowObjs[cmd.idx][cmd.attr] = cmd.val
                            }
                        }
                    }
                    if (cmd.method !== undefined) {
//                        console.log('cmd.method', cmd.method, cmd.cmd, cmd.val)
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
                        } else if (cmd.method === 'pause') {
                            if (cmd.val.length > 0) {
                               glowObjs[cmd.idx].pause(cmd.val[0], process_pause) 
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
                             'background', 'ambient', 'linecolor', 'dot_color', 'trail_color',
                             'origin', 'normal', 'bumpaxis','texpos']
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
                        } else if (attr.attr ==='pos' && (cmd.cmd === 'curve' || cmd.cmd === 'points')) {
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
                            console.log('graph', cfg)
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
                        } else if (cmd.cmd === 'lights') {
                            glowObjs[cmd.idx] = lights(cfg)
                        } else if (cmd.cmd === 'rotate') {
                            glowObjs[cmd.idx].rotate(cfg)
                        } else if (cmd.cmd === 'local_light') {
                            glowObjs[cmd.idx] = local_light(cfg)
                        } else if (cmd.cmd === 'distant_light') {
                            glowObjs[cmd.idx] = distant_light(cfg)
                        } else if (cmd.cmd === 'compound') {
                            glowObjs[cmd.idx] = compound(objects, cfg)
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
    update_canvas()
};


});