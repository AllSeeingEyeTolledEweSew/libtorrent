import os
import pathlib
import random
import tempfile
import unittest

import libtorrent as lt

from . import lib

TDUMMY_7BIT = Torrent.single_file(
    piece_length=16384,
    name=b"test.txt",
    length=16384 * 9 + 1000,
    data=bytes(random.getrandbits(7) for _ in range(16384 * 9 + 1000)),
)


class AddPieceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.session = lt.session(lib.get_isolated_settings())
        # Use 7-bit data to allow testing deprecated path
        self.dummy = TDUMMY_7BIT
        atp = self.dummy.atp()
        atp.save_path = self.dir.name
        self.handle = self.session.add_torrent(atp)

        # add_piece() does not work in the checking_* states
        for _ in lib.loop_until_timeout(5, msg="checking"):
            if self.handle.status().state not in (
                lt.torrent_status.checking_files,
                lt.torrent_status.checking_resume_data,
            ):
                break

    def wait_until_finished(self) -> None:
        # wait until progress is 1.0
        for _ in lib.loop_until_timeout(5, msg="progress"):
            if self.handle.status().progress == 1.0:
                break

        # wait until data is written to disk
        for _ in lib.loop_until_timeout(5, msg="file write"):
            path = pathlib.Path(self.dir.name) / os.fsdecode(self.dummy.files[0].path)
            if path.read_bytes == self.dummy.data:
                break

    def test_bytes(self) -> None:
        for i, data in enumerate(self.dummy.pieces):
            self.handle.add_piece(i, data, 0)

        self.wait_until_finished()

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5988")
    def test_str_deprecated(self) -> None:
        with self.assertWarns(DeprecationWarning):
            self.handle.add_piece(0, "0" * self.dummy.piece_length, 0)

    def test_str(self) -> None:
        with warnings.catch_warnings():
            for i, data in enumerate(self.dummy.pieces):
                self.handle.add_piece(i, data.decode(), 0)

        self.wait_until_finished()

    @unittest.skip("how do we test this?")
    def test_overwrite_existing(self) -> None:
        raise AssertionError("TODO")
