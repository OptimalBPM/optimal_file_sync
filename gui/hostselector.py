
from kivy.adapters.args_converters import list_item_args_converter
from kivy.uix.listview import ListView, ListItemButton
from kivy.adapters.listadapter import ListAdapter
from expandselector import ExpandSelector

from ScanNetworkForSMB import NonBlockingNetBIOS

class HostSelector(ExpandSelector):

    def __init__(self, **kwargs):
        """Constructor"""
        super(HostSelector, self).__init__(**kwargs)
        self.closeup_on_select = True

    def get_values_hosts(self):
        """Looks through the subnet for SMB-hosts"""
        _nmb = NonBlockingNetBIOS()
        _hosts =  _nmb.list_all_hosts()
        _values = []
        for _curr_host in _hosts:
            _values.append(_curr_host[0] + ' (IP:' + _curr_host[1] + ', domain/workgroup = ' + _curr_host[2] +')')

        return _values

    def init_selector(self, _height):

        _list_adapter = ListAdapter(data=self.get_values_hosts(),
                           args_converter=list_item_args_converter,
                           cls=ListItemButton,
                           selection_mode='single',
                           allow_empty_selection=False)
        _selector = ListView(adapter=_list_adapter)
        _selector.height = _height

        _selector.adapter.bind(on_selection_change= self.set_selector_text)
        return _selector

    def set_selector_text(self, *args):
        if self.selector and len(self.selector.adapter.selection) > 0:
            self.selection = self.selector.adapter.selection[0].text.split(' ')[0]
            self.switch_selector()
        else:
            self.selection = ''


