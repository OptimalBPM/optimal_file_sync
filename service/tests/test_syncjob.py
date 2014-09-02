import sys

from service.lib.synctools import walk_local


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


class Test_SyncJob(unittest.TestCase):

    def test_1_parse_encode_sync_job(self):
        _job = SyncJob.parse(_read_parser_single(), "Local")
        self.assertEqual(_job.name, "Local", "Job name differs")
        self.assertEqual(_job.source_folder, "resources/source", "Source folder differs")
        _cfg = ConfigParser()
        _job.encode(_cfg, _job)
        _f = open(Test_Resource_Dir + "/destination/job_local.txt", "w")
        _cfg.write(_f)
        _f.close()
        self.assertTrue(cmp(Test_Resource_Dir + "/optimal_file_sync_single_job.txt",
                            Test_Resource_Dir + "/destination/job_local.txt",
                            shallow=True),
                        "The files differ")
        os.remove(Test_Resource_Dir + "/destination/job_local.txt")

    def test_2_execute_diff_job_localtosmb_smbtolocal(self):
        _job = SyncJob.parse(_read_parser_multiple(), "LocalToSMB")
        SyncJob.execute(_job)
        
        _job = SyncJob.parse(_read_parser_multiple(), "SMBToLocal")
        SyncJob.execute(_job)
        
        self.assertEqual(
        [
            ['resources/destination/l1', True, 0],
            ['resources/destination/ofs_status.txt', False, 52],
            ['resources/destination/l1/l2_1', True, 0],
            ['resources/destination/l1/L2_3', True, 0],
            ['resources/destination/l1/l2_1/l2_1.txt', False, 9],
            ['resources/destination/l1/L2_3/L2_3_1', True, 0],
            ['resources/destination/l1/L2_3/L2_3_1/L2_3_1.txt', False, 11]
        ],
        [x[0:3] for x in walk_local('resources/destination')],
        "Files not matching expected result")


if __name__ == '__main__':
    unittest.main()
