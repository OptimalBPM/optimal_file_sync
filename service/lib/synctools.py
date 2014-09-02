import StringIO
import os
import datetime
import stat
from shutil import copyfile
from time import sleep

from smb.smb_constants import SMB_FILE_ATTRIBUTE_DIRECTORY
from smb.smb_structs import OperationFailure
from smb.SMBConnection import SMBConnection

from smbutils import list_shares, windowfy, split_smb_path


__author__ = 'Nicklas Boerjesson'

def read_string_file_smb(_smb_connection, _path):
    try:
        _file_obj = StringIO.StringIO()
        _service_name, _path = split_smb_path(_path)
        _smb_connection.retrieveFile(_service_name, _path, _file_obj)
        _file_obj.pos = 0
        return _file_obj
    except OperationFailure:
        return None
    except Exception as e:
        raise Exception("Error in read_string_file_smb(path = " +_path +") ("+ e.__class__.__name__+") : " + str(e) )

def write_string_file_smb(_smb_connection, _path, _file_obj):
    try:
        _service_name, _path = split_smb_path(_path)
        _file_obj.pos = 0
        _smb_connection.storeFile(_service_name, _path, _file_obj)
        _file_obj.close()
    except Exception as e:
        raise Exception("Error in write_string_file_smb(path = " +_path +") : " + str(e))

def walk_smb(_full_path, _smb_connection):
    """
    Recursively walks the file tree
    :param _full_path: The path to the root
    :param _smb_connection: An active SMBConnection
    :return:
    """
    try:
        _service_name, _path = split_smb_path(_full_path)
        if _service_name=="":
            return list_shares(_smb_connection)
        else:

            print("_service_name=" + _service_name+", _path=" + windowfy(_path))
            try:
                _files =_smb_connection.listPath(_service_name, windowfy(_path))
            except Exception as e:
                #raise Exception("Error listing contents of " + self.current_service + "\\"+ self.windowfy(self.current_dir) + ": " + e.message)
                print("Error listing contents of " + _service_name + "\\"+ windowfy(_path) + ": \n" + e.message)
                _files=[]

            _results = []
            for _file in  _files:
                if _file.filename not in ('..', '.'):
                    if SMB_FILE_ATTRIBUTE_DIRECTORY & _file.file_attributes == SMB_FILE_ATTRIBUTE_DIRECTORY:
                        _subtree = walk_smb(os.path.join(_full_path, _file.filename), _smb_connection)
                        _results+=_subtree

                    _results.append(
                        [
                            os.path.join(_full_path,_file.filename),
                            SMB_FILE_ATTRIBUTE_DIRECTORY & _file.file_attributes == SMB_FILE_ATTRIBUTE_DIRECTORY,
                            int(_file.file_size),
                            datetime.datetime.fromtimestamp(_file.last_write_time)
                        ])
            return _results
    except Exception as e:
        raise Exception("Error in walk_smb(path = " +_full_path +") : " + str(e))

def walk_local(_full_path):
    """
    Recursively walks the file tree
    :param _full_path: The path to the root
    :return:
    """
    try:
        _results = []
        for _root, _dirnames, _filenames in os.walk(_full_path):
            for _curr_dir in _dirnames:
                _curr_stat = os.stat(os.path.join(_root, _curr_dir))

                _results.append([os.path.join(_root, _curr_dir),
                                stat.S_ISDIR(_curr_stat.st_mode),
                                0,
                                datetime.datetime.fromtimestamp(_curr_stat.st_mtime)
                                ])
            for _curr_file in _filenames:

                _curr_stat = os.stat(os.path.join(_root, _curr_file))

                _results.append([os.path.join(_root, _curr_file),
                                stat.S_ISDIR(_curr_stat.st_mode),
                                _curr_stat.st_size,
                                datetime.datetime.fromtimestamp(_curr_stat.st_mtime)
                                ])
        return _results

    except Exception as e:
        raise Exception("Error in walk_smb(path = " +_full_path +") : " + str(e))



