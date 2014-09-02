import os

from kivy.uix.filechooser import FileSystemAbstract
from smb.smb_constants import SMB_FILE_ATTRIBUTE_DIRECTORY, SMB_FILE_ATTRIBUTE_HIDDEN

from service.lib.smbutils import windowfy, smb_connect, split_smb_path


class FileSystemSMB(FileSystemAbstract):
    smb = None
    current_dir = None
    current_service = None
    only_dir = None
    items = {"..": [True, False, 0]}
    on_status = None

    def do_on_status(self, _message):
        if self.on_status is not None:
            self.on_status(_message)

    def connect(self, _hostname, _username, _password, _on_status):
        self.on_status = _on_status
        self.do_on_status("")

        try:
            self.smb = smb_connect(_hostname, _username, _password)
        except Exception as e:
            self.do_on_status(str(e))
            return None

    def disconnect(self):
        try:

            self.smb.close()
        except Exception as e:
            self.do_on_status(str(e))
            return None
    def list_shares(self, _smb_connection):
        try:
            self.do_on_status("")
            _shares = _smb_connection.listShares()
            _result = []
            for _curr_share in _shares:
                _filename = str(_curr_share.name).encode('utf-8').replace('/', '')
                self.items[_filename] = [_curr_share.name, False, False, 0, None]
                _result.append(_curr_share.name)

            return _result
        except Exception as e:
            self.do_on_status(str(e))
            return []



    def listdir(self, _path):
        try:
            """Mimic the behaviour of a local folder on a SMB server by mixing service and path"""
            print("listdir - " + _path)
            _path = os.path.normpath(_path)
            # The notation of using a single dot to say that nothing should be done fades in comparison with...nothing.
            if _path == ".":
                # Setting an empty path results in listing the same dir again. This mimics os.listdir():s behaviour.
                _path = ''

            # Special case: If the path is *only* 'up', the top level is to also clear the current service
            if _path == "..":
                self.current_service = ''
                self.current_dir = ''
            else:
                # Remove the first slash as it just messes up the service name.
                if _path != "" and _path[0] == "/":
                    _path = _path[1:]

                # Parse the service from the path.
                self.current_service, self.current_dir = split_smb_path(_path)

            # It there is no service specified, list them.
            if self.current_service == '':
                self.current_dir == ''
                return self.list_shares(self.smb)
            else:

                print("self.current_service=" + self.current_service + ", windowfy(self.current_dir)=" + windowfy(
                    self.current_dir))
                try:
                    _files = self.smb.listPath(self.current_service, windowfy(self.current_dir))
                except Exception as e:
                    raise Exception("Error listing contents of " + self.current_service + "\\"+ windowfy(self.current_dir) + ": " + e.message)


                _results = []
                for _file in _files:
                    if _file.filename not in ('..', '.'):
                        _filename = str(
                            self.current_service.encode('utf-8') + self.current_dir.encode('utf-8') + _file.filename.encode(
                                'utf-8')).replace('/', '')
                        self.items[_filename] = \
                            [
                                SMB_FILE_ATTRIBUTE_DIRECTORY & _file.file_attributes == SMB_FILE_ATTRIBUTE_DIRECTORY,
                                SMB_FILE_ATTRIBUTE_HIDDEN & _file.file_attributes == SMB_FILE_ATTRIBUTE_HIDDEN,
                                int(_file.file_size)
                            ]
                        _results.append(_file.filename)
                print("Files " + str(_results))
                return _results
        except Exception as e:
            self.do_on_status(str(e))
            return []


    def is_hidden(self, _path):
        try:
            _file = self.items[str(_path.encode('utf-8')).replace('/', '').replace('..', '')]
            print("is_hidden - " + _path + " - " + str(_file[1]))
            return _file[1]
        except Exception as e:
            self.do_on_status(str(e))
            return None

    def is_dir(self, _path):
        try:
            if _path[0:2] == "..":
                return True

            _file = self.items[str(_path.encode('utf-8')).replace('/', '').replace('..', '')]
            print("is_dir - " + _path + " - " + str(_file[0]))
            return _file[0]
        except Exception as e:
            self.do_on_status(str(e))
            return None
    def getsize(self, _path):
        try:
            _file = self.items[str(_path.encode('utf-8')).replace('/', '').replace('..', '')]
            print("getsize - " + _path + " - " + str(_file[2]))
            return _file[2]

        except Exception as e:
            self.do_on_status(str(e))
            return None
