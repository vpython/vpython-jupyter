
define(["nbextensions/jquery-ui.custom.min","nbextensions/glow.2.0.min"], function() {
/*jslint plusplus: true */
console.log("glowscript loading");

var canvases = {} // canvases with their idx values
var glowObjs = [];

//scene.title.text("fps = frames/sec\n ");
// Display frames per second and render time:
//$("<div id='fps'/>").appendTo(scene.title);

function o2vec3(p) {
    "use strict";
    return vec(p[0], p[1], p[2]);
}

comm = IPython.notebook.kernel.comm_manager.new_comm('glow')
comm.on_msg(handler)
console.log("Comm created for glow target", comm)

function process(event) {
    "use strict";
    var evt = {event:event.event}
    var idx = canvases[event.canvas]
    evt.canvas = idx
    var pos = event.pos
    evt.pos = [pos.x, pos.y, pos.z]
    evt.press = event.press
    evt.release = event.release
    evt.which = event.which
    var ray = glowObjs[idx].mouse.ray 
    evt.ray = [ ray.x, ray.y, ray.z ]
    evt.alt = glowObjs[idx].mouse.alt
    evt.ctrl = glowObjs[idx].mouse.ctrl
    evt.shift = glowObjs[idx].mouse.shift
    comm.send( {arguments: [evt]} )
}

function handler(msg) {
    "use strict";
    var data = msg.content.data;
    console.log('glow msg', msg, msg.content)
    console.log('glow', data, data.length);
    console.log('JSON ' + JSON.stringify(data));

    if (data.length > 0) {
        var i, j, k, cmd, attr, cfg, cfg2, vertdata, len2, len3, attr2, elems, elen, len4, S, b, vlst
        var triangle_quad, objects;  
        var len = data.length;
        triangle_quad = ['v0', 'v1', 'v2', 'v3'];
        for (i = 0; i < len; i++) {
            cmd = data.shift();
//            console.log('\n\n-------------------')
//            console.log('glowwidget0', cmd.idx, cmd.attr, cmd.val, cmd.cmd, cmd.method)
            if (cmd.cmd === undefined) { //  not a constructor
                if (cmd.idx !== undefined) {
                    if (cmd.attr !== undefined) {  
//                        console.log('commsend cmd.attr not undefined', cmd.attr)
                        // not handled yet: 'normal', 'bumpaxis'
                        vlst = ['pos', 'size', 'color', 'axis', 'up', 'direction', 'center', 'forward',
                                'foreground', 'background', 'ambient', 'linecolor', 'dot_color', 'trail_color', 'origin',
                                'normal', 'bumpaxis', 'texpos'];
                        var v
                        if (vlst.indexOf(cmd.attr) !== -1) {
                            if (cmd.attr === 'pos' && (cmd.cmd === 'points' || cmd.cmd === 'curve')) {                       
                                var ptlist = []
                                for (var kk = 0; kk < cmd.val.length; kk++) {
                                    ptlist.push( o2vec3(cmd.val[kk]) )
                                }
                                glowObjs[cmd.idx][cmd.attr] = ptlist
                            } else {
                                v = vec(cmd.val[0], cmd.val[1], cmd.val[2]);
                                if (glowObjs[cmd.idx] instanceof arrow && cmd.attr === 'axis') {
                                    glowObjs[cmd.idx]['axis_and_length'] = v
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
                        if (val == 'None') {
                            if (cmd.method == 'delete') glowObjs[cmd.idx]['remove']()
                            else glowObjs[cmd.idx][cmd.method]()
                        } else if (cmd.method == 'GSprint') {
                            //GSprint(cmd.val) // This appends to $('body'), which doesn't work in notebook
                            var c = canvas.get_selected()
                            var cr = ''
                            if (c.caption.text() !== cr) cr = '\n'
                            c.caption.text(c.caption.text()+cr+cmd.val)
                        } else if ((cmd.method === 'text' || cmd.method === 'html' || 
                                        cmd.method === 'append') && glowObjs[cmd.idx] instanceof canvas) {
                            var loc = cmd.val[0]
                            var s = cmd.val[1]
                            glowObjs[cmd.idx][loc][cmd.method](s)
                        } else if (cmd.method === 'bind') {
                            glowObjs[cmd.idx].bind(cmd.val, process)
                        } else if (cmd.cmd === 'unbind') {
                            glowObjs[cmd.idx].unbind(cmd.val, process)
                        } else {
                            var npargs = 0
                            var info
                            if (parametric.indexOf(cmd.method) > -1) {
                                npargs = val.length - 1
                                info = val[npargs]  // a list of dictionaries
                            } else {
                                info = val
                            }
                            for (var i=0; i < info.length; i++) {
                                var d = info[i]
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
                    console.log('glow', data, data.length);
                    console.log('JSON ' + JSON.stringify(data));
                }
                */
                //assembling cfg
//                console.log('assembling cfg', cmd.cmd, typeof cmd.attrs, cmd.attrs) //**************
//                for (var i in cmd.attrs) { console.log(cmd.attrs[i]) }
                if (cmd.attrs !== undefined) {
                     vlst = ['pos', 'color', 'axis', 'up', 'direction', 'center', 'forward', 'foreground', 'background', 'ambient', 'linecolor', 'dot_color', 'trail_color','origin', 'normal', 'bumpaxis','texpos'];
                    if ((cmd.cmd != 'gcurve') && ( cmd.cmd != 'gdots' ) ) {
                        vlst.push( 'size' )
                    }

                    len2 = cmd.attrs.length;
                    cfg = {};
                    objects = [];
                    for (j = 0; j < len2; j++) {
                        attr = cmd.attrs.shift();
                        if (attr.attr === "size") {
                            if ( (cmd.cmd == 'gcurve') || ( cmd.cmd == 'gdots' ) ) {
                                cfg[attr.attr] = attr.value;   // size is a scalar
                            } else {
                               cfg[attr.attr] = o2vec3(attr.value);
                            }                            
                        } else if (attr.attr ==='pos' && (cmd.cmd === 'curve' || cmd.cmd === 'points')) {
                            var ptlist = []
                            for (var kk = 0; kk < attr.value.length; kk++) {
                                ptlist.push( o2vec3(attr.value[kk]) )
                            }
                            cfg[attr.attr] = ptlist                          
                        } else if (attr.attr === "axis" && cmd.cmd == 'arrow') {
                            cfg['axis_and_length'] = o2vec3(attr.value);
                        } else if (vlst.indexOf(attr.attr) !== -1) {
                            cfg[attr.attr] = o2vec3(attr.value);
                        } else if (triangle_quad.indexOf(attr.attr) !== -1) {
                            cfg[attr.attr] = glowObjs[attr.value]
                        } else if (attr.attr === "canvas" ) {
                            cfg[attr.attr] = glowObjs[attr.value];
                        } else if (attr.attr === "graph" ) {
                            cfg[attr.attr] = glowObjs[attr.value];
                        } else if (attr.attr === "obj_idxs") {
                            len4 = attr.value.length;
                            if (len4 > 0) {
                                for (k = 0; k < len4; k++) {
                                    objects[k] = glowObjs[attr.value[k]];
                                }
                            }
                        } else {
                            cfg[attr.attr] = attr.value;
                            // console.log(attr.attr, attr.value)
                        }
                    }
                    //making the objects
                    if (cmd.idx !== undefined) {
                        if (cmd.cmd === 'box') {
                            glowObjs[cmd.idx] = box(cfg);
                            glowObjs[cmd.idx].gidx = cmd.idx;
                        } else if (cmd.cmd === 'sphere') {
                            glowObjs[cmd.idx] = sphere(cfg);
                            glowObjs[cmd.idx].gidx = cmd.idx;
                        } else if (cmd.cmd === 'arrow') {
                            glowObjs[cmd.idx] = arrow(cfg);
                        } else if (cmd.cmd === 'cone') {
                            glowObjs[cmd.idx] = cone(cfg);
                        } else if (cmd.cmd === 'cylinder') {
                            glowObjs[cmd.idx] = cylinder(cfg);
                        } else if (cmd.cmd === 'helix') {
                            glowObjs[cmd.idx] = helix(cfg);
                        } else if (cmd.cmd === 'pyramid') {
                            glowObjs[cmd.idx] = pyramid(cfg);
                        } else if (cmd.cmd === 'ring') {
                            glowObjs[cmd.idx] = ring(cfg);
						} else if  (cmd.cmd === 'gcurve') {
							glowObjs[cmd.idx] = gcurve(cfg)
						} else if  (cmd.cmd === 'gdots') {
							glowObjs[cmd.idx] = gdots(cfg)
						} else if  (cmd.cmd === 'gvbars') {
							glowObjs[cmd.idx] = gvbars(cfg)
						} else if  (cmd.cmd === 'ghbars') {
							glowObjs[cmd.idx] = ghbars(cfg)
                        } else if (cmd.cmd == 'graph') {
                            glowObjs[cmd.idx] = vp_graph(cfg)
                        } else if (cmd.cmd === 'curve') {
                            glowObjs[cmd.idx] = curve(cfg);
                        } else if (cmd.cmd === 'points') {
                            glowObjs[cmd.idx] = points(cfg);
                        } else if (cmd.cmd === 'vertex') {
                            glowObjs[cmd.idx] = vertex(cfg);
                        } else if (cmd.cmd === 'triangle') {
                            glowObjs[cmd.idx] = triangle(cfg);
                        } else if (cmd.cmd === 'quad') {
                            glowObjs[cmd.idx] = quad(cfg);
                        } else if (cmd.cmd === 'push') {
                            glowObjs[cmd.idx].push(cfg);
                        } else if (cmd.cmd === 'label') {
                            glowObjs[cmd.idx] = label(cfg);
                        } else if (cmd.cmd === 'ellipsoid') {
                            glowObjs[cmd.idx] = sphere(cfg);
                        } else if (cmd.cmd === 'lights') {
                            glowObjs[cmd.idx] = lights(cfg);
                        } else if (cmd.cmd === 'rotate') {
                            glowObjs[cmd.idx].rotate(cfg);
                        } else if (cmd.cmd === 'local_light') {
                            glowObjs[cmd.idx] = local_light(cfg);
                        } else if (cmd.cmd === 'distant_light') {
                            glowObjs[cmd.idx] = distant_light(cfg);
                        } else if (cmd.cmd === 'compound') {
                            glowObjs[cmd.idx] = compound(objects, cfg);
                        } else if (cmd.cmd === 'canvas') {
                            glowObjs[cmd.idx] = canvas(cfg);
                            canvases[glowObjs[cmd.idx]] = cmd.idx
                                // Display frames per second and render time:
                                //$("<div id='fps'/>").appendTo(glowObjs[cmd.idx].title);
                        } else {
                            console.log("Unrecognized Object");
                        }
                    } else {
                        console.log("Unable to create object, idx attribute is not provided");
                    }
                }
                if (cmd.cmd === 'redisplay') {
                    var c = document.getElementById(cmd.sceneId);
                    if (c !== null) {
                        var scn = "#" + cmd.sceneId;
                        glowObjs[cmd.idx].sceneclone = $(scn).clone(true,true);
                        //document.getElementById('glowscript2').appendChild(c);
                        //document.getElementById('glowscript2').replaceWith(c);
                        $('#glowscript2').replaceWith(c);
                        c = document.getElementById(cmd.sceneId);
                        var cont = scn + " .glowscript";
                        window.__context = { glowscript_container:    $(cont) };
                    } else {
                        window.__context = { glowscript_container: $("#glowscript").removeAttr("id") };                    
                        var newcnvs = canvas();
                        for (var obj in glowObjs[cmd.idx].objects) {
                            var o = glowObjs[cmd.idx].objects[obj];
                            if ((o.constructor.name !== 'curve') && (o.constructor.name !== 'points')) {
                                glowObjs[o.gidx] = o.clone({canvas: newcnvs});
                                var olen = newcnvs.objects.length;
                                if (olen > 0) {
                                    newcnvs.objects[olen - 1].gidx = o.gidx;
                                }
                            }
                        }
                        glowObjs[cmd.idx] = newcnvs;
                        $("#glowscript2").attr("id",cmd.sceneId);
                    }
                } else if (cmd.cmd === 'delete') {
                    b = glowObjs[cmd.idx];
                    //console.log("delete : ",cmd.idx);
                    if ((b !== null) || (b.visible !== undefined)) {
                        b.visible = false;
                    }
                    glowObjs[cmd.idx] = null;
                } else if (cmd.cmd === 'heartbeat') {
                    //console.log("heartbeat");
                } else if (cmd.cmd === 'debug') {
                    console.log("debug : ", cmd);
                }
            }
        }
    }
};


});