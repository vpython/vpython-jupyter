import {
  IDisposable, DisposableDelegate
} from '@lumino/disposable';

import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import { PageConfig } from '@jupyterlab/coreutils';

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

    Promise.all([panel.revealed, panel.sessionContext.ready, context.ready]).then(function() {
		const session = context.sessionContext.session;
		const kernelInstance = session?.kernel;
		(<any>window).JLab_VPython = true;

 		try {
			kernelInstance?.registerCommTarget('glow', (vp_comm: any, commMsg: any) => {
				// Use Dynamic import() Expression to import glowcomm when comm is opened
				import("./glowcommlab").then(glowcommlab => {
					glowcommlab.comm = vp_comm
					vp_comm.onMsg = glowcommlab.onmessage
					
					// Get Websocket URL of current notebook server
					let ws_url = PageConfig.getWsUrl()

					// Construct URL of our proxied service
					let serviceUrl = ws_url + 'proxy/';
					
					glowcommlab.setupWebsocket(commMsg, serviceUrl)					
				});
			
				vp_comm.onClose = (msg: any) => {console.log("comm onClose");};
			});
		}
		catch(err) {
			if (err instanceof Error) {
				console.log("register glow error : ",err.message);
			} else {
				console.log('Unexpected error', err);
			}
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
