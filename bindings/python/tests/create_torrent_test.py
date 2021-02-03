import contextlib
import os
import pathlib
import tempfile
from typing import AnyStr
from typing import Callable
from typing import Iterator
from typing import Tuple
from typing import Union
import unittest
import unittest.mock
import warnings

import libtorrent as lt

from . import lib


class EnumTest(unittest.TestCase):
    def test_enums(self) -> None:
        self.assertIsInstance(lt.file_storage.flag_pad_file, int)
        self.assertIsInstance(lt.file_storage.flag_hidden, int)
        self.assertIsInstance(lt.file_storage.flag_executable, int)
        self.assertIsInstance(lt.file_storage.flag_symlink, int)

        self.assertIsInstance(lt.file_flags_t.flag_pad_file, int)
        self.assertIsInstance(lt.file_flags_t.flag_hidden, int)
        self.assertIsInstance(lt.file_flags_t.flag_executable, int)
        self.assertIsInstance(lt.file_flags_t.flag_symlink, int)

        with warnings.catch_warnings():
            self.assertIsInstance(lt.create_torrent.optimize_alignment, int)
            self.assertIsInstance(lt.create_torrent.merkle, int)
        self.assertIsInstance(lt.create_torrent.v2_only, int)
        self.assertIsInstance(lt.create_torrent.modification_time, int)
        self.assertIsInstance(lt.create_torrent.symlinks, int)

        with warnings.catch_warnings():
            self.assertIsInstance(lt.create_torrent_flags_t.optimize_alignment, int)
            self.assertIsInstance(lt.create_torrent_flags_t.merkle, int)
        self.assertIsInstance(lt.create_torrent_flags_t.v2_only, int)
        self.assertIsInstance(lt.create_torrent_flags_t.modification_time, int)
        self.assertIsInstance(lt.create_torrent_flags_t.symlinks, int)


class InputFileEntryTest(unittest.TestCase):
    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_deprecated(self) -> None:
        with self.assertWarns(DeprecationWarning):
            lt.file_entry()

    def test_usage(self) -> None:
        # It's not clear this has ever been useful, as the file size can't be modified
        with warnings.catch_warnings():
            fe = lt.file_entry()
            fe.path = "path/file.txt"
            fe.symlink_path = "path/other.txt"
            fe.file_hash = lt.sha1_hash(lib.get_random_bytes(20))
            fe.mtime = 123456


