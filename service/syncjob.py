from ConfigParser import ConfigParser
import StringIO
import os
import datetime

from lib.smbutils import smb_connect
from lib.synctools import read_string_file_smb, walk_smb, walk_local, copy_files, write_string_file_smb


__author__ = 'Nicklas Boerjesson'

class SyncJob(object):
    """
    This class defines syncronization job
    """
    name = None
    """The name of the job"""
    type = None
    """The type of the job - can be "sync" """
    trigger = None
    """What triggers the job - can be "can_reach", "same_subnet","schedule" """
    frequency = None
    """How often should the trigger be checked in seconds"""


    source_settings = None
    """Any special settings the source may have"""
    source_folder = None
    """The folder of the source files"""
    source_hostname = None
    """The host name of the source. This is set if the source is a remote host"""
    source_username = None
    """If needed, the user name needed to connect to the source file location"""
    source_password = None
    """If needed, the password needed to connect to the source file location"""


    destination_settings = None
    """Any special settings the destination may have"""
    destination_folder = None
    """The folder of the destination files"""
    destination_hostname = None
    """The host name of the destination. This is set if the destination is a remote host"""
    destination_username = None
    """If needed, the user name needed to connect to the destination file location"""
    destination_password = None
    """If needed, the password needed to connect to the destination file location"""

    smb_connection_destination = None
    """The destination connection."""


    service = None
    """The service under which the job is running"""
    stopped = None
    """If True, the service has been told to stop"""
    running = None
    """If true, the job is running. Not to be confused with stopped, which means that the job has been told to stop,
    not that it is running"""

    def process_messages(self):
        """Forward request to process messages to service"""
        if self.service is not None:
            self.service.process_messages()

    @classmethod
    def parse(self, _parser, _jobname):
        """
        Parse settings from Config parser object
        :param _parser: Parser object
        :param _jobname: Name of the job. Without the "job_"-prefix
        """
        _jobsection = "Job_"+_jobname
        if _parser.has_section(_jobsection):
            _job = SyncJob()
            _job.name = _jobname
            _job.type = _parser.get(_jobsection, "type")
            _job.trigger = _parser.get(_jobsection, "trigger")
            _job.frequency = _parser.get(_jobsection, "frequency")
            _job.source_hostname = _parser.get(_jobsection, "source_hostname")
            _job.source_settings = _parser.get(_jobsection, "source_settings")
            _job.source_folder = _parser.get(_jobsection, "source_folder")
            _job.source_username = _parser.get(_jobsection, "source_username")
            _job.source_password = _parser.get(_jobsection, "source_password")
            _job.destination_hostname = _parser.get(_jobsection, "destination_hostname")
            _job.destination_settings = _parser.get(_jobsection, "destination_settings")
            _job.destination_folder = _parser.get(_jobsection, "destination_folder")
            _job.destination_username = _parser.get(_jobsection, "destination_username")
            _job.destination_password = _parser.get(_jobsection, "destination_password")
            return _job
        else:
            raise Exception("The job \"" + _jobsection + "\" isn't defined.")

    @classmethod
    def encode(self, _parser, _job):
        """
        Write settings to Config parser object
        :param _parser: Parser object
        :param _job: An instance of SyncJob
        """
        _jobsection = "Job_"+_job.name
        if not _parser.has_section(_jobsection):
            _parser.add_section(_jobsection)

        _parser.set(_jobsection, "type", _job.type)
        _parser.set(_jobsection, "trigger", _job.trigger)
        _parser.set(_jobsection, "frequency", _job.frequency)
        _parser.set(_jobsection, "source_hostname", _job.source_hostname)
        _parser.set(_jobsection, "source_settings", _job.source_settings)
        _parser.set(_jobsection, "source_folder", _job.source_folder)
        _parser.set(_jobsection, "source_username", _job.source_username)
        _parser.set(_jobsection, "source_password", _job.source_password)
        _parser.set(_jobsection, "destination_hostname", _job.destination_hostname)
        _parser.set(_jobsection, "destination_settings", _job.destination_settings)
        _parser.set(_jobsection, "destination_folder", _job.destination_folder)
        _parser.set(_jobsection, "destination_username", _job.destination_username)
        _parser.set(_jobsection, "destination_password", _job.destination_password)

    @classmethod
    def read_last_synced(self, _job, _smb_connection=None):
        """
        Read the date and time from the last_synced property of the destination status file
        :param _job: A SyncJob instance
        :param _smb_connection: An SMB connection.
        :return:
        """
        _cfg = ConfigParser()
        _file_obj = None
        # Is it a remote host?
        if _smb_connection is not None:
            _file_obj = read_string_file_smb(_smb_connection, os.path.join(_job.destination_folder, 'ofs_status.txt'))
        else:
            try:
                _file_obj = open(os.path.join(_job.destination_folder, 'ofs_status.txt'), "r")
            except IOError:
                _file_obj = None

        if _file_obj:
            _cfg.readfp(_file_obj)
            _file_obj.close()
            _result = _cfg.get("history", "last_synced")
            if _result is not None:
                return datetime.datetime.strptime(_result, "%Y-%m-%d %H:%M:%S.%f")
        else:
            return None


    @classmethod
    def write_last_synced(self, _value, _job, _new, _smb_connection=None):
        """
        Write _value to the last_synced property of the destination status file
        :param _value: The value to write
        :param _job: A SyncJob instance
        :param _new: If there isn't already a history-section
        :param _smb_connection: An SMB connection.
        :return:
        """
        if _new is None:
            if _smb_connection is not None:
                _file_obj = read_string_file_smb(_smb_connection, os.path.join(_job.destination_folder, 'ofs_status.txt'))
            else:
                try:
                    _file_obj = open(os.path.join(_job.destination_folder, 'ofs_status.txt'), "r")
                except IOError:
                    pass
        else:
            _file_obj = StringIO.StringIO()

        _cfg = ConfigParser()
        _cfg.readfp(_file_obj)
        if _new is not None:
            _cfg.add_section("history")

        _cfg.set("history", "last_synced", _value)
        _cfg.write(_file_obj)

        if _smb_connection is not None:
            write_string_file_smb(_smb_connection, os.path.join(_job.destination_folder, 'ofs_status.txt'), _file_obj)
        else:
            try:
                _file = open(os.path.join(_job.destination_folder, 'ofs_status.txt'), "r")
            except IOError:
                pass

    @classmethod
    def gather_files(self, _job, _start_date):
        """
        List all source files
        :param _job: An instance of SyncJob
        :param _start_date: The modified date from when to backup
        """

        if _job.source_hostname  and _job.source_hostname != "":
            _file = read_string_file_smb(os.path.join(_job.destination_folder, 'ofs_status.txt'))
        else:
            _file = open(os.path.join(_job.destination_folder, 'ofs_status.txt'), "r")

    @classmethod
    def execute(self, _job):
        """
        Executes the supplied job
        :param _job: SyncJob - An instance of a sync job.
        :return: Boolean - True if successful
        """

        if _job.name is not None:
            _job.service.send_progress('Job started: ' + _job.name )

        if _job.source_hostname is not None and _job.source_hostname != "":
            try:
                _smb_connection_source = smb_connect(_job.source_hostname, _job.source_username, _job.source_password)
            except Exception as e:
                raise Exception("Optimal File Sync Service", "job.execute, error connecting to source SMB share at " + _job.source_hostname + ": Error" + str(e))
        else:
            _smb_connection_source = None

        if _job.destination_hostname is not None and _job.destination_hostname != "":
            try:
                _smb_connection_destination = smb_connect(_job.destination_hostname, _job.destination_username, _job.destination_password)
                if self is not None:
                    self.smb_connection_destination = _smb_connection_destination
            except Exception as e:
                raise Exception("Optimal File Sync Service", "job.execute, error connecting to destination SMB share at " + _job.destination_hostname + ": Error" + str(e))
        else:
            _smb_connection_destination = None

        # Set _last_sync_datetime to before all operations
        _new_sync_datetime = datetime.datetime.now()

        # List all source files
        if _smb_connection_source:
            _filelist = walk_smb(_job.source_folder, _smb_connection_source)
        else:
            _filelist = walk_local(_job.source_folder)

        _files_to_exclude=[os.path.join(_job.source_folder, "ofs_status.txt")]

        # Remove directories
        for _curr_file in _filelist:
            if _curr_file[1] == True:
                _files_to_exclude.append(_curr_file)

        # Remove temp_video file
        for _curr_file in _filelist:
            if _curr_file[0].find('temp_video') > -1:
                _files_to_exclude.append(_curr_file)


        if _job.type == 'incremental':
            try:
                # Load _last_sync_datetime  from ofs_status,txt-file in destination
                _last_sync_datetime = SyncJob.read_last_synced(_job, _smb_connection_destination)
            except Exception as e:
                raise Exception("Optimal File Sync Service", "job.execute, reading status file at " + _job.destination_hostname + ": Error" + str(e))

            if _last_sync_datetime is not None:
                # Filter out all files that need not be updated
                for _curr_file in _filelist:
                    if _curr_file[3] <= _last_sync_datetime:
                        _files_to_exclude.append(_curr_file)

        _final_filelist = [item for item in _filelist if item not in _files_to_exclude]
        _source_files = []
        _destination_files = []

        # Make source and destination lists
        for _curr_file in _final_filelist:
            _source_files.append(_curr_file[0])
            _destination_files.append(os.path.join(_job.destination_folder, os.path.relpath(_curr_file[0],
                                                                                            _job.source_folder)))

        try:
            # Copy selected files
            if _smb_connection_source is not None:
                _result = copy_files(_source_paths= _source_files, _destination_paths= _destination_files, _context= "smbtolocal",
                           _smb_connection = _smb_connection_source, _job = _job)

            elif _smb_connection_destination is not None:
                _result = copy_files(_source_paths= _source_files, _destination_paths= _destination_files, _context= "localtosmb",
                           _smb_connection =  _smb_connection_destination, _job = _job)
            else:
                _result = copy_files(_source_paths= _source_files, _destination_paths=_destination_files, _context="localtolocal",
                           _job = _job)

            # _result is false when it has been stopped or encountered some other problem, however nothing serious enough
            # to raise an error for.
            if _result is True:
                try:
                    # Upload _last_sync_datetimes file
                    SyncJob.write_last_synced(_value=_new_sync_datetime, _job=_job, _new=(_last_sync_datetime is None), _smb_connection=_smb_connection_destination)
                except Exception as e:
                    raise Exception("job.execute, error writing status file to destination host(" + _job.source_hostname +  "): Error" + str(e))
        except Exception as e:
            raise Exception("job.execute, error copying files from " + _job.source_folder + " to " + _job.destination_folder +  ": Error" + str(e))



        # Close all SMB connections
        if _smb_connection_source is not None:
            try:
                _smb_connection_source.close()
            except Exception as e:
                raise Exception("job.execute, error closing source connection to " + _job.source_hostname +  ": Error" + str(e))

        if _smb_connection_destination is not None:
            try:
                _smb_connection_destination.close()
            except Exception as e:
                raise Exception("job.execute, error closing source connection to " + _job.destination_hostname +  ": Error" + str(e))


        _job.running = False
