import json
import os
import pathlib
import random
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import TypeVar
import unittest

import importlib_resources


def get_random_bytes(n: int) -> bytes:
    return bytes(random.getrandbits(8) for _ in range(n))


def get_isolated_settings() -> Dict[str, Any]:
    return {
        "enable_dht": False,
        "enable_lsd": False,
        "enable_natpmp": False,
        "enable_upnp": False,
        "listen_interfaces": "127.0.0.1:0",
    }


def loop_until_timeout(timeout: float, msg: str = "condition") -> Iterator[None]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        yield
    raise AssertionError(f"{msg} timed out")


class GoldenTestCase(unittest.TestCase):

    maxDiff = None

    def get_meld_path(self, suffix: str) -> pathlib.Path:
        # importlib_resources doesn't provide any way for updating files
        # that are assumed to be individually accessible on the filesystem. So
        # for updating golden data, we use the "naive" approach of referencing
        # a file based off of the __file__ path.
        return pathlib.Path(__file__) / "data" / f"{self.id()}.{suffix}"

    def get_golden_data(self, suffix: str) -> str:
        return importlib_resources.read_text("tests.data", f"{self.id()}.{suffix}")

    def assert_golden(self, value: str, suffix: str = "golden.txt") -> None:
        if os.environ.get("GOLDEN_MELD"):
            with self.get_meld_path(suffix).open(mode="w") as golden_fp:
                golden_fp.write(value)
        else:
            second = self.get_golden_data(suffix)
            self.assertEqual(value, second)

    def assert_golden_json(
        self, value: Any, suffix: str = "golden.json", **kwargs: Any
    ) -> None:
        kwargs["indent"] = 4
        kwargs["sort_keys"] = True
        value_text = json.dumps(value, **kwargs)
        self.assert_golden(value_text, suffix=suffix)


_FT = TypeVar("_FT", bound=Callable[..., Any])


def uses_non_unicode_paths() -> Callable[[_FT], _FT]:
    supported = True
    try:
        os.fsdecode(b"\xff")
    except ValueError:
        supported = False
    return unittest.skipIf(
        not supported, "platform doesn't support non-unicode filenames"
    )
