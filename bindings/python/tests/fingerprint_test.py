import unittest

import libtorrent as lt


class GenerateFingerprintTest(unittest.TestCase):
    @unittest.skip("https://github.com/arvidn/libtorrent/issues/5988")
    def test_deprecations(self) -> None:
        with self.assertWarns(DeprecationWarning):
            lt.generate_fingerprint("ABCD", 1, 2, 3, 4)

    def test_generate_str(self) -> None:
        # full version
        self.assertEqual(lt.generate_fingerprint("ABCD", 1, 2, 3, 4), "-AB1234-")

        # short name
        self.assertEqual(lt.generate_fingerprint("A", 1, 2, 3, 4), "---1234-")

        # version < 0
        self.assertEqual(lt.generate_fingerprint("ABCD", 1, 2, -1, -1), "-AB1200-")


class FingerprintTest(unittest.TestCase):
    @unittest.skip("backport needed")
    def test_fingerprint(self) -> None:
        with self.assertWarns(DeprecationWarning):
            fprint = lt.fingerprint("AB", 1, 2, 3, 4)
        self.assertEqual(str(fprint), "-AB1234-")
        self.assertEqual(fprint.major_version, 1)
        self.assertEqual(fprint.minor_version, 2)
        self.assertEqual(fprint.revision_version, 3)
        self.assertEqual(fprint.tag_version, 4)

        # short names behave differently
        with self.assertWarns(DeprecationWarning):
            fprint = lt.fingerprint("A", 1, 2, 3, 4)
        self.assertEqual(str(fprint), "-A\x001234-")
