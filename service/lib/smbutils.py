__author__ = 'Nicklas Boerjesson'

from smb.SMBConnection import SMBConnection


def windowfy(_value):
    """
    Turn backslashes into forward slashes
    :param _value: A string value
    """
    return _value.replace("/", "\\")


def split_smb_path(_path):
    """
    Parse the Service name from a full path
    :param _path: A full SMB path ("/servicename/dir/subdir")
    :return: A tuple with service name and the path part
    """
    _splitted = _path.split("/")
    _service = _splitted[0]
    _remote_path = "/".join(_splitted[1:])
    return _service, _remote_path


def smb_connect(_hostname, _username, _password):
    """
    Connect to a SMB server and return a connection
    :param _hostname: The name of the host to connect to
    :param _username: The username
    :param _password: The password
    :return: Returns an instance of SMBConnection or raises an exception
    """
    _smb = SMBConnection(username=_username, password=_password, my_name='client', remote_name=_hostname)
    if _smb.connect(ip=_hostname) is True:
        return _smb
    else:
        raise Exception("SMB authentication failed")


def list_shares(_smb_connection):
    """List shares from the connected server.
    Don't confuse with FileSystemSMB.list_shares, they return slightly different fields
    :param _smb_connection: The SMB connection to use
    :return: A list of lists containing, filename, is directory, size, modified date
    """
    _shares = _smb_connection.listShares()
    _result = []
    for _curr_share in _shares:
        _result.append([_curr_share.name, True, 0, None])

    return _result

