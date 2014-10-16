import os

from kivy.uix.filechooser import FileSystemAbstract
from smb.smb_constants import SMB_FILE_ATTRIBUTE_DIRECTORY, SMB_FILE_ATTRIBUTE_HIDDEN

from service.lib.smbutils import windowfy, smb_connect, split_smb_path


class FileSystemSMB(FileSystemAbstract):
    """This class is an implementation of FileSystemAbstract for SMB"""
    smb = None
    """A SMB connection"""
    current_dir = None
    """The current directory"""
    current_service = None
    """The current service(share)"""
    only_dir = None
    """Only select directories"""
    items = {"..": [True, False, 0]}
    """A list of the items in the directory"""
    on_status = None
    """Event triggered if the status is changed"""

    def do_on_status(self, _message):
        """
        Trigger the on_status event
        :param _message: Message to send
        :return:
        """
        if self.on_status is not None:
            self.on_status(_message)

    def connect(self, _hostname, _username, _password, _on_status):
        """
        Connect to the SMB server

        :param _hostname: The name of the host to connect to
        :param _username: The username
        :param _password: The password
        :param _on_status: A callback function to get status messages
        """
        self.on_status = _on_status
        self.do_on_status("")

        try:
            self.smb = smb_connect(_hostname, _username, _password)
        except Exception as e:
            self.do_on_status(str(e))
            return None

    def disconnect(self):
        """Disconnect from the SMB server"""
        try:

            self.smb.close()
        except Exception as e:
            self.do_on_status(str(e))
            return None

    def list_shares(self, _smb_connection):
        """
        List all shares of the connection. Provides a slightly different result set
        than the lib.smbutils.list_shares()
        :param _smb_connection: A SMB connection
        :return: A list of items describing the shares
        """
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
        """
        List the files in the path
        :param _path: Path to be listed
        :return: A list of items describing the items in the folder
        """
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
                    raise Exception("Error listing contents of " + self.current_service + "\\" +
                                    windowfy(self.current_dir) + ": " + e.message)

                _results = []
                for _file in _files:
                    if _file.filename not in ('..', '.'):
                        _filename = str(
                            self.current_service.encode('utf-8') + self.current_dir.encode('utf-8') +
                            _file.filename.encode('utf-8')).replace('/', '')
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
        """
        Check if an file system item has the "hidden" attribute
        :param _path: Path to item
        :return: True if hidden.
        """
        try:
            _file = self.items[str(_path.encode('utf-8')).replace('/', '').replace('..', '')]
            print("is_hidden - " + _path + " - " + str(_file[1]))
            return _file[1]
        except Exception as e:
            self.do_on_status(str(e))
            return None

    def is_dir(self, _path):
        """
        Check if an file system item is a directory
        :param _path: Path to item
        :return: True if it is a directory
        """
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
        """
        Return the size of an item.
        :param _path: Path to item
        :return: An integer containing the size of the item
        """
        try:
            _file = self.items[str(_path.encode('utf-8')).replace('/', '').replace('..', '')]
            print("getsize - " + _path + " - " + str(_file[2]))
            return _file[2]

        except Exception as e:
            self.do_on_status(str(e))
            return None
