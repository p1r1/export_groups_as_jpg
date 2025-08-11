from krita import *
import os
import time
from PyQt5.QtWidgets import QApplication, QProgressDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor


EXTENSION_ID = "pykrita_export_groups_as_jpg"
MENU_ENTRY = "Export Groups as JPG"
EXPORT_PATH = os.path.expanduser("~/Desktop/KritaExports")  # Change path as needed

"""
color=QColor('#ff9966')
pngOptions=InfoObject()
pngOptions.setProperty('compression', 9)        # 0 (no compression) to 9 (max compression)
pngOptions.setProperty('indexed', False)        # True to use indexed palette    
pngOptions.setProperty('interlaced', False)     # True to use interlaced 
pngOptions.setProperty('saveSRGBProfile', True) # False to not use sRGB profile
pngOptions.setProperty('forceSRGB', True)       # False to not use convert to sRGB
pngOptions.setProperty('alpha', True)           # False to not save alpha channel
pngOptions.setProperty('transparencyFillcolor', [color.red(), color.green(), color.blue()])

jpgOptions=InfoObject()
jpgOptions.setProperty('quality', 85)           # 0 (high compression/low quality) to 100 (low compression/higher quality)
jpgOptions.setProperty('smoothing', 15)         # 0 to 100    
jpgOptions.setProperty('subsampling', 2)        # 0=4:2:0 (smallest file size)   1=4:2:2    2=4:4:0     3=4:4:4 (Best quality)
jpgOptions.setProperty('progressive', True)             # False for non pogressive JPEG file
jpgOptions.setProperty('optimize', True)
jpgOptions.setProperty('saveProfile', True)             # False to not save icc profile
jpgOptions.setProperty('transparencyFillcolor', [color.red(), color.green(), color.blue()])


currentDocument=Krita.instance().activeDocument()
currentDocument.setBatchmode(True)              # do not display export dialog box
saved = currentDocument.exportImage("test.png", pngOptions)
saved = currentDocument.exportImage("test.jpeg", jpgOptions)
"""


class Export_groups_as_jpg(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(EXTENSION_ID, MENU_ENTRY, "tools/scripts")
        action.triggered.connect(self.export_groups_as_jpg)

    def set_visibility_recursively(self, node, visible):
        node.setVisible(visible)
        time.sleep(0.2)
        QApplication.processEvents()
        time.sleep(0.2)
        for child in node.childNodes():
            self.set_visibility_recursively(child, visible)

    def set_visibility(self, node, visible):
        node.setVisible(visible)
        time.sleep(0.3)
        QApplication.processEvents()
        time.sleep(0.3)

    def duplicate_and_flatten_group(self, doc, group_node):
        # Duplicate group
        duplicated = group_node.duplicate()
        doc.rootNode().addChildNode(duplicated, None)

        # Flatten duplicated group
        doc.setActiveNode(duplicated)
        Krita.instance().action("flatten_layer").trigger()

        doc.waitForDone()
        doc.refreshProjection()
        doc.waitForDone()
        time.sleep(0.3)
        QApplication.processEvents()

        # Hide current group
        self.set_visibility(group_node, False)

        # The duplicate is now a flattened paint layer
        return duplicated

    def export_groups_as_jpg(self):
        doc = Krita.instance().activeDocument()

        # progress bar
        total_groups = sum(
            1 for node in doc.rootNode().childNodes() if node.type() == "grouplayer"
        )
        progress = QProgressDialog("Exporting Groups...", "Cancel", 0, total_groups)
        progress.setWindowTitle("Batch Export")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        if not doc:
            QMessageBox.warning(None, "Error", "No active document found!")
            return

        # Ensure export folder exists
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH)

        # Hide all groups first
        for n in doc.rootNode().childNodes():
            if n.type() == "grouplayer":
                self.set_visibility(n, False)

        # Iterate over root child nodes
        for node in doc.rootNode().childNodes():
            if (
                node.type() != "grouplayer"
                or node.name() == "G_design"
                or node.name() == "xxx"
            ):
                continue  # Skip non-group layers

            # progress cancel
            if progress.wasCanceled():
                QMessageBox.information(None, "Cancelled", "Export cancelled by user.")
                break  # Exit the loop immediately

            # Duplicate & Flatten group
            flattened_group = self.duplicate_and_flatten_group(doc, node)
            QApplication.processEvents()
            time.sleep(0.2)

            # Show current group and childs!!!
            self.set_visibility(node, True)
            for child in node.childNodes():
                self.set_visibility_recursively(child, True)

            color = QColor("#ffffff")  # Background fill color (white)
            jpgOptions = InfoObject()
            jpgOptions.setProperty("quality", 100)  # Compression Quality (0-100)
            jpgOptions.setProperty("smoothing", 0)  # No smoothing
            jpgOptions.setProperty("subsampling", 3)  # Best quality (4:4:4)
            jpgOptions.setProperty("progressive", False)
            jpgOptions.setProperty("optimize", True)
            jpgOptions.setProperty("saveProfile", False)
            jpgOptions.setProperty("alpha", False)  # JPEG doesn't support alpha
            jpgOptions.setProperty(
                "transparencyFillcolor", [color.red(), color.green(), color.blue()]
            )

            # Export visible content
            filename = f"{node.name()}.jpg"
            export_file = os.path.join(EXPORT_PATH, filename)
            doc.setBatchmode(True)  # Suppress dialog box
            QApplication.processEvents()
            doc.waitForDone()
            doc.refreshProjection()
            doc.waitForDone()
            time.sleep(0.3)

            saved = doc.exportImage(export_file, jpgOptions)
            if not saved:
                QMessageBox.information(
                    None, "Done", f"{filename} failed to export {export_file}"
                )

            time.sleep(0.2)
            QApplication.processEvents()
            time.sleep(0.2)

            # Delete the temporary flattened group
            doc.rootNode().removeChildNode(flattened_group)
            QApplication.processEvents()
            time.sleep(0.2)

            # progress
            progress.setValue(progress.value() + 1)
            QApplication.processEvents()
            time.sleep(0.5)

        progress.close()
        QMessageBox.information(None, "Done", "All groups exported as JPG!")
