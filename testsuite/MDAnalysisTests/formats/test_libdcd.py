from __future__ import print_function

from nose.tools import raises
from numpy.testing import assert_equal, assert_array_equal
from numpy.testing import assert_array_almost_equal
from numpy.testing import assert_almost_equal

from MDAnalysis.lib.formats.libdcd import DCDFile
from MDAnalysisTests.datafiles import PSF, DCD

from unittest import TestCase
import MDAnalysis
from MDAnalysisTests.tempdir import run_in_tempdir
from MDAnalysisTests import tempdir
import numpy as np
import os

class DCDReadFrameTest(TestCase):

    def setUp(self):
        self.dcdfile = DCDFile(DCD)

    def tearDown(self):
        del self.dcdfile

    def test_read_coords(self):
        # confirm shape of coordinate data against result from previous
        # MDAnalysis implementation of DCD file handling
        dcd_frame = self.dcdfile.read()
        xyz = dcd_frame[0]
        assert_equal(xyz.shape, (3341, 3))

    def test_read_unit_cell(self):
        # confirm unit cell read against result from previous
        # MDAnalysis implementation of DCD file handling
        dcd_frame = self.dcdfile.read()
        unitcell = dcd_frame[1]
        expected = np.array([  0.,   0.,   0.,  90.,  90.,  90.],
                            dtype=np.float32)
        assert_equal(unitcell, expected)

    def test_seek_over_max(self):
        # should raise IOError if beyond 98th frame
        with self.assertRaises(IOError):
            self.dcdfile.seek(102)

    def test_seek_normal(self):
        # frame seek within range is tested
        new_frame = 91
        self.dcdfile.seek(new_frame)
        assert_equal(self.dcdfile.tell(), new_frame)

    def test_seek_negative(self):
        # frame seek with negative number
        with self.assertRaises(IOError):
            self.dcdfile.seek(-78)

    def test_iteration(self):
        self.dcdfile.__next__()
        self.dcdfile.__next__()
        self.dcdfile.__next__()
        expected_frame = 3
        assert_equal(self.dcdfile.tell(), expected_frame)

    def test_zero_based_frames(self):
        expected_frame = 0
        assert_equal(self.dcdfile.tell(), expected_frame)

    def test_length_traj(self):
        expected = 98
        assert_equal(len(self.dcdfile), expected)

    def test_context_manager(self):
        frame = 22
        with self.dcdfile as f:
            f.seek(frame)
            assert_equal(f.tell(), frame)

    @raises(IOError)
    def test_open_wrong_mode(self):
        DCDFile('foo', 'e')

    @raises(IOError)
    def test_raise_not_existing(self):
        DCDFile('foo')

    def test_n_atoms(self):
        assert_equal(self.dcdfile.n_atoms, 3341)

    @raises(IOError)
    @run_in_tempdir()
    def test_read_write_mode_file(self):
        with DCDFile('foo', 'w') as f:
            f.read()

    @raises(IOError)
    def test_read_closed(self):
        self.dcdfile.close()
        self.dcdfile.read()

    def test_iteration_2(self):
        with self.dcdfile as f:
            for frame in f:
                pass

class DCDWriteHeaderTest(TestCase):

    def setUp(self):
        self.tmpdir = tempdir.TempDir()
        self.testfile = self.tmpdir.name + '/test.dcd'
        self.dcdfile = DCDFile(self.testfile, 'w')
        self.dcdfile_r = DCDFile(DCD, 'r')

    def tearDown(self):
        try: 
            os.unlink(self.testfile)
        except OSError:
            pass
        del self.tmpdir
    
    def test_write_header_crude(self):
        # test that _write_header() can produce a very crude
        # header for a new / empty file
        self.dcdfile._write_header()
        self.dcdfile.close()

        # we're not actually asserting anything, yet
        # run with: nosetests test_libdcd.py --nocapture
        # to see printed output from nose
        with open(self.testfile, "rb") as f:
            for element in f:
                print(element)

    def test_write_header_mode_sensitivy(self):
        # an exception should be raised on any attempt to use
        # _write_header with a DCDFile object in 'r' mode
        with self.assertRaises(IOError):
            self.dcdfile_r._write_header()



class DCDWriteTest(TestCase):

    def setUp(self):
        self.tmpdir = tempdir.TempDir()
        self.testfile = self.tmpdir.name + '/test.dcd'
        self.dcdfile = DCDFile(self.testfile, 'w')
        self.dcdfile_r = DCDFile(DCD, 'r')
        self.traj = MDAnalysis.Universe(PSF, DCD).trajectory

    def tearDown(self):
        try: 
            os.unlink(self.testfile)
        except OSError:
            pass
        del self.tmpdir
        del self.traj

    def test_write_mode(self):
        # ensure that writing of DCD files only occurs with properly
        # opened files
        with self.assertRaises(IOError):
            self.dcdfile_r.write(np.zeros((3,3)), np.zeros(6, dtype=np.float64),
                                 0, 0.0, 330, 0)

    def test_write_dcd(self):
        with self.dcdfile_r as f_in, self.dcdfile as f_out:
            for frame in f_in:
                frame = frame._asdict()
                f_out.write(xyz=frame['x'],
                            box=frame['unitcell'].astype(np.float64),
                            step=0,
                            time=0.0,
                            natoms=frame['x'].shape[0],
                            charmm=0)

        with open(self.testfile, "rb") as f:
            for element in f:
                print(element)
            
