import {
  IDisposable, DisposableDelegate
} from '@phosphor/disposable';

import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';



/**
 * The plugin registration information.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  activate,
  id: 'vpython',
  autoStart: true
};

/**
 * A notebook extension to support VPython in Jupyterlab
 */
export
class VPythonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {

    Promise.all([panel.revealed, panel.session.ready, context.ready]).then(function() {
		const session = context.session;
		const kernelInstance = session.kernel;
		(<any>window).JLab_VPython = true;

 		try {	
			kernelInstance.registerCommTarget('glow', (vp_comm, commMsg) => {
				// Use Dynamic import() Expression to import glowcomm when comm is opened
				import("./glowcommlab").then(glowcommlab => {
					glowcommlab.comm = vp_comm
					vp_comm.onMsg = glowcommlab.onmessage
					
					glowcommlab.setupWebsocket(commMsg)
					
				});
			
				vp_comm.onClose = (msg) => {console.log("comm onClose");};
			});
		}
		catch(err) {
			console.log("register glow error : ",err.message);
		}
		
    });
	
    return new DisposableDelegate(() => {
    });

  }
}

/**
 * Activate the extension.
 */
function activate(app: JupyterFrontEnd) {
  app.docRegistry.addWidgetExtension('Notebook', new VPythonExtension());
};



/**
 * Export the plugin as default.
 */
export default plugin;