class InputFileStorageTest(unittest.TestCase):
    def test_is_valid(self) -> None:
        fs = lt.file_storage()
        self.assertFalse(fs.is_valid())

    def test_add_file_params(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/file1.txt", 1024)
        fs.add_file("path/file2.txt", 1024, 0)
        fs.add_file("path/file3.txt", 1024, flags=0)
        fs.add_file("path/file4.txt", 1024, 0, 10000)
        fs.add_file("path/file5.txt", 1024, 0, mtime=10000)
        fs.add_file("path/file6.txt", 1024, 0, 10000, "path/file1.txt")
        fs.add_file("path/file7.txt", 1024, 0, 10000, linkpath="path/file1.txt")
        self.assertEqual(fs.num_files(), 7)

    def test_num_files(self) -> None:
        fs = lt.file_storage()
        self.assertEqual(fs.num_files(), 0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_add_file_entry_deprecated(self) -> None:
        fs = lt.file_storage()
        with warnings.catch_warnings():
            fe = lt.file_entry()
        with self.assertWarns(DeprecationWarning):
            fs.add_file(fe)

    def test_add_file_entry(self) -> None:
        fs = lt.file_storage()
        # It's not clear this path has ever been useful, as the entry size can't
        # be modified
        with warnings.catch_warnings():
            fe = lt.file_entry()
            fe.path = "path/test.txt"
            fs.add_file(fe)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_at_deprecated(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        with self.assertWarns(DeprecationWarning):
            fs.at(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_at_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.at(0)
        with self.assertRaises(IndexError):
            fs.at(-1)

    def test_at(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        with warnings.catch_warnings():
            fe = fs.at(0)
        self.assertEqual(fe.path, "path/test.txt")
        self.assertEqual(fe.size, 1024)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_iter_deprecated(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        with self.assertWarns(DeprecationWarning):
            self.assertEqual([fe.path for fe in fs], ["path/test.txt"])

    def test_iter(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        with warnings.catch_warnings():
            self.assertEqual([fe.path for fe in fs], ["path/test.txt"])
            self.assertEqual([fe.size for fe in fs], [1024])

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_len_deprecated(self) -> None:
        fs = lt.file_storage()
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(len(fs), 0)

    def test_len(self) -> None:
        fs = lt.file_storage()
        with warnings.catch_warnings():
            self.assertEqual(len(fs), 0)
            fs.add_file("path/test.txt", 1024)
            self.assertEqual(len(fs), 1)

    def test_symlink(self) -> None:
        # default empty str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.symlink(0), "")

        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="other.txt")
        self.assertEqual(fs.symlink(0), "path/other.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath=b"other.txt")
        self.assertEqual(fs.symlink(0), "path/other.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="\u1234.txt")
        self.assertEqual(fs.symlink(0), "path/\u1234.txt")

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="\u1234.txt".encode())
        self.assertEqual(fs.symlink(0), "path/\u1234.txt")

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath=b"\xff.txt")
        with self.assertRaises(UnicodeDecodeError):
            fs.symlink(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_symlink_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.symlink(0)
        with self.assertRaises(IndexError):
            fs.symlink(-1)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_symlink_bytes(self) -> None:
        # default empty
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.symlink_bytes(0), b"")

        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="other.txt")
        self.assertEqual(fs.symlink_bytes(0), b"path/other.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath=b"other.txt")
        self.assertEqual(fs.symlink_bytes(0), b"path/other.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="\u1234.txt")
        self.assertEqual(fs.symlink_bytes(0), "path/\u1234.txt".encode())

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath="\u1234.txt".encode())
        self.assertEqual(fs.symlink_bytes(0), "path/\u1234.txt".encode())

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 0, linkpath=b"\xff.txt")
        self.assertEqual(fs.symlink_bytes(0), b"path/\xff.txt")

    def test_file_path_params(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_path(0), "path/test.txt")
        self.assertEqual(fs.file_path(idx=0), "path/test.txt")
        self.assertEqual(fs.file_path(0, "base"), "base/path/test.txt")
        self.assertEqual(fs.file_path(0, save_path="base"), "base/path/test.txt")

    def test_file_path(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_path(0), "path/test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.file_path(0), "path/test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt", 1024)
        self.assertEqual(fs.file_path(0), "path/\u1234.txt")

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt".encode(), 1024)
        self.assertEqual(fs.file_path(0), "path/\u1234.txt")

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"path/\xff.txt", 1024)
        with self.assertRaises(UnicodeDecodeError):
            fs.file_path(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_file_path_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.file_path(0)
        with self.assertRaises(IndexError):
            fs.file_path(-1)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_file_path_bytes(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_path_bytes(0), b"path/test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.file_path_bytes(0), b"path/test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt", 1024)
        self.assertEqual(fs.file_path_bytes(0), "path/\u1234.txt".encode())

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt".encode(), 1024)
        self.assertEqual(fs.file_path_bytes(0), "path/\u1234.txt".encode())

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"path/\xff.txt", 1024)
        self.assertEqual(fs.file_path_bytes(0), b"path/\xff.txt")

    def test_file_name(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_name(0), "test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.file_name(0), "test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt", 1024)
        self.assertEqual(fs.file_name(0), "\u1234.txt")

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt".encode(), 1024)
        self.assertEqual(fs.file_name(0), "\u1234.txt")

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"path/\xff.txt", 1024)
        with self.assertRaises(UnicodeDecodeError):
            fs.file_name(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_file_name_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.file_name(0)
        with self.assertRaises(IndexError):
            fs.file_name(-1)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_file_name_bytes(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_name_bytes(0), b"test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.file_name_bytes(0), b"test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt", 1024)
        self.assertEqual(fs.file_name_bytes(0), "\u1234.txt".encode())

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/\u1234.txt".encode(), 1024)
        self.assertEqual(fs.file_name_bytes(0), "\u1234.txt".encode())

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"path/\xff.txt", 1024)
        self.assertEqual(fs.file_name_bytes(0), b"\xff.txt")

    def test_file_size(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_size(0), 1024)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_file_size_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.file_size(0)
        with self.assertRaises(IndexError):
            fs.file_size(-1)

    def test_file_offset(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test1.txt", 1024)
        fs.add_file("path/test2.txt", 1024)
        self.assertEqual(fs.file_offset(0), 0)
        self.assertEqual(fs.file_offset(1), 1024)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_file_offset_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.file_offset(0)
        with self.assertRaises(IndexError):
            fs.file_offset(-1)

    def test_file_flags(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.file_flags(0), 0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_file_flags_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.file_flags(0)
        with self.assertRaises(IndexError):
            fs.file_flags(-1)

    def test_total_size(self) -> None:
        fs = lt.file_storage()
        self.assertEqual(fs.total_size(), 0)
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.total_size(), 1024)

    @unittest.skip("this should be deprecated")
    def test_set_num_pieces_deprecated(self) -> None:
        fs = lt.file_storage()
        with self.assertWarns(DeprecationWarning):
            fs.set_num_pieces(1024)
        with self.assertWarns(DeprecationWarning):
            fs.num_pieces()

    def test_piece_length(self) -> None:
        fs = lt.file_storage()
        fs.set_piece_length(16384)
        self.assertEqual(fs.piece_length(), 16384)

    def test_piece_size(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.set_piece_length(16384)
        fs.set_num_pieces(1)
        self.assertEqual(fs.piece_size(0), 1024)
        self.assertEqual(fs.piece_size(1), 16384)

    def test_name(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.name(), "path")
        fs.set_name("other")
        self.assertEqual(fs.file_path(0), "other/test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.name(), "path")
        fs.set_name(b"other")
        self.assertEqual(fs.file_path(0), "other/test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("\u1234/test.txt", 1024)
        self.assertEqual(fs.name(), "\u1234")
        fs.set_name("\u2345")
        self.assertEqual(fs.file_path(0), "\u2345/test.txt")

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("\u1234/test.txt".encode(), 1024)
        self.assertEqual(fs.name(), "\u1234")
        fs.set_name("\u2345".encode())
        self.assertEqual(fs.file_path(0), "\u2345/test.txt")

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"\xff/test.txt", 1024)
        with self.assertRaises(UnicodeDecodeError):
            fs.name()
        fs.set_name(b"\xfe")
        with self.assertRaises(UnicodeDecodeError):
            fs.file_path(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_name_bytes(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        self.assertEqual(fs.name_bytes(), b"path")
        fs.set_name("other")
        self.assertEqual(fs.file_path_bytes(0), b"other/test.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file(b"path/test.txt", 1024)
        self.assertEqual(fs.name_bytes(), b"path")
        fs.set_name(b"other")
        self.assertEqual(fs.file_path_bytes(0), b"other/test.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("\u1234/test.txt", 1024)
        self.assertEqual(fs.name_bytes(), "\u1234".encode())
        fs.set_name("\u2345")
        self.assertEqual(fs.file_path_bytes(0), "\u2345/test.txt".encode())

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("\u1234/test.txt".encode(), 1024)
        self.assertEqual(fs.name_bytes(), "\u1234".encode())
        fs.set_name("\u2345".encode())
        self.assertEqual(fs.file_path_bytes(0), "\u2345/test.txt".encode())

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file(b"\xff/test.txt", 1024)
        self.assertEqual(fs.name_bytes(), b"\xff")
        fs.set_name(b"\xfe")
        self.assertEqual(fs.file_path_bytes(0), b"\xfe/test.txt")

    def test_rename_file(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/other.txt")
        self.assertEqual(fs.file_path(0), "path/other.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, b"path/other.txt")
        self.assertEqual(fs.file_path(0), "path/other.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/\u1234.txt")
        self.assertEqual(fs.file_path(0), "path/\u1234.txt")

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/\u1234.txt".encode())
        self.assertEqual(fs.file_path(0), "path/\u1234.txt")

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, b"path\xff.txt")
        with self.assertRaises(UnicodeDecodeError):
            fs.file_path(0)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_rename_file_invalid(self) -> None:
        fs = lt.file_storage()
        with self.assertRaises(IndexError):
            fs.rename_file(0, "path/test.txt")
        with self.assertRaises(IndexError):
            fs.rename_file(-1, "path/test.txt")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_rename_file_bytes(self) -> None:
        # ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/other.txt")
        self.assertEqual(fs.file_path_bytes(0), b"path/other.txt")

        # ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, b"path/other.txt")
        self.assertEqual(fs.file_path_bytes(0), b"path/other.txt")

        # non-ascii str
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/\u1234.txt")
        self.assertEqual(fs.file_path_bytes(0), "path/\u1234.txt".encode())

        # non-ascii bytes
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, "path/\u1234.txt".encode())
        self.assertEqual(fs.file_path_bytes(0), "path/\u1234.txt".encode())

        # invalid encoding
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        fs.rename_file(0, b"path\xff.txt")
        self.assertEqual(fs.file_path_bytes(0), b"path/\xff.txt")


class CreateTorrentTest(unittest.TestCase):
    maxDiff = None

    @unittest.skip("generate() outputs a tuple of ints for some reason")
    def test_init_torrent_info(self) -> None:
        entry = {
            b"info": {
                b"name": b"test.txt",
                b"piece length": 16384,
                b"pieces": lib.get_random_bytes(20),
                b"length": 1024,
            }
        }
        ti = lt.torrent_info(entry)
        ct = lt.create_torrent(ti)
        self.assertEqual(ct.generate(), entry)

    def test_args_file_storage(self) -> None:
        fs = lt.file_storage()

        lt.create_torrent(fs)
        lt.create_torrent(fs, 0)
        lt.create_torrent(fs, 0, 0)
        lt.create_torrent(fs, 0, lt.create_torrent_flags_t.v2_only)
        lt.create_torrent(storage=fs)
        lt.create_torrent(storage=fs, piece_size=0)
        lt.create_torrent(storage=fs, piece_size=0, flags=0)
        lt.create_torrent(
            storage=fs, piece_size=0, flags=lt.create_torrent_flags_t.v2_only
        )

    def test_generate(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertIsInstance(entry, dict)
        lt.torrent_info(entry)

    def test_files(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test1.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.files().add_file("path/test2.txt", 1024)
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(len(entry[b"info"][b"files"]), 2)

    def test_comment(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_comment("test")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"comment"], b"test")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_comment_bytes(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_comment(b"test")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"comment"], b"test")

    def test_creator(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_creator("test")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"created by"], b"test")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_creator_bytes(self) -> None:
        fs = lt.file_storage()
        fs.add_file("path/test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_creator(b"test")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"created by"], b"test")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_set_hash_invalid(self) -> None:
        fs = lt.file_storage()
        ct = lt.create_torrent(fs)
        with self.assertRaises(IndexError):
            ct.set_hash(0, lib.get_random_bytes(20))
        with self.assertRaises(IndexError):
            ct.set_hash(-1, lib.get_random_bytes(20))

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5993")
    def test_set_hash_short(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        with self.assertRaises(ValueError):
            ct.set_hash(0, lib.get_random_bytes(19))

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_set_file_hash_deprecated(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        with self.assertWarns(DeprecationWarning):
            ct.set_file_hash(0, lib.get_random_bytes(20))

    def test_set_file_hash(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        with warnings.catch_warnings():
            ct.set_file_hash(0, lib.get_random_bytes(20))
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertIn(b"sha1", entry[b"info"])

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5989")
    def test_set_file_hash_invalid(self) -> None:
        fs = lt.file_storage()
        ct = lt.create_torrent(fs)
        with self.assertRaises(IndexError):
            ct.set_file_hash(0, lib.get_random_bytes(20))
        with self.assertRaises(IndexError):
            ct.set_file_hash(-1, lib.get_random_bytes(20))

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5993")
    def test_set_file_hash_short(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        with self.assertRaises(ValueError):
            ct.set_file_hash(0, lib.get_random_bytes(19))

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_url_seed(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.add_url_seed("http://example.com")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"url-list"], [b"http://example.com"])

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_http_seed(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        with warnings.catch_warnings():
            ct.add_http_seed("http://example.com")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"url-list"], [b"http://example.com"])

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5967")
    def test_http_seed_deprecated(self) -> None:
        fs = lt.file_storage()
        ct = lt.create_torrent(fs)
        with self.assertWarns(DeprecationWarning):
            ct.add_http_seed("http://example.com")

    def test_add_node(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.add_node("1.2.3.4", 5678)
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"nodes"], [[b"1.2.3.4", 5678]])

    def test_add_tracker(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.add_tracker("http://example.com")
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(entry[b"announce"], b"http://example.com")

    def test_add_tracker_args(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.add_tracker("http://1.com")
        ct.add_tracker("http://2.com", 200)
        ct.add_tracker(announce_url="http://3.com")
        ct.add_tracker(announce_url="http://4.com", tier=100)
        ct.set_hash(0, lib.get_random_bytes(20))
        entry = ct.generate()
        self.assertEqual(
            entry[b"announce-list"],
            [[b"http://1.com", b"http://3.com"], [b"http://4.com"], [b"http://2.com"]],
        )

    def test_priv(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_priv(True)
        self.assertTrue(ct.priv())

    def test_num_pieces(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        self.assertEqual(ct.num_pieces(), 1)

    def test_piece_length(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        self.assertEqual(ct.piece_length(), 16384)

    def test_piece_size(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        self.assertEqual(ct.piece_size(-1), 16384)
        self.assertEqual(ct.piece_size(0), 1024)
        self.assertEqual(ct.piece_size(1), 16384)

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_root_cert_str(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        ct.set_root_cert("test")
        entry = ct.generate()
        self.assertEqual(entry[b"info"][b"ssl-cert"], b"test")

    def test_root_cert(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        ct.set_root_cert(b"test")
        entry = ct.generate()
        self.assertEqual(entry[b"info"][b"ssl-cert"], b"test")

    def test_collections(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        # ct.add_collection("ascii-str")
        ct.add_collection(b"ascii-bytes")
        # ct.add_collection("non-ascii-str-\u1234")
        ct.add_collection("non-ascii-bytes-\u1234".encode())
        ct.add_collection(b"bad-\xff")
        entry = ct.generate()
        self.assertEqual(
            entry[b"info"][b"collections"],
            [
                # b"ascii-str",
                b"ascii-bytes",
                # "non-ascii-str-\u1234".encode(),
                "non-ascii-bytes-\u1234".encode(),
                b"bad-\xff",
            ],
        )

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5995")
    def test_collections_broken(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        ct.add_collection("ascii-str")
        ct.add_collection(b"ascii-bytes")
        ct.add_collection("non-ascii-str-\u1234")
        ct.add_collection("non-ascii-bytes-\u1234".encode())
        ct.add_collection(b"bad-\xff")
        entry = ct.generate()
        self.assertEqual(
            entry[b"info"][b"collections"],
            [
                b"ascii-str",
                b"ascii-bytes",
                "non-ascii-str-\u1234".encode(),
                "non-ascii-bytes-\u1234".encode(),
                b"bad-\xff",
            ],
        )

    def test_similar(self) -> None:
        fs = lt.file_storage()
        fs.add_file("test.txt", 1024)
        ct = lt.create_torrent(fs)
        ct.set_hash(0, lib.get_random_bytes(20))
        sha1 = lt.sha1_hash(lib.get_random_bytes(20))
        ct.add_similar_torrent(sha1)
        entry = ct.generate()
        self.assertEqual(entry[b"info"][b"similar"], [sha1.to_bytes()])


class AddFilesTest(unittest.TestCase):
    @contextlib.contextmanager
    def setup_args_check(
        self,
    ) -> Iterator[Tuple[lt.file_storage, str, Callable[[str], bool]]]:
        fs = lt.file_storage()
        pred = unittest.mock.Mock(return_value=True)
        with tempfile.TemporaryDirectory() as tempdir_str:
            tempdir = pathlib.Path(tempdir_str)
            file_paths = [tempdir / name for name in ("a.txt", "b.txt")]
            for file_path in file_paths:
                file_path.write_bytes(lib.get_random_bytes(1024))
            yield (fs, tempdir_str, pred)
            calls = [unittest.mock.call(str(path)) for path in file_paths]
            pred.assert_has_calls(calls, any_order=True)
            self.assertEqual(fs.num_files(), 2)

    def test_args(self) -> None:
        fs = lt.file_storage()
        with tempfile.TemporaryDirectory() as path:
            lt.add_files(fs, path)
            lt.add_files(fs=fs, path=path)
            lt.add_files(fs=fs, path=path, flags=0)
            lt.add_files(fs=fs, path=path, flags=lt.create_torrent_flags_t.v2_only)

        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(fs, path, pred)
        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(fs, path, pred, 0)
        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(fs, path, pred, lt.create_torrent_flags_t.v2_only)
        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(fs=fs, path=path, predicate=pred)
        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(fs=fs, path=path, predicate=pred, flags=0)
        with self.setup_args_check() as (fs, path, pred):
            lt.add_files(
                fs=fs,
                path=path,
                predicate=pred,
                flags=lt.create_torrent_flags_t.v2_only,
            )

    def do_test_path_encoding(
        self, name: AnyStr, check_str: str = None, check_bytes: bytes = None
    ) -> None:
        with tempfile.TemporaryDirectory() as tempdir_str:
            # /tmp/abcd
            tempdir: AnyStr
            if isinstance(name, str):
                tempdir = tempdir_str
            else:
                tempdir = os.fsencode(tempdir_str)
            # /tmp/abcd/<name>
            inner = os.path.join(tempdir, name)
            os.mkdir(inner)
            # /tmp/abcd/<name>/<name>
            with open(os.path.join(inner, name), mode="wb") as fp:
                fp.write(lib.get_random_bytes(1024))
            fs = lt.file_storage()
            lt.add_files(fs, inner)
            if check_str is not None:
                self.assertEqual(fs.file_name(0), check_str)
            if check_bytes is not None:
                self.assertEqual(fs.file_name_bytes(0), check_bytes)

    def test_path_types(self) -> None:
        # ascii str
        self.do_test_path_encoding("test.txt", "test.txt")

        # ascii bytes
        self.do_test_path_encoding(b"test.txt", "test.txt")

        # non-ascii str
        self.do_test_path_encoding("\u1234.txt", "\u1234.txt")

        # non-ascii bytes
        self.do_test_path_encoding(os.fsencode("\u1234.txt"), "\u1234.txt")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    def test_add_files_bytes_path(self) -> None:
        # ascii str
        self.do_test_path_encoding("test.txt", "test.txt", b"test.txt")

        # ascii bytes
        self.do_test_path_encoding(b"test.txt", "test.txt", b"test.txt")

        # non-ascii str
        self.do_test_path_encoding(
            "\u1234.txt", "\u1234.txt", os.fsencode("\u1234.txt")
        )

        # non-ascii bytes
        self.do_test_path_encoding(
            os.fsencode("\u1234.txt"), "\u1234.txt", os.fsencode("\u1234.txt")
        )

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5985")
    @lib.uses_non_unicode_paths()
    def test_invalid_encoding_bytes(self) -> None:
        # invalid encoding str
        self.do_test_path_encoding(os.fsdecode(b"\xff.txt"), None, b"\xff.txt")

        # invalid encoding bytes
        self.do_test_path_encoding(b"\xff.txt", None, b"\xff.txt")


class SetPieceHashesTest(unittest.TestCase):
    def test_args(self) -> None:
        fs = lt.file_storage()
        pred = unittest.mock.Mock()
        with tempfile.TemporaryDirectory() as tempdir_str:
            tempdir = pathlib.Path(tempdir_str)
            inner = tempdir / "inner"
            inner.mkdir()
            file_path = inner / "a.txt"
            file_path.write_bytes(lib.get_random_bytes(1024))
            lt.add_files(fs, str(inner))
            ct = lt.create_torrent(fs)

            # path str
            lt.set_piece_hashes(ct, tempdir_str)

            # path str and predicate
            lt.set_piece_hashes(ct, tempdir_str, pred)
            calls = [unittest.mock.call(0)]
            pred.assert_has_calls(calls)

    def do_test_path_encoding(
        self, name: AnyStr, add_name: Union[str, bytes] = None
    ) -> None:
        with tempfile.TemporaryDirectory() as tempdir_str:
            tempdir: AnyStr
            if isinstance(name, str):
                tempdir = tempdir_str
            else:
                tempdir = os.fsencode(tempdir_str)
            # /tmp/abcd/<name>/
            inner = os.path.join(tempdir, name)
            os.mkdir(inner)
            # /tmp/abcd/<name>/<name>
            with open(os.path.join(inner, name), mode="wb") as fp:
                fp.write(lib.get_random_bytes(1024))
            fs = lt.file_storage()
            if add_name is None:
                add_name = name
            fs.add_file(add_name, 1024)
            ct = lt.create_torrent(fs)
            lt.set_piece_hashes(ct, inner)

    def test_path_types(self) -> None:
        # ascii str
        self.do_test_path_encoding("test.txt")

        # ascii bytes
        self.do_test_path_encoding(b"test.txt")

        # non-ascii str
        self.do_test_path_encoding("\u1234.txt")

        # non-ascii bytes
        self.do_test_path_encoding(os.fsencode("\u1234.txt"))

    @lib.uses_non_unicode_paths()
    def test_path_invalid_encoding(self) -> None:
        # non-unicode bytes
        self.do_test_path_encoding(b"\xff.txt")

    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5984")
    @lib.uses_non_unicode_paths()
    def test_path_invalid_encoding_fsdecode(self) -> None:
        # non-unicode bytes
        self.do_test_path_encoding(os.fsdecode(b"\xff.txt"), b"\xff.txt")
