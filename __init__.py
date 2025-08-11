from .export_groups_as_jpg import Export_groups_as_jpg

# And add the extension to Krita's list of extensions:
app = Krita.instance()
# Instantiate your class:
extension = Export_groups_as_jpg(parent=app)
app.addExtension(extension)
