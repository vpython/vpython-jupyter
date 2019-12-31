import sys
import PyQt5.QtCore
import PyQt5.QtWebEngineWidgets
from PyQt5.QtWidgets import QApplication


if len(sys.argv) > 1:

    if sys.argv[1]:

        app = QApplication(sys.argv)

        web = PyQt5.QtWebEngineWidgets.QWebEngineView()
        web.load(PyQt5.QtCore.QUrl(sys.argv[1]))
        web.show()

        sys.exit(app.exec_())

    else:
        print("Please give a URL as the first command-line argument "
              "when running the program.")

else:
    print("Please give a URL as the first command-line argument "
          "when running the program.")
