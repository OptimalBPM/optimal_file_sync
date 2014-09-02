from functools import partial
import sys
from threading import Timer, Thread
from time import sleep
from kivy.clock import Clock, ClockBase, mainthread
from kivy.lib import osc
from kivy.utils import platform
from syncjob import SyncJob
import socket
import fcntl
import struct
import re
from io import StringIO
from time import strftime

# Conditional imports

if platform != "android":
    import netifaces

if sys.version_info.major == 2:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

__author__ = "Nicklas Boerjesson"

from plyer import notification


def is_valid_ipv4(ip):
    """Validates IPv4 addresses.
    """
    pattern = re.compile(r"""
        ^
        (?:
          # Dotted variants:
          (?:
            # Decimal 1-255 (no leading 0's)
            [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
          |
            0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
          |
            0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
          )
          (?:                  # Repeat 0-3 times, separated by a dot
            \.
            (?:
              [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
            |
              0x0*[0-9a-f]{1,2}
            |
              0+[1-3]?[0-7]{0,2}
            )
          ){0,3}
        |
          0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
        |
          0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
        |
          # Decimal notation, 1-4294967295:
          429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
          42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
          4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
        )
        $
    """, re.VERBOSE | re.IGNORECASE)
    return pattern.match(ip) is not None


def read_default_dir():
    import os

    return os.path.dirname(__file__)


