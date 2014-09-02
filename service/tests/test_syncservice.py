import subprocess
import sys
from time import sleep
from kivy.lib import osc

from service.syncservice import SyncService

if sys.version_info.major == 2:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

__author__ = 'Nicklas Boerjesson'

import unittest
from service.syncjob import SyncJob

from filecmp import cmp


import os
Test_Script_Dir = os.path.dirname(__file__)
Test_Resource_Dir = os.path.join(Test_Script_Dir, 'resources')

def _read_parser_single():
    _cfg = ConfigParser()
    _cfg.read(filenames = [Test_Resource_Dir + "/optimal_file_sync_single_job.txt"])
    return _cfg

def _read_parser_multiple():
    _cfg = ConfigParser()
    _cfg.read(filenames = [Test_Resource_Dir + "/optimal_file_sync_multiple_jobs.txt"])
    return _cfg


class Test_SyncService(unittest.TestCase):

    test_2_success = None



    def _status_result(self, _message, *args):

        if _message[2] == "Optimal File Sync service is running":
            self.test_2_result = True
        else:
            self.test_2_result = str(_message)

    def test_1_test_service_direct(self):
        _service = SyncService(_cfg_file = Test_Resource_Dir + "/optimal_file_sync_multiple_jobs.txt")
        _service.start(_start_job = "LocalToSMB")

    def _test_2_test_service_control(self):
        # Run main
        _proc = subprocess.Popen(args = ["python", os.path.normpath(Test_Script_Dir + "/../main.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


        # Connect to it and sent message

        osc.init()
        self.oscid = osc.listen(ipAddr='0.0.0.0', port=3002)
        osc.bind(self.oscid, self._status_result, '/status')

        self.test_2_result = None
        sleep(1)
        osc.sendMsg(oscAddress ='/status', ipAddr="0.0.0.0", dataArray=[""], port=3000)

        while self.test_2_result is None:
            osc.readQueue(self.oscid)
            sleep(.1)
        if self.test_2_result is True:
            self.assertTrue(True)
        else:
            self.assertTrue(False, "Test failed, service returned:" + str(self.test_2_result))

        osc.sendMsg(oscAddress ='/stop', ipAddr="0.0.0.0", dataArray=[], port=3000)
        osc.dontListen(self.oscid)
        #_proc.terminate()

    def _test_3_test_service_job(self):
        # Run main
        _proc = subprocess.Popen(args = ["python", os.path.normpath(Test_Script_Dir + "/../main.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Connect to it and sent message

        osc.init()
        self.oscid = osc.listen(ipAddr='0.0.0.0', port=3002)
        osc.bind(self.oscid, self._status_result, "/status")

        sleep(1)

        osc.sendMsg(oscAddress ='/run_job', ipAddr="0.0.0.0", dataArray=["Default", ], port=3000)

        sleep(10)

        osc.sendMsg(oscAddress ='/stop', ipAddr="0.0.0.0", dataArray=[], port=3000)
        #osc.dontListen(self.oscid)

if __name__ == '__main__':
    unittest.main()
