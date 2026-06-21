# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ventanamapa.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setStyleSheet(u"QComboBox {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    selection-background-color: #555;\n"
"}")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.webEngineView = QWebEngineView(self.centralwidget)
        self.webEngineView.setObjectName(u"webEngineView")
        self.webEngineView.setGeometry(QRect(20, 20, 711, 491))
        self.webEngineView.setMinimumSize(QSize(711, 0))
        self.webEngineView.setMaximumSize(QSize(711, 16777215))
        self.webEngineView.setUrl(QUrl(u"about:blank"))
        self.FiltrosBarcos = QComboBox(self.centralwidget)
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.addItem("")
        self.FiltrosBarcos.setObjectName(u"FiltrosBarcos")
        self.FiltrosBarcos.setGeometry(QRect(540, 70, 181, 26))
        self.FiltrosBarcos.setStyleSheet(u"QComboBox {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    selection-background-color: #555;\n"
"}")
        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(230, 30, 191, 26))
        self.lineEdit.setStyleSheet(u"QLineEdit {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}")
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(430, 30, 81, 26))
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #555;\n"
"}")
        self.Busquedapaismmsi = QComboBox(self.centralwidget)
        self.Busquedapaismmsi.addItem("")
        self.Busquedapaismmsi.setObjectName(u"Busquedapaismmsi")
        self.Busquedapaismmsi.setGeometry(QRect(130, 30, 89, 26))
        self.Filtro_site = QComboBox(self.centralwidget)
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.addItem("")
        self.Filtro_site.setObjectName(u"Filtro_site")
        self.Filtro_site.setGeometry(QRect(540, 180, 181, 26))
        self.Filtro_site.setStyleSheet(u"QComboBox {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    selection-background-color: #555;\n"
"}")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(540, 30, 181, 31))
        self.label_2.setStyleSheet(u"QLabel {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QLabel::drop-down {\n"
"    border: none;\n"
"}")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(540, 140, 181, 31))
        self.label_3.setStyleSheet(u"QLabel {\n"
"    background-color: #2b2b2b;\n"
"    color: white;\n"
"    border: 1px solid #555;\n"
"    border-radius: 4px;\n"
"    padding: 4px;\n"
"}\n"
"\n"
"QLabel::drop-down {\n"
"    border: none;\n"
"}")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.FiltrosBarcos.setItemText(0, QCoreApplication.translate("MainWindow", u"Todos", None))
        self.FiltrosBarcos.setItemText(1, QCoreApplication.translate("MainWindow", u"Pesca", None))
        self.FiltrosBarcos.setItemText(2, QCoreApplication.translate("MainWindow", u"Remolque", None))
        self.FiltrosBarcos.setItemText(3, QCoreApplication.translate("MainWindow", u"Velero", None))
        self.FiltrosBarcos.setItemText(4, QCoreApplication.translate("MainWindow", u"Recreo", None))
        self.FiltrosBarcos.setItemText(5, QCoreApplication.translate("MainWindow", u"Remolcador", None))
        self.FiltrosBarcos.setItemText(6, QCoreApplication.translate("MainWindow", u"Pasajeros", None))
        self.FiltrosBarcos.setItemText(7, QCoreApplication.translate("MainWindow", u"Carga", None))
        self.FiltrosBarcos.setItemText(8, QCoreApplication.translate("MainWindow", u"Petrolero", None))

        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Buscar", None))
        self.Busquedapaismmsi.setItemText(0, QCoreApplication.translate("MainWindow", u"MMSI", None))

        self.Filtro_site.setItemText(0, QCoreApplication.translate("MainWindow", u"Ninguna seleccionada", None))
        self.Filtro_site.setItemText(1, QCoreApplication.translate("MainWindow", u"Mar Mediterraneo", None))
        self.Filtro_site.setItemText(2, QCoreApplication.translate("MainWindow", u"Canal de Suez", None))
        self.Filtro_site.setItemText(3, QCoreApplication.translate("MainWindow", u"Canal de Panam\u00e1", None))
        self.Filtro_site.setItemText(4, QCoreApplication.translate("MainWindow", u"Estrecho de Malaka", None))
        self.Filtro_site.setItemText(5, QCoreApplication.translate("MainWindow", u"Estrecho de Ormuz", None))
        self.Filtro_site.setItemText(6, QCoreApplication.translate("MainWindow", u"Mar de China", None))

        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Tipo de barco:", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Localizaciones importantes:", None))
    # retranslateUi