def blaze_trail_smb(_directory_path, _smb_connection, _do_progress=None):
    """

    :param _directory_path: A path to the directory
    :param _smb_connection: The SMBConnection to use
    :param _do_progress: A progress callback
    :return:
    """
    try:
        _service_name, _path = split_smb_path(_directory_path)

        _levels = _path.split("/")
        _so_far = ""
        for _curr_level in _levels:
            _so_far+=_curr_level
            try:
                _smb_connection.listPath(_service_name, _so_far)
            except :
                _do_progress("Creating remote directory: "+_directory_path)
                _smb_connection.createDirectory(_service_name, _so_far)
            _so_far+="/"
    except Exception as e:
        raise Exception("Error in blaze_trail_smb(path = " +_directory_path +") : " + str(e))

def blaze_trail_local(_path, _do_progress=None):
    try:
        if not os.path.exists(_path):
            _do_progress("Creating directory: "+ _path)
            os.makedirs(_path)
    except Exception as e:
        raise Exception("Error in blaze_trail_local(path = " +_path +") : " + str(e))

def copy_files(_source_paths,  _destination_paths, _context, _smb_connection = None , _job = None):
    def _do_progress(_message):
        if _job is not None:
            _job.service.send_progress(_message)

    def _process_messages():
        _job.process_messages()
        if _job is not None and _job.stopped is True:
            return True
        else:
            return False

    try:
        if _context in ('localtosmb','smbtolocal') and _smb_connection is None:
            raise Exception("Error in copy_files; contexts 'localtosmb' and 'smbtolocal' needs the _smb_connection argument to be set")

        _zipped_paths = zip(_source_paths, _destination_paths)
        _sorted_paths = sorted(_zipped_paths,key=lambda _zipped_paths: _zipped_paths[1])
        _last_destination_path = ''
        for _curr_source_path, _curr_destination_path in _sorted_paths:

            if _process_messages():
                return False

            _curr_path = os.path.dirname(_curr_destination_path)
            if _last_destination_path != _curr_path:
                # if it doesn't exists,
                if _context in ("localtolocal", "smbtolocal"):
                    blaze_trail_local(_curr_path, _do_progress)
                else:
                    blaze_trail_smb(_curr_path, _smb_connection, _do_progress)

            _do_progress("Copying " + _curr_destination_path)

            if _context == "localtolocal":
                copyfile(_curr_source_path, _curr_destination_path)
            else:
                if _context == "localtosmb":

                    _service_name, _path = split_smb_path(_curr_destination_path)
                    _file_obj = open(_curr_source_path, "r")

                    _retry_count = 3

                    try:
                        # If file exists, delete it
                        _smb_connection.deleteFiles(_service_name, _path)
                    except:
                        pass



                    while _retry_count > 0:
                        if _process_messages():
                            _file_obj.close()
                            return False
                        try:

                            _smb_connection.storeFile(_service_name, _path, _file_obj)
                            break
                        except:
                            sleep(2)
                            pass
                        _retry_count -= 1

                    _file_obj.close()
                    if _retry_count == 0:
                        raise Exception("Error in copy_files; failed to write " + _path )


                elif _context == "smbtolocal":
                    if _process_messages():
                        return False

                    _file_obj = open(_curr_destination_path, "w")
                    _service_name, _path = split_smb_path(_curr_source_path)
                    if _process_messages():
                        _file_obj.close()
                        return False

                    _smb_connection.retrieveFile(_service_name, _path, _file_obj)
                    _file_obj.close()

            _last_destination_path = _curr_path
    except Exception as e:
        raise Exception("Error in copy_files(first source path = " + str(_source_paths[0:1]) +
                        ", dest path = " + str(_source_paths[0:1]) + ", context = " + _context +") : " + str(e))
    return True