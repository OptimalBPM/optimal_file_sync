

__author__ = 'Nicklas Boerjesson'

import unittest
from os import listdir, remove, rmdir

from lib.smbutils import smb_connect
from service.lib.synctools import copy_files, walk_local, walk_smb


local_source_files = ['resources/source/test_root.txt', 'resources/source/l1/l2_1/l2_1.txt']
local_destination_files = ['resources/destination/test_root.txt', 'resources/destination/l1/l2_1/l2_1.txt']
smb_destination_files = ['test/destination/test_root.txt', 'test/destination/l1/l2_1/l2_1.txt']


def get_connection():
    return smb_connect('fs01', 'tester', 'test')

def clear_smb(_conn=None):
    try:
        if _conn is None:
            _conn = get_connection()
        _conn.deleteFiles("test","destination/test_root.txt")
        _conn.deleteFiles("test","destination/l1/l2_1/l2_1.txt")
        _conn.deleteDirectory("test","destination/l1/l2_1")
        _conn.deleteDirectory("test","destination/l1")
        _conn.close()
    except:
        pass

def clear_local():
    try:
        remove("resources/destination/test_root.txt")
        remove("resources/destination/l1/l2_1/l2_1.txt")
        rmdir("resources/destination//l1/l2_1")
        rmdir("resources/destination//l1")
    except:
        pass

class TestSyncTools(unittest.TestCase):

    def _on_progress(self, _subject, _body):
        print("_subject:" + _subject + " _body:" + _body)

    def test_copy_files_local(self):
        clear_local()
        copy_files(_source_paths=local_source_files, _destination_paths=local_destination_files, _context = 'localtolocal', _on_progress=self._on_progress)
        self.assertEqual(listdir('resources/destination'), ['l1', 'test_root.txt'], "Files not matching expected result")
        clear_local()

    def test_copy_files_local_to_SMB_and_back(self):
        """To run this test you need a SMB server called FS01 with the appropriate shares, see get_connection()"""
        _connection = get_connection()
        clear_smb(_connection)

        copy_files(_source_paths=local_source_files, _destination_paths=smb_destination_files, _context = 'localtosmb',_smb_connection=_connection, _on_progress=self._on_progress)
        #self.assertEqual(listdir('resources/destination'),['test2.txt', 'test1.txt'], "Files not matching expected result")
        clear_local()
        copy_files(_source_paths=smb_destination_files, _destination_paths=local_destination_files, _context = 'smbtolocal',_smb_connection=_connection, _on_progress=self._on_progress)
        clear_smb(_connection)
        _connection.close()
        print(str([x[0:3] for x in walk_local('resources/destination')]))
        self.assertEqual(
        [
            ['resources/destination/l1', True, 0],
            ['resources/destination/test_root.txt', False, 0],
            ['resources/destination/l1/l2_1', True, 0],
            ['resources/destination/l1/l2_1/l2_1.txt', False, 9]
        ],
        [x[0:3] for x in walk_local('resources/destination')],
        "Files not matching expected result")
        clear_local()



    def test_walk_smb(self):
        _connection = get_connection()

        #print(str(walk_smb("test/l1", _connection)))
        self.assertEqual(
        [[u'test/l1/l2_1/l2_1.txt', False, 9],
            [u'test/l1/l2_1', True, 0],
            [u'test/l1/l2_2/l3_2_1', True, 0],
            [u'test/l1/l2_2', True, 0],
            [u'test/l1/L2_3/L2_3_1/L2_3_1.txt', False, 11],
            [u'test/l1/L2_3/L2_3_1', True, 0],
            [u'test/l1/L2_3', True, 0]
        ],
        [x[0:3] for x in walk_smb("test/l1", _connection)],
         "Directory structures differ"
        )

    def test_walk_local(self):
        _sorted = sorted([x[0:3] for x in walk_local("resources/source")], key=lambda i:i[0])
        print(str(_sorted))
        self.assertEqual(
        [
            ['resources/source/l1', True, 0],
            ['resources/source/l1/L2_3', True, 0],
            ['resources/source/l1/L2_3/L2_3_1', True, 0],
            ['resources/source/l1/L2_3/L2_3_1/L2_3_1.txt', False, 11],
            ['resources/source/l1/l2_1', True, 0],
            ['resources/source/l1/l2_1/l2_1.txt', False, 9],
            ['resources/source/l1/l2_2', True, 0],
            ['resources/source/l1/l2_2/l3_2_1', True, 0],
            ['resources/source/test_old.txt', False, 12],
            ['resources/source/test_root.txt', False, 0]
        ]
        ,
        _sorted,
         "Directory structures differ"
        )

if __name__ == '__main__':
    unittest.main()
