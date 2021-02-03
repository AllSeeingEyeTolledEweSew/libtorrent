import os
import subprocess as sub
import sys
import time
import unittest

import importlib_resources


class ClientTest(unittest.TestCase):

    maxDiff = None

    @unittest.skipIf(os.name == "nt", "need to make stdin work on windows")
    def test_client(self) -> None:
        import pty

        _, stdin = pty.openpty()

        with importlib_resources.path("tests.data", "url_seed_multi.torrent") as path:
            process = sub.Popen(
                [sys.executable, "client.py", os.fspath(path)],
                stdin=stdin,
                stdout=sub.PIPE,
                stderr=sub.PIPE,
            )
            time.sleep(5)
            early_returncode = process.poll()
            process.kill()
            _, stderr = process.communicate()

            self.assertEqual(stderr, b"")
            self.assertEqual(early_returncode, None)
