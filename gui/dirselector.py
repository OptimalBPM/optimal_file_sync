from kivy.uix.filechooser import FileChooserListView
from expandselector import ExpandSelector

class DirSelector(ExpandSelector):
    """This selector is an ExpandSelector that selects directories"""

    def init_selector(self, _height):
        # Use a FileChooserListView for selector
        _selector = FileChooserListView()
        _selector.height = _height
        _selector.dirselect = True
        _selector.bind(selection = self.set_selector_text)
        return _selector
