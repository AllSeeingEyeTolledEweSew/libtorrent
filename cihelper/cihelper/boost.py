import contextlib
import logging
import os
import os.path
import pathlib
import sys
import tarfile
from typing import Iterable
from typing import Mapping
import urllib.request

from . import common

_LOG = logging.getLogger(__name__)


def get_version() -> str:
    return os.environ.get("CIHELPER_BOOST_VERSION", "1.75.0")


def get_root() -> pathlib.Path:
    # bootstrap.sh doesn't support being run from a dir with spaces
    assert " " not in str(common.get_base()), common.get_base()
    vunder = get_version().replace(".", "_")
    return common.get_base() / f"boost_{vunder}"


def get_archive_url(suffix: str) -> str:
    version = get_version()
    vunder = version.replace(".", "_")
    return (
        "https://boostorg.jfrog.io/artifactory/main/release/"
        f"{version}/source/boost_{vunder}{suffix}"
    )


def download_and_extract() -> None:
    # This is pure-python but slow
    url = get_archive_url(".tar.bz2")
    _LOG.debug("requesting: %s", url)
    resp = urllib.request.urlopen(url)
    tar = tarfile.open(mode="r|bz2", fileobj=resp)
    with contextlib.closing(tar):
        # will populate /<base>/boost_x_y_z
        _LOG.debug("extracting to: %s", common.get_base())
        common.get_base().mkdir(parents=True, exist_ok=True)
        tar.extractall(path=str(common.get_base()))


def bootstrap() -> None:
    if sys.platform == "win32":
        exe = get_root() / "bootstrap.bat"
    else:
        exe = get_root() / "bootstrap.sh"
    common.check_call([exe], cwd=get_root())
    config = get_root() / "project-config.jam"
    _LOG.info("contents of %s:\n%s", config, config.read_text())
    common.check_call(
        [get_root() / "b2", f"-j{common.get_jobs()}", "headers"], cwd=get_root()
    )


def install() -> None:
    _LOG.info("PATH = %r", os.environ["PATH"])
    if get_root().is_dir():
        return
    download_and_extract()
    bootstrap()


def get_required_path() -> Iterable[pathlib.Path]:
    return [get_root()]


def get_required_env() -> Mapping[str, str]:
    return {
        "BOOST_ROOT": str(get_root()),
        "BOOST_BUILD_PATH": str(get_root() / "tools" / "build"),
    }


def configure_env() -> None:
    # like: echo "BOOST_ROOT=$..." >> $GITHUB_ENV
    if os.environ.get("GITHUB_ENV"):
        github_env_path = pathlib.Path(os.environ["GITHUB_ENV"])
        _LOG.info("adding to $GITHUB_ENV:")
        with github_env_path.open(mode="a") as fp:
            for key, value in get_required_env().items():
                _LOG.info("... %s=%s", key, value)
                fp.write(f"{key}={value}\n")

    # like: echo "$..." >> $GITHUB_PATH
    if os.environ.get("GITHUB_PATH"):
        github_path_path = pathlib.Path(os.environ["GITHUB_PATH"])
        _LOG.info("adding to $GITHUB_PATH:")
        with github_path_path.open(mode="a") as fp:
            for path in get_required_path():
                _LOG.info("... %s", path)
                fp.write(f"{path}\n")


def install_cmd() -> None:
    common.configure_logger()
    install()
    configure_env()