class SyncService(object):
    timer = None
    cfg = None
    oscid = None
    stopped = None
    clock = None
    jobs = {}
    curr_progress = None
    curr_status = None

    def __init__(self, _cfg_file=None):

        super(SyncService, self).__init__()

        # notification.notify("Optimal File Sync Service", "Initializing service.")
        try:

            osc.init()
            self.send_status("Initializing")

            self.jobs = {}
            self.cfg = self.read_config(_cfg_file)
            self.clock = ClockBase()

        except  Exception as e:
            notification.notify("Optimal File Sync Service", "Error initiating service: " + str(e))


    def start(self, _start_job=False):

        self.stopped = False

        try:
            self.oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
            osc.bind(self.oscid, self.return_status, '/status')
            osc.bind(self.oscid, self.return_progress, '/progress')
            osc.bind(self.oscid, self.run_job_osc, '/run_job')
            osc.bind(self.oscid, self.stop, '/stop')
        except Exception as e:
            notification.notify("Optimal File Sync Service", "Error starting listener: " + str(e))
        self.send_status("Running")

        if _start_job:
            try:
                self.run_job(_start_job)
            except Exception as e:
                notification.notify("Optimal File Sync Service", "Error starting job: " + str(e))

        while self.stopped == False:
            try:
                sleep(0.01)
                self.clock.tick()
                self.process_messages()
            except Exception as e:
                notification.notify("Optimal File Sync Service", "Internal error, error in message loop:" + str(e))
                self.send_progress("Internal error, error in message loop:" + str(e))

        notification.notify("Optimal File Sync Service", "Service is shut down")
        self.send_status("Service is shut down.")
        exit(0)


    def process_messages(self):
        try:
            osc.readQueue(self.oscid)
        except  Exception as e:
            notification.notify("Optimal File Sync Service", "Error handling request: " + str(e))


    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def _find_active_interface_address(self, _job):

        _active_ip = None
        _if_name = None
        if platform == "android":

            try:
                _active_ip = str(self.get_ip_address("wlan0"))
                _if_name = "wlan0"
            except:
                try:
                    _active_ip = str(self.get_ip_address("tiwlan0"))
                    _if_name = "tiwlan0"
                except Exception as e:
                    return None

            if is_valid_ipv4(_active_ip) and _active_ip[0:5] != "127.0":
                if _job.trigger == "same_subnet":
                    if is_valid_ipv4(_job.destination_hostname):
                        _destination_ip = _job.destination_hostname
                    else:
                        # Lookup remote IP to be able to discern subnet
                        _destination_ip = socket.gethostbyname(_job.destination_hostname)

                    # Only return if the IP is local
                    if _destination_ip is not None and _active_ip.split(".")[0:2] == _destination_ip.split(
                            ".")[0:2]:
                        return _active_ip
                else:
                    return _active_ip
        else:
            _interfaces = netifaces.interfaces()
            for _curr_interface in _interfaces:
                if (
                            (_curr_interface[0:5] == "tiwlan" or
                                     _curr_interface[0:4] == "wlan")
                        and
                            (
                                    # Exclude XEN virtualization host stuff and loopback for testing on stationary Linux dev
                                    # boxes.
                                    _curr_interface[0:5] != "virbr" and
                                            _curr_interface != "lo")
                ):
                    _addrs = netifaces.ifaddresses(_curr_interface)
                    if _addrs.has_key(netifaces.AF_INET):
                        for _curr_address in _addrs[netifaces.AF_INET]:
                            _active_ip = _curr_address['addr']
                            if is_valid_ipv4(_active_ip) and _active_ip[0:5] != "127.0":
                                if _job.trigger == "same_subnet":
                                    if is_valid_ipv4(_job.destination_hostname):
                                        _destination_ip = _job.destination_hostname
                                    else:
                                        # Lookup remote IP to be able to discern subnet
                                        _destination_ip = socket.gethostbyname(_job.destination_hostname)

                                    # Only return if the IP is local
                                    if _destination_ip is not None and _active_ip.split(".")[
                                                                       0:2] == _destination_ip.split(
                                            ".")[0:2]:
                                        return _active_ip
                                else:
                                    return _active_ip
        return None


    def run_job_once(self, _job, *args):
        # TODO: Find out why *args is needed, why does clock supply
        # the mysterious extra argument included even if partial is not.
        _job.running = True
        try:
            if self.stopped is False:
                try:
                    # Checks the IP address against trigger
                    _active_IP = self._find_active_interface_address(_job)
                except Exception as e:
                    notification.notify("Optimal File Sync Service", "Error checking IP: " + str(e))
                    raise Exception(e)

            if self.stopped is False and _active_IP is not None:
                try:
                    # Execute the job action
                    _job.execute(_job)
                except socket.error as e:
                    _job.service.send_progress("Error in connection to server :" + str(e))
                except Exception as e:
                    _job.service.send_progress("Error running sync job : " + str(e))
            _job.running = False
        except:
            _job.running = False
            raise


    def run_job_osc(self, *args):
        # Parse name
        try:
            notification.notify("Optimal File Sync Service", "Starting job: " + str(args))
            _name = str(args[0][2])
            self.run_job(_name)

        except Exception as e:
            self.send_status("Failed running job " + str(e))

    def run_job(self, _name):

        try:
            _job = self.jobs[_name]
        except KeyError:
            _job = SyncJob.parse(self.cfg, _name)
            _job.service = self
            self.jobs[_name] = _job

        # Run the job the first time
        self.run_job_once(_job)
        # Schedule the rest of the occurrences.
        try:

            if self.stopped == False:
                _job.clock_event = self.clock.schedule_interval(callback=partial(self.run_job_once, _job),
                                                                timeout=int(_job.frequency))
        except Exception as e:
            self.send_status("Failed to schedule job " + str(e))

    def stop(self, *args):
        self.send_progress("Shutting down jobs")
        try:
            for _curr_job_name, _curr_job in self.jobs.items():
                if _curr_job.running:
                    _curr_job.stopped = True
                    self.send_progress("Shutting down job " + _curr_job_name)
                    if _curr_job.clock_event is not None:
                        try:
                            _curr_job.clock_event.cancel()
                        except:
                            pass
                    if _curr_job.smb_connection_destination is not None:
                        _curr_job.smb_connection_destination.is_busy = False
                        _curr_job.smb_connection_destination.close()
            _seconds = 10
            while len([v for x, v in self.jobs.items() if v.running == True]) > 0 and _seconds > 0:
                self.process_messages()
                self.send_progress("All jobs told to shut down, waiting for " + str(_seconds) +" more seconds ")
                sleep(1)
                _seconds-=1
            self.stopped = True
        except Exception as e:
            self.send_progress("Shutting down jobs failed, error:" + str(e))
            self.stopped = True

        self.send_progress("All jobs shut down.")

    def return_progress(self, *args):
        osc.sendMsg(oscAddress='/progress_callback', ipAddr="0.0.0.0", dataArray=[str(self.curr_progress), ],
                    port=3002)

    def send_progress(self, _progress):
        self.curr_progress = strftime("%Y-%m-%d %H:%M:%S") + ": " + _progress
        self.return_progress()


    def return_status(self, *args):
        osc.sendMsg(oscAddress='/status_callback', ipAddr="0.0.0.0", dataArray=[str(self.curr_status), ],
                    port=3002)

    def send_status(self, _status):
        self.curr_status = strftime("%Y-%m-%d %H:%M:%S") + ": " + _status
        self.return_status()

    def parse_status(self, _configdata):
        """
        Parse a config file from a string
        :param _configdata: A string of config data
        :return: Return an instance of ConfigParser
        """
        _config = ConfigParser.ConfigParser()
        _config.readfp(open(StringIO(_configdata)))

        return _config

    def read_config(self, _cfg_file):

        _cfg = ConfigParser()
        _cfg.read(filenames=[_cfg_file])
        return _cfg
