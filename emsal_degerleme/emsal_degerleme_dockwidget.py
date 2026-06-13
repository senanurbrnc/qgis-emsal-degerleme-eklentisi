# -*- coding: utf-8 -*-

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'emsal_degerleme_dockwidget_base.ui'))


class EmsalDegerlemeDockWidget(QDockWidget, FORM_CLASS):

    def __init__(self, parent=None):
        super(EmsalDegerlemeDockWidget, self).__init__(parent)
        self.setupUi(self)