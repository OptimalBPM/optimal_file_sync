from kivy.properties import StringProperty

from service.lib.filesystemsmb import FileSystemSMB
from gui.dirselector import DirSelector


class SMBSelector(DirSelector):

    def init_selector(self, _height):
        _selector = super(SMBSelector, self).init_selector(_height)
        # Change the underlying file system
        self.do_on_status("")
        try:
            _selector.file_system = FileSystemSMB()
            _selector.file_system.connect(_hostname =  self.host, _username= self.username, _password= self.password,
                                          _on_status = self.on_status)
        except Exception as e:
            self.do_on_status(str(e))
            return False

        return _selector


    def after_hide_selector(self):
        """Unloads the file system, we possibly want to reconnect with new credentials later"""
        self.selector.file_system.disconnect()
        self.selector = None

    def set_path(self,_path):
        if _path.replace("/", "") == "":
            return False

        try:
            self.selector.path = _path
        except Exception as e:
            self.do_on_status(str(e))
            return False

        return True

    host = StringProperty()
    username = StringProperty()
    password = StringProperty()


