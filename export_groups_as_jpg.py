from krita import *
import os
import time
from PyQt5.QtWidgets import QApplication, QProgressDialog, QMessageBox, QFileDialog
from PyQt5.QtGui import QColor


EXTENSION_ID = "pykrita_export_groups_as_jpg"
MENU_ENTRY = "2 OFM Export Groups as JPG"
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

    def wait_for_krita_then_refresh(self, doc, sleep_time=0.01):
        # doc.waitForDone()
        # doc.refreshProjection()
        doc.waitForDone()
        time.sleep(sleep_time)

    def wait_for_krita(self, doc, sleep_time=0.01):
        doc.waitForDone()
        # time.sleep(sleep_time)

    def set_visibility_recursively(self, node, visible, doc):
        node.setVisible(visible)
        self.wait_for_krita(doc)
        for child in node.childNodes():
            self.set_visibility_recursively(child, visible, doc)

    def set_visibility(self, node, visible, doc):
        node.setVisible(visible)
        self.wait_for_krita(doc)

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
        self.wait_for_krita_then_refresh(doc=doc)
        Krita.instance().action("flatten_layer").trigger()
        self.wait_for_krita_then_refresh(doc=doc)

        # Export the flattened image
        self.wait_for_krita(doc=doc)
        doc.setBatchmode(True)  # Suppress dialog box
        saved = doc.exportImage(export_file, jpgOptions)
        self.wait_for_krita(doc=doc)
        if not saved:
            print(f"Failed to export {export_file}")

    def save_as_kra_dialog(self, doc, start_directory=""):
        if not doc:
            QMessageBox.warning(None, "Error", "No document to save!")
            return

        # Get save path from dialog
        file_path, _ = QFileDialog.getSaveFileName(
            Krita.instance().activeWindow().qwindow(),
            "Save Krita Document",
            start_directory,
            "Krita Files (*.kra);;All Files (*)",
        )

        if file_path:
            # Ensure .kra extension
            if not file_path.lower().endswith(".kra"):
                file_path += ".kra"

            success = doc.saveAs(file_path)
            if success:
                QMessageBox.information(None, "Success", f"Saved as: {file_path}")
            else:
                QMessageBox.critical(None, "Error", "Save failed!")

    def export_groups_as_jpg(self):
        if (
            QMessageBox.question(
                None,
                "Exporting All Groups as Jpg!!",
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.No
        ):
            return

        doc = Krita.instance().activeDocument()
        if not doc:
            QMessageBox.warning(None, "Error", "No active document found!")
            return

        self.wait_for_krita_then_refresh(doc)

        # file name
        kra_full_path = doc.fileName()  # Full path to the .kra file
        kra_file_name = os.path.basename(kra_full_path)  # Just the file name
        kra_folder = os.path.dirname(kra_full_path)  # Folder containing the .kra file

        # start directory
        start_directory = ""
        if "ink" in kra_file_name:
            start_directory = (
                "C:\\PROJECTS\\Tee_Companies\\02_Ink Coton LLC Ebru\\1WORK\\1OUTPUT"
            )
        elif "pn" in kra_file_name:
            start_directory = (
                "C:\\PROJECTS\\Tee_Companies\\01_Play Nexus LLC OFM\\0work\\1output"
            )
        else:
            start_directory = ""

        # save orginal file first
        self.save_as_kra_dialog(doc, kra_folder)
        self.wait_for_krita_then_refresh(doc)

        # ask for export path
        export_path = QFileDialog.getExistingDirectory(
            None,  # parent widget (None = main window)
            "Select Export Folder",  # dialog title
            start_directory,  # starting directory ("" = last used)
            QFileDialog.ShowDirsOnly,  # only allow selecting folders
        )
        if not export_path:
            QMessageBox.warning(None, "Error", "No export path found!")
            return

        # jpg export folder path
        export_path = os.path.join(export_path, kra_file_name)

        # Ensure export folder exists
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        # progress bar
        total_groups = sum(
            1 for node in doc.rootNode().childNodes() if node.type() == "grouplayer"
        )
        progress = QProgressDialog("Exporting Groups...", "Cancel", 0, total_groups)
        progress.setWindowTitle("Batch Export")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # Hide all groups first
        for n in doc.rootNode().childNodes():
            if n.type() == "grouplayer":
                self.set_visibility(n, False, doc)
        self.wait_for_krita(doc)

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

        # progress cancel
        if progress.wasCanceled():
            QMessageBox.information(None, "Cancelled", "Export cancelled by user.")
            return  # Exit the loop immediately

        # progress
        progress.close()
        QMessageBox.information(None, "Done", "All groups exported as JPG!")
