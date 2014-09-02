from functools import partial
import subprocess
from time import sleep
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.stacklayout import StackLayout
from service.lib.smbutils import smb_connect


__author__ = "Nicklas Boerjesson"

import ConfigParser
import re

from kivy.lib import osc
from kivy.utils import platform
platform = platform()

from kivy.lang import Builder

Builder.load_file("gui/settings.kv")

class SettingsFrame(StackLayout):
    test_service = None
    cfg_file = None
    service_status = None
    service_progress = None

    def init(self, _cfg_file=None):
        self.ids.destination_host.ids.input_selection.bind(text=self._update_host)
        self.ids.destination_path.on_status = self.do_on_smbselector_status
        self.load_settings(_cfg_file)
        self.service = None
        osc.init()
        self.oscid = osc.listen(port=3002)
        osc.bind(self.oscid, self.progress_callback, "/progress_callback")
        osc.bind(self.oscid, self.status_callback, "/status_callback")

        # Check if service is running
        self.service_running = False
        osc.sendMsg("/status", [], port=3000)
        osc.sendMsg("/progress", [], port=3000)
        sleep(0.3)
        osc.readQueue(self.oscid)


        Clock.schedule_interval(self.process_messages, 1)

    ####### Service #################
    #######################################################################################


    def do_on_smbselector_status(self, _message):
        self.ids.l_test_smbselector_result.text = re.sub("(.{40})", "\\1\n", _message, 0, re.DOTALL)
    def process_messages(self, *args):
        osc.readQueue(self.oscid)

    def status_callback(self, *args):
        self.service_running = True
        self.service_status = str(args[0][2])
        self.ids.label_status.text = self.service_status

    def progress_callback(self, *args):
        self.service_running = True
        self.service_progress = str(args[0][2])
        self.ids.label_progress.text = re.sub("(.{40})", "\\1\n", self.service_progress, 0, re.DOTALL)

    def start_service(self):
        self.save_settings()
        print("Starting service")
        self.service_running = False
        osc.sendMsg("/status", [], port=3000)
        osc.sendMsg("/progress", [], port=3000)
        sleep(0.1)
        osc.readQueue(self.oscid)
        if not self.service_status:
            # Wait a little longer and try again
            sleep(0.5)
            osc.readQueue(self.oscid)

        if not self.service_status:
            print("Start_service: Service is not running, starting")
            if self.service is None:

                if platform == "android":
                    from android import AndroidService
                    self.service = AndroidService("Optimal file sync service", "running")
                    self.service.start("service started")
                else:
                    # Start process on linux.
                    print("Running on !android initializing service using Popen.")
                    self.service = subprocess.Popen(args = ["python", "./service/main.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            print("Start_service: Service is already running, not starting.")


    def stop_service(self):
        print("Asking service to stop.")
        self.service_running = False

        osc.sendMsg("/status", [], port=3000)
        sleep(0.2)
        osc.readQueue(self.oscid)

        osc.sendMsg("/stop", [], port=3000)
        sleep(0.2)
        osc.readQueue(self.oscid)
        if self.service is not None and platform == "android":
            self.service.stop()
            self.service = None


    ####### GUI #################
    #######################################################################################

    def _update_host(self, *args):
        #TODO: Why the hell is this needed?
        self.ids.destination_path.host = self.ids.destination_host.ids.input_selection.text

    def reload_settings(self):
        self.load_settings(self.cfg_file)

    def load_settings(self, _cfg_file=None):
        self.cfg_file = _cfg_file
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(_cfg_file)

        self.ids.sourcedir_select.selection = cfg.get("Job_Default", "source_folder")
        self.ids.destination_host.selection = cfg.get("Job_Default", "destination_hostname")
        self.ids.destination_path.selection = cfg.get("Job_Default", "destination_folder")
        self.ids.destination_username.text = cfg.get("Job_Default", "destination_username")
        self.ids.destination_password.text = cfg.get("Job_Default", "destination_password")

    def save_settings(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(self.cfg_file)

        cfg.set("Job_Default", "source_folder", self.ids.sourcedir_select.selection)
        cfg.set("Job_Default", "destination_hostname", self.ids.destination_host.selection)
        cfg.set("Job_Default", "destination_folder", self.ids.destination_path.selection)
        cfg.set("Job_Default", "destination_username", self.ids.destination_username.text)
        cfg.set("Job_Default", "destination_password", self.ids.destination_password.text)
        f = open(self.cfg_file, "wb")
        cfg.write(f)
        f.close()

    def test_connection(self):
        try:
            self.ids.l_test_connection_result.text = "Testing..."
            _smb = smb_connect(_hostname=self.ids.destination_host.selection,
                               _username=self.ids.destination_username.text,
                               _password=self.ids.destination_password.text )
            self.ids.l_test_connection_result.text = "Connection successful!"
        except Exception as e:
            self.ids.l_test_connection_result.text = "Test failed, error connecting: " + str(e)

        try:
            _shares = _smb.listShares()
            self.ids.l_test_connection_result.text = "Listing shares (" + str(len(_shares)) + ") successful!"
        except Exception as e:
            self.ids.l_test_connection_result.text = "Test failed, error listing shares: " + str(e)




