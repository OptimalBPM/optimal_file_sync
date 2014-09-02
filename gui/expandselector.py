import os
from kivy.properties import StringProperty, AliasProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout

from kivy.lang import Builder


Builder.load_file('gui/expandselector.kv')

class ExpandSelector(BoxLayout):
    """ExpandSelector is the superclass for all expanding selectors"""
    selector = None
    caption = None
    selection = None
    selector_height = None
    input_height = None
    font_size = None

    on_status = None

    def do_on_status(self, _message):
        if self.on_status is not None:
            self.on_status(_message)

    def __init__(self, **kwargs):
        """Constructor"""
        super(ExpandSelector, self).__init__(**kwargs)

    def init_selector(self, _height):
        pass

    def after_hide_selector(self):
        """Implement to add things to do after the selector has been hidden"""
        pass

    def recalc_layout(self):
        self.height = self.calc_child_height(self)

    def switch_selector(self):
        self.do_on_status("")
        if not self.selector:
            self.selector = self.init_selector(self.selector_height)

        if self.selector:
            self.selector.path = self.ids.input_selection.text

            if self.selector.parent:
                self.selector.parent.remove_widget(self.selector)
                self.after_hide_selector()
            else:
                self.add_widget(self.selector)

            self.recalc_layout()

    def calc_child_height(self, _widget):
        _result = 0
        for _curr_child in _widget.children:
            _result+= _curr_child.height
        return _result

    def set_path(self, _path):
        try:
            self.selector.path = _path
        except Exception as e:
            self.do_on_status(str(e))
            return False

        return True

    def set_selector_text(self, *args):

        if self.selector and len(self.selector.selection) > 0:
            _selection = self.selector.selection[0]

            if _selection[0:2] == "..":
                # If the "../" item has been clicked, go up one level.
                _resulting_path = os.path.split(self.selector.path)[0]
            else:
                # Otherwise, just set path
                _resulting_path = os.path.normpath(_selection)

            if self.set_path(_resulting_path):
                # Path accepted and set, reflect in input
                self.ids.input_selection.text = self.selector.path


    def _set_caption(self, _value):
        self.ids.selector_label.text = _value

    def _get_caption(self):
        return self.ids.selector_label.text

    def _set_selection(self, _value):
        self.ids.input_selection.text = _value

    def _get_selection(self):
        return self.ids.input_selection.text


    caption = AliasProperty(_get_caption, _set_caption)
    selection = AliasProperty(_get_selection, _set_selection)
    selector_height = NumericProperty(200)
    input_height = NumericProperty(60)
    font_size = NumericProperty(20)

