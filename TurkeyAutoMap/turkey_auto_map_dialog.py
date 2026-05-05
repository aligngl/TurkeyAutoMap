# -*- coding: utf-8 -*-
"""PyQt dialog for the TurkeyAutoMap QGIS plugin."""

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "turkey_auto_map_dialog.ui")
)


class TurkeyAutoMapDialog(QDialog, FORM_CLASS):
    """Main dialog used to collect user input and display progress."""

    def __init__(self, parent=None):
        """Initialize dialog widgets from the Qt Designer UI file."""
        super().__init__(parent)
        self.setupUi(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.districtFocusCheckBox.setChecked(False)

    def set_busy(self, busy):
        """Enable or disable controls while a task is running."""
        self.createButton.setEnabled(not busy)
        self.clearCacheButton.setEnabled(not busy)
        self.saveButton.setEnabled(not busy)
        self.provinceComboBox.setEnabled(not busy)
        self.showNeighborsCheckBox.setEnabled(not busy)
        self.neighborStyleComboBox.setEnabled(not busy)
        self.showPlacesCheckBox.setEnabled(not busy)
        self.placeLabelsCheckBox.setEnabled(not busy)
        self.showMajorWaterwaysCheckBox.setEnabled(not busy)
        self.showMinorWaterwaysCheckBox.setEnabled(not busy)
        self.showLakesCheckBox.setEnabled(not busy)
        self.showReservoirsCheckBox.setEnabled(not busy)
        self.showSeaContextCheckBox.setEnabled(not busy)
        self.waterLabelsCheckBox.setEnabled(not busy)
        self.basemapComboBox.setEnabled(not busy)
        self.themeComboBox.setEnabled(not busy)
        self.paletteComboBox.setEnabled(not busy)
        self.highlightColorComboBox.setEnabled(not busy)
        self.paperSizeComboBox.setEnabled(not busy)
        self.orientationComboBox.setEnabled(not busy)
        self.roadScopeComboBox.setEnabled(not busy)
        self.districtColorCheckBox.setEnabled(not busy)
        self.provinceHighlightCheckBox.setEnabled(not busy)
        self.neighborLabelsCheckBox.setEnabled(not busy)
        self.dynamicLegendCheckBox.setEnabled(not busy)
        self.districtFocusCheckBox.setEnabled(not busy)
        self.districtFocusLineEdit.setEnabled(not busy)
        self.highlightDistrictCheckBox.setEnabled(not busy)
        self.highlightDistrictLineEdit.setEnabled(not busy)
        self.insetMapCheckBox.setEnabled(not busy)
        self.locatorModeComboBox.setEnabled(not busy)
