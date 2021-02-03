import unittest
import warnings

import libtorrent as lt


class IpFilterTest(unittest.TestCase):
    def test_access(self) -> None:
        ipf = lt.ip_filter()
        self.assertEqual(ipf.access("0.1.2.3"), 0)
        ipf.add_rule("0.0.0.0", "0.255.255.255", 123)
        self.assertEqual(ipf.access("0.1.2.3"), 123)
        self.assertEqual(ipf.access("1.2.3.4"), 0)
        # self.assertEqual(ipf.export_filter(), ...)

    @unittest.skip("binding doesn't work")
    def test_broken(self) -> None:
        # self.assertEqual(ipf.export_filter(), ...)
