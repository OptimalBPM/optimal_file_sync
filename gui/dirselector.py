from kivy.uix.filechooser import FileChooserListView
from expandselector import ExpandSelector

class DirSelector(ExpandSelector):

    def init_selector(self, _height):
        _selector = FileChooserListView()
        _selector.height = _height
        _selector.dirselect = True
        _selector.bind(selection = self.set_selector_text)
        return _selector
