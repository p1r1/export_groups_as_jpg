from krita import *
import os
import time
from PyQt5.QtWidgets import QApplication, QProgressDialog, QMessageBox, QFileDialog
from PyQt5.QtGui import QColor


EXTENSION_ID = "pykrita_export_groups_as_jpg"
MENU_ENTRY = "OFM Export Groups as JPG"
# export_path = os.path.expanduser("~/Desktop/KritaExports")  # Change path as needed

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

    def wait_for_krita_then_refresh(self, doc, sleep_time=0.1):
        doc.waitForDone()
        doc.refreshProjection()
        doc.waitForDone()
        time.sleep(sleep_time)

    def wait_for_krita(self, doc, sleep_time=0.1):
        doc.waitForDone()
        time.sleep(sleep_time)

    def set_visibility_recursively(self, node, visible, doc):
        node.setVisible(visible)
        self.wait_for_krita_then_refresh(doc)
        for child in node.childNodes():
            self.set_visibility_recursively(child, visible, doc)

    def set_visibility(self, node, visible, doc):
        node.setVisible(visible)
        self.wait_for_krita_then_refresh(doc)

    def duplicate_and_flatten_group2(self, doc, group_node):
        # Duplicate group
        duplicated = group_node.duplicate()
        doc.rootNode().addChildNode(duplicated, None)

        # Flatten duplicated group
        doc.setActiveNode(duplicated)
        self.wait_for_krita(doc=doc)
        Krita.instance().action("flatten_layer").trigger()
        self.wait_for_krita(doc=doc)

        # Hide current group
        self.set_visibility(group_node, False, doc)

        # The duplicate is now a flattened paint layer
        return duplicated

    def duplicate_flatten_then_save_group(
        self, doc, group_node, export_file, jpgOptions
    ):
        # Duplicate group
        duplicated_node = group_node.duplicate()
        self.wait_for_krita(doc)
        doc.rootNode().addChildNode(duplicated_node, None)
        self.wait_for_krita(doc)

        # Ensure the group is visible
        self.set_visibility_recursively(duplicated_node, True, doc)

        # Select and flatten
        doc.setActiveNode(duplicated_node)
        self.wait_for_krita(doc=doc)
        Krita.instance().action("flatten_layer").trigger()
        self.wait_for_krita(doc=doc)

        # Export the flattened image
        doc.setBatchmode(True)  # Suppress dialog box
        saved = doc.exportImage(export_file, jpgOptions)
        self.wait_for_krita(doc=doc)
        if not saved:
            print(f"Failed to export {export_file}")

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

        # ask for export path
        export_path = QFileDialog.getExistingDirectory(
            None,  # parent widget (None = main window)
            "Select Export Folder",  # dialog title
            "",  # starting directory ("" = last used)
            QFileDialog.ShowDirsOnly,  # only allow selecting folders
        )
        if not export_path:
            QMessageBox.warning(None, "Error", "No export path found!")
            return

        kra_full_path = doc.fileName()  # Full path to the .kra file
        kra_file_name = os.path.basename(kra_full_path)  # Just the file name
        export_path = os.path.join(export_path, kra_file_name)

        # Ensure export folder exists
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        # Hide all groups first
        for n in doc.rootNode().childNodes():
            if n.type() == "grouplayer":
                self.set_visibility(n, False, doc)

        # save options
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

        # Iterate over root child nodes
        for node in doc.rootNode().childNodes():
            if node.type() != "grouplayer" or "xxx" in node.name():
                continue  # Skip non-group layers

            # progress cancel
            if progress.wasCanceled():
                QMessageBox.information(None, "Cancelled", "Export cancelled by user.")
                break  # Exit the loop immediately

            # Show current group and childs!!!
            self.set_visibility(node, True, doc)
            for child in node.childNodes():
                self.set_visibility_recursively(child, True, doc)

            # Duplicate & Flatten group
            filename = f"{node.name()}.jpg"
            export_file = os.path.join(export_path, filename)
            self.duplicate_flatten_then_save_group(doc, node, export_file, jpgOptions)

            # progress
            progress.setValue(progress.value() + 1)
            QApplication.processEvents()
            time.sleep(0.2)

        # progress
        progress.close()
        QMessageBox.information(None, "Done", "All groups exported as JPG!")
