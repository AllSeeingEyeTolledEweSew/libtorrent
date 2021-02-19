#!/usr/bin/env python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from __future__ import print_function

import glob
import os
import sys
from typing import Dict
from typing import IO
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
import urllib.parse

verbose = "--verbose" in sys.argv
dump = "--dump" in sys.argv
internal = "--internal" in sys.argv
plain_output = "--plain-output" in sys.argv
single_page_output = "--single-page" in sys.argv
if plain_output:
    plain_file = open("plain_text_out.txt", "w+")
in_code: Optional[str] = None

paths = [
    "include/libtorrent/*.hpp",
    "include/libtorrent/kademlia/*.hpp",
    "include/libtorrent/extensions/*.hpp",
]

if internal:
    paths.append("include/libtorrent/aux_/*.hpp")

files = []

for p in paths:
    files.extend(glob.glob(os.path.join("..", p)))


class Declared:
    def __init__(self, *, file: str):
        self.file = file


class Function(Declared):
    def __init__(
        self,
        *,
        file: str,
        signatures: Iterable[str] = (),
        names: Iterable[str] = (),
        desc: str = "",
    ):
        super().__init__(file=file)
        self.signatures = set(signatures)
        self.names = set(names)
        self.desc = desc


class EnumValue:
    def __init__(self, *, name: str, desc: str, val: str):
        self.name = name
        self.desc = desc
        self.val = val


class Enum(Declared):
    def __init__(
        self,
        *,
        file: str,
        name: str,
        values: Iterable[EnumValue] = (),
        desc: str = "",
    ):
        super().__init__(file=file)
        self.name = name
        self.values = list(values)
        self.desc = desc


class Field:
    def __init__(
        self,
        *,
        desc: str,
        names: Iterable[str] = (),
        signatures: Iterable[str] = (),
    ) -> None:
        self.names = list(names)
        self.signatures = list(signatures)
        self.desc = desc


class Class(Declared):
    def __init__(
        self,
        *,
        file: str,
        type: str,
        name: str,
        decl: str,
        enums: Iterable[Enum] = (),
        fields: Iterable[Field] = (),
        funs: Iterable[Function] = (),
        desc: str = "",
    ):
        super().__init__(file=file)
        self.type = type
        self.name = name
        self.decl = decl
        self.enums = list(enums)
        self.fields = list(fields)
        self.funs = list(funs)
        self.desc = desc


class Constant(Declared):
    def __init__(self, *, file: str, type: str, name: str, desc: str = ""):
        super().__init__(file=file)
        self.type = type
        self.name = name
        self.desc = desc


functions: List[Function] = []
classes: List[Class] = []
enums: List[Enum] = []
constants: Dict[str, List[Constant]] = {}

# maps filename to overview description
overviews: Dict[str, str] = {}

# maps names -> URL
symbols = {}

global orphaned_export

# some files that need pre-processing to turn symbols into
# links into the reference documentation
preprocess_rst = {
    "manual.rst": "manual-ref.rst",
    "tuning.rst": "tuning-ref.rst",
    "tutorial.rst": "tutorial-ref.rst",
    "features.rst": "features-ref.rst",
    "upgrade_to_1.2.rst": "upgrade_to_1.2-ref.rst",
    "upgrade_to_2.0.rst": "upgrade_to_2.0-ref.rst",
    "settings.rst": "settings-ref.rst",
}

# some pre-defined sections from the main manual
symbols = {
    "queuing_": "manual-ref.html#queuing",
    "fast-resume_": "manual-ref.html#fast-resume",
    "storage-allocation_": "manual-ref.html#storage-allocation",
    "alerts_": "manual-ref.html#alerts",
    "upnp-and-nat-pmp_": "manual-ref.html#upnp-and-nat-pmp",
    "http-seeding_": "manual-ref.html#http-seeding",
    "metadata-from-peers_": "manual-ref.html#metadata-from-peers",
    "magnet-links_": "manual-ref.html#magnet-links",
    "ssl-torrents_": "manual-ref.html#ssl-torrents",
    "dynamic-loading-of-torrent-files_": "manual-ref.html"
    "#dynamic-loading-of-torrent-files",
    "session-statistics_": "manual-ref.html#session-statistics",
    "peer-classes_": "manual-ref.html#peer-classes",
}

# parse out names of settings, and add them to the symbols list, to get cross
# references working
with open("../src/settings_pack.cpp") as fp:
    for line in fp:
        line = line.strip()
        if not line.startswith("SET("):
            continue

        name = line.split("(")[1].split(",")[0]
        symbols["settings_pack::" + name] = "reference-Settings.html#" + name

static_links = {
    ".. _`BEP 3`: https://www.bittorrent.org/beps/bep_0003.html",
    ".. _`BEP 17`: https://www.bittorrent.org/beps/bep_0017.html",
    ".. _`BEP 19`: https://www.bittorrent.org/beps/bep_0019.html",
    ".. _`BEP 38`: https://www.bittorrent.org/beps/bep_0038.html",
    ".. _`BEP 42`: https://www.bittorrent.org/beps/bep_0042.html",
    ".. _`rate based choking`: manual-ref.html#rate-based-choking",
    ".. _extensions: manual-ref.html#extensions",
}

anon_index = 0

category_mapping = {
    "ed25519.hpp": "ed25519",
    "session.hpp": "Session",
    "session_handle.hpp": "Session",
    "torrent_handle.hpp": "Torrent Handle",
    "torrent_info.hpp": "Torrent Info",
    "announce_entry.hpp": "Trackers",
    "peer_class_type_filter.hpp": "PeerClass",
    "peer_class.hpp": "PeerClass",
    "torrent_status.hpp": "Torrent Status",
    "session_stats.hpp": "Stats",
    "performance_counters.hpp": "Stats",
    "read_resume_data.hpp": "Resume Data",
    "write_resume_data.hpp": "Resume Data",
    "add_torrent_params.hpp": "Add Torrent",
    "client_data.hpp": "Add Torrent",
    "session_status.hpp": "Session",
    "session_params.hpp": "Session",
    "error_code.hpp": "Error Codes",
    "storage_defs.hpp": "Storage",
    "file_storage.hpp": "Storage",
    "disk_interface.hpp": "Custom Storage",
    "disk_observer.hpp": "Custom Storage",
    "mmap_disk_io.hpp": "Storage",
    "disabled_disk_io.hpp": "Storage",
    "posix_disk_io.hpp": "Storage",
    "extensions.hpp": "Plugins",
    "ut_metadata.hpp": "Plugins",
    "ut_pex.hpp": "Plugins",
    "ut_trackers.hpp": "Plugins",
    "smart_ban.hpp": "Plugins",
    "peer_connection_handle.hpp": "Plugins",
    "create_torrent.hpp": "Create Torrents",
    "alert.hpp": "Alerts",
    "alert_types.hpp": "Alerts",
    "bencode.hpp": "Bencoding",
    "bdecode.hpp": "Bdecoding",
    "entry.hpp": "Bencoding",
    "time.hpp": "Time",
    "escape_string.hpp": "Utility",
    "enum_net.hpp": "Network",
    "socket.hpp": "Network",
    "address.hpp": "Network",
    "socket_io.hpp": "Network",
    "bitfield.hpp": "Utility",
    "sha1_hash.hpp": "Utility",
    "hasher.hpp": "Utility",
    "identify_client.hpp": "Utility",
    "ip_filter.hpp": "Filter",
    "session_settings.hpp": "Settings",
    "settings_pack.hpp": "Settings",
    "fingerprint.hpp": "Settings",
    "operations.hpp": "Alerts",
    "disk_buffer_holder.hpp": "Custom Storage",
    "alert_dispatcher.hpp": "Alerts",
}

category_fun_mapping = {
    "min_memory_usage()": "Settings",
    "high_performance_seed()": "Settings",
    "default_disk_io_constructor()": "Storage",
    "settings_interface": "Custom Storage",
}


def categorize_symbol(name: str, filename: str) -> str:
    part = os.path.split(filename)[1]

    if (
        name.endswith("_category()")
        or name.endswith("_error_code")
        or name.endswith("error_code_enum")
        or name.endswith("errors")
    ):
        return "Error Codes"

    if name in category_fun_mapping:
        return category_fun_mapping[name]

    if part in category_mapping:
        return category_mapping[part]

    if filename.startswith("libtorrent/kademlia/"):
        return "DHT"

    return "Core"


def suppress_warning(filename: str) -> bool:
    part = os.path.split(filename)[1]
    if part != "alert_types.hpp":
        return False

    # if name.endswith('_alert') or name == 'message()':
    return True

    # return False


def is_visible(desc: str) -> bool:
    if desc.strip().startswith("hidden"):
        return False
    if internal:
        return True
    if desc.strip().startswith("internal"):
        return False
    return True


def highlight_signature(s: str) -> str:
    name = s.split("(", 1)
    name2 = name[0].split(" ")
    if len(name2[-1]) == 0:
        return s

    # make the name of the function bold
    name2[-1] = "**" + name2[-1] + "** "

    # if there is a return value, make sure we preserve pointer types
    if len(name2) > 1:
        name2[0] = name2[0].replace("*", "\\*")
    name[0] = " ".join(name2)

    # we have to escape asterisks, since this is rendered into
    # a parsed literal in rst
    name[1] = name[1].replace("*", "\\*")

    # we also have to escape colons
    name[1] = name[1].replace(":", "\\:")

    # escape trailing underscores
    name[1] = name[1].replace("_", "\\_")

    # comments in signatures are italic
    name[1] = name[1].replace("/\\*", "*/\\*")
    name[1] = name[1].replace("\\*/", "\\*/*")
    return "(".join(name)


def highlight_name(s: str) -> str:
    if "=" in s:
        splitter = " = "
    elif "{" in s:
        splitter = "{"
    else:
        return s

    name = s.split(splitter, 1)
    name2 = name[0].split(" ")
    if len(name2[-1]) == 0:
        return s

    name2[-1] = "**" + name2[-1] + "** "
    name[0] = " ".join(name2)
    return splitter.join(name)


def html_sanitize(s: str) -> str:
    ret = ""
    for i in s:
        if i == "<":
            ret += "&lt;"
        elif i == ">":
            ret += "&gt;"
        elif i == "&":
            ret += "&amp;"
        else:
            ret += i
    return ret


def looks_like_namespace(line: str) -> bool:
    line = line.strip()
    if line.startswith("namespace"):
        return True
    return False


def looks_like_blank(line: str) -> bool:
    line = line.split("//")[0]
    line = line.replace("{", "")
    line = line.replace("}", "")
    line = line.replace("[", "")
    line = line.replace("]", "")
    line = line.replace(";", "")
    line = line.strip()
    return len(line) == 0


def looks_like_variable(line: str) -> bool:
    line = line.split("//")[0]
    line = line.strip()
    if " " not in line and "\t" not in line:
        return False
    if line.startswith("friend "):
        return False
    if line.startswith("enum "):
        return False
    if line.startswith(","):
        return False
    if line.startswith(":"):
        return False
    if line.startswith("typedef"):
        return False
    if line.startswith("using"):
        return False
    if " = " in line:
        return True
    if line.endswith(";"):
        return True
    return False


def looks_like_constant(line: str) -> bool:
    line = line.strip()
    if line.startswith("inline"):
        line = line.split("inline")[1]
    line = line.strip()
    if not line.startswith("constexpr"):
        return False
    line = line.split("constexpr")[1]
    return looks_like_variable(line)


def looks_like_forward_decl(line: str) -> bool:
    line = line.split("//")[0]
    line = line.strip()
    if not line.endswith(";"):
        return False
    if "{" in line:
        return False
    if "}" in line:
        return False
    if line.startswith("friend "):
        return True
    if line.startswith("struct "):
        return True
    if line.startswith("class "):
        return True
    return False


def looks_like_function(line: str) -> bool:
    line = line.split("//")[0]
    if line.startswith("friend class "):
        return False
    if line.startswith("friend struct "):
        return False
    if "::" in line.split("(")[0].split(" ")[-1]:
        return False
    if line.startswith(","):
        return False
    if line.startswith(":"):
        return False
    return "(" in line


def parse_function(
    lno: int, lines: List[str], filename: str
) -> Tuple[Optional[Function], int]:

    start_paren = 0
    end_paren = 0
    signature = ""

    global orphaned_export
    orphaned_export = False

    while lno < len(lines):
        line = lines[lno].strip()
        lno += 1
        if line.startswith("//"):
            continue

        start_paren += line.count("(")
        end_paren += line.count(")")

        sig_line = (
            line.replace("TORRENT_EXPORT ", "")
            .replace("TORRENT_EXTRA_EXPORT", "")
            .replace("TORRENT_V3_EXPLICIT", "")
            .replace("TORRENT_COUNTER_NOEXCEPT", "")
            .split("//")[0]
            .strip()
        )
        if signature != "":
            sig_line = "\n   " + sig_line
        signature += sig_line
        if verbose:
            print("fun     %s" % line)

        if start_paren > 0 and start_paren == end_paren:
            if signature[-1] != ";":
                # we also need to consume the function body
                start_paren = 0
                end_paren = 0
                for i in range(len(signature)):
                    if signature[i] == "(":
                        start_paren += 1
                    elif signature[i] == ")":
                        end_paren += 1

                    if start_paren > 0 and start_paren == end_paren:
                        for k in range(i, len(signature)):
                            if signature[k] == ":" or signature[k] == "{":
                                signature = signature[0:k].strip()
                                break
                        break

                lno = consume_block(lno - 1, lines)
                signature += ";"
            func = Function(
                file=filename[11:],
                signatures=[signature],
                names=[signature.split("(")[0].split(" ")[-1].strip() + "()"],
            )
            if sorted(func.names)[:1] == ["()"]:
                return (None, lno)
            return (func, lno)
    if len(signature) > 0:
        print(
            "\x1b[31mFAILED TO PARSE FUNCTION\x1b[0m %s\nline: %d\nfile: %s"
            % (signature, lno, filename)
        )
    return (None, lno)


def add_desc(line: str) -> None:
    # plain output prints just descriptions and filters out c++ code.
    # it's used to run spell checker over
    if plain_output:
        for s in line.split("\n"):
            # if the first character is a space, strip it
            if len(s) > 0 and s[0] == " ":
                s = s[1:]
            global in_code
            if in_code is not None and not s.startswith(in_code) and len(s) > 1:
                in_code = None

            if s.strip().startswith(".. code::"):
                in_code = s.split(".. code::")[0] + "\t"

            # strip out C++ code from the plain text output since it's meant for
            # running spell checking over
            if not s.strip().startswith(".. ") and in_code is None:
                plain_file.write(s + "\n")


def parse_class(
    lno: int, lines: List[str], filename: str
) -> Tuple[Optional[Class], int]:
    start_brace = 0
    end_brace = 0

    name = ""
    funs: List[Function] = []
    fields: List[Field] = []
    enums: List[Enum] = []
    state = "public"
    context = ""
    class_type = "struct"
    blanks = 0
    decl = ""

    while lno < len(lines):
        line = lines[lno].strip()
        decl += (
            lines[lno]
            .replace("TORRENT_EXPORT ", "")
            .replace("TORRENT_EXTRA_EXPORT", "")
            .replace("TORRENT_V3_EXPLICIT", "")
            .replace("TORRENT_COUNTER_NOEXCEPT", "")
            .split("{")[0]
            .strip()
        )
        if "{" in line:
            break
        if verbose:
            print("class  %s" % line)
        lno += 1

    if decl.startswith("class"):
        state = "private"
        class_type = "class"

    name = (
        decl.split(":")[0]
        .replace("class ", "")
        .replace("struct ", "")
        .replace("final", "")
        .strip()
    )

    global orphaned_export
    orphaned_export = False

    while lno < len(lines):
        line = lines[lno].strip()
        lno += 1

        if line == "":
            blanks += 1
            context = ""
            continue

        if line.startswith("/*"):
            lno = consume_comment(lno - 1, lines)
            continue

        if line.startswith("#"):
            lno = consume_ifdef(lno - 1, lines, True)
            continue

        if "TORRENT_DEFINE_ALERT" in line:
            if verbose:
                print("xx    %s" % line)
            blanks += 1
            continue
        if "TORRENT_DEPRECATED" in line:
            if verbose:
                print("xx    %s" % line)
            blanks += 1
            continue

        if line.startswith("//"):
            if verbose:
                print("desc  %s" % line)

            line = line[2:]
            if len(line) and line[0] == " ":
                line = line[1:]
            context += line + "\n"
            continue

        start_brace += line.count("{")
        end_brace += line.count("}")

        if line == "private:":
            state = "private"
        elif line == "protected:":
            state = "protected"
        elif line == "public:":
            state = "public"

        if start_brace > 0 and start_brace == end_brace:
            cls = Class(
                file=filename[11:],
                enums=enums,
                fields=fields,
                type=class_type,
                name=name,
                decl=decl,
                funs=funs,
            )
            return (cls, lno)

        if state != "public" and not internal:
            if verbose:
                print("private %s" % line)
            blanks += 1
            continue

        if start_brace - end_brace > 1:
            if verbose:
                print("scope   %s" % line)
            blanks += 1
            continue

        if looks_like_function(line):
            current_fun, lno = parse_function(lno - 1, lines, filename)
            if current_fun is not None and is_visible(context):
                if context == "" and blanks == 0 and len(funs):
                    funs[-1].signatures.update(current_fun.signatures)
                    funs[-1].names.update(current_fun.names)
                else:
                    if "TODO: " in context:
                        print(
                            "TODO comment in public documentation: %s:%d"
                            % (filename, lno)
                        )
                        sys.exit(1)
                    current_fun.desc = context
                    add_desc(context)
                    if context == "" and not suppress_warning(filename):
                        print(
                            'WARNING: member function "%s" is not documented: '
                            "\x1b[34m%s:%d\x1b[0m"
                            % (
                                name + "::" + str(sorted(current_fun.names)[0]),
                                filename,
                                lno,
                            )
                        )
                    funs.append(current_fun)
                context = ""
                blanks = 0
            continue

        if looks_like_variable(line):
            if "constexpr static" in line:
                print(
                    'ERROR: found "constexpr static", use "static constexpr" '
                    "instead for consistency!\n%s:%d\n%s" % (filename, lno, line)
                )
                sys.exit(1)
            if verbose:
                print("var     %s" % line)
            if not is_visible(context):
                continue
            line = line.split("//")[0].strip()
            # the name may look like this:
            # std::uint8_t fails : 7;
            # int scrape_downloaded = -1;
            # static constexpr peer_flags_t interesting{0x1};
            n = (
                line.split("=")[0]
                .split("{")[0]
                .strip()
                .split(" : ")[0]
                .split(" ")[-1]
                .split(":")[0]
                .split(";")[0]
            )
            if context == "" and blanks == 0 and len(fields):
                fields[-1].names.append(n)
                fields[-1].signatures.append(line)
            else:
                if context == "" and not suppress_warning(filename):
                    print(
                        'WARNING: field "%s" is not documented: \x1b[34m%s:%d\x1b[0m'
                        % (name + "::" + n, filename, lno)
                    )
                add_desc(context)
                field = Field(desc=context, signatures=[line], names=[n])
                fields.append(field)
            context = ""
            blanks = 0
            continue

        if line.startswith("enum "):
            if verbose:
                print("enum    %s" % line)
            if not is_visible(context):
                consume_block(lno - 1, lines)
            else:
                enum, lno = parse_enum(lno - 1, lines, filename)
                if enum is not None:
                    if "TODO: " in context:
                        print(
                            "TODO comment in public documentation: %s:%d"
                            % (filename, lno)
                        )
                        sys.exit(1)
                    enum.desc = context
                    add_desc(context)
                    if context == "" and not suppress_warning(filename):
                        print(
                            'WARNING: enum "%s" is not documented: \x1b[34m%s:%d\x1b[0m'
                            % (name + "::" + enum.name, filename, lno)
                        )
                    enums.append(enum)
                context = ""
            continue

        context = ""

        if verbose:
            if (
                looks_like_forward_decl(line)
                or looks_like_blank(line)
                or looks_like_namespace(line)
            ):
                print("--      %s" % line)
            else:
                print("??      %s" % line)

    if len(name) > 0:
        print(
            "\x1b[31mFAILED TO PARSE CLASS\x1b[0m %s\nfile: %s:%d"
            % (name, filename, lno)
        )
    return (None, lno)


def parse_constant(lno: int, lines: List[str], filename: str) -> Tuple[Constant, int]:
    line = lines[lno].strip()
    if verbose:
        print("const   %s" % line)
    line = line.split("=")[0]
    if "constexpr" in line:
        line = line.split("constexpr")[1]
    if "{" in line and "}" in line:
        line = line.split("{")[0]
    t, name = line.strip().rsplit(" ", 1)
    constant = Constant(file=filename[11:], type=t, name=name)
    return (constant, lno + 1)


def parse_enum(lno: int, lines: List[str], filename: str) -> Tuple[Optional[Enum], int]:
    start_brace = 0
    end_brace = 0
    global anon_index

    line = lines[lno].strip()
    name = (
        line.replace("enum ", "")
        .replace("class ", "")
        .split(":")[0]
        .split("{")[0]
        .strip()
    )
    if len(name) == 0:
        if not internal:
            print("WARNING: anonymous enum at: \x1b[34m%s:%d\x1b[0m" % (filename, lno))
            lno = consume_block(lno - 1, lines)
            return (None, lno)
        name = "anonymous_enum_%d" % anon_index
        anon_index += 1

    values: List[EnumValue] = []
    context = ""
    if "{" not in line:
        if verbose:
            print("enum  %s" % lines[lno])
        lno += 1

    val = 0
    while lno < len(lines):
        line = lines[lno].strip()
        lno += 1

        if line.startswith("//"):
            if verbose:
                print("desc  %s" % line)
            line = line[2:]
            if len(line) and line[0] == " ":
                line = line[1:]
            context += line + "\n"
            continue

        if line.startswith("#"):
            lno = consume_ifdef(lno - 1, lines)
            continue

        start_brace += line.count("{")
        end_brace += line.count("}")

        if "{" in line:
            line = line.split("{")[1]
        line = line.split("}")[0]

        if len(line):
            if verbose:
                print("enumv %s" % lines[lno - 1])
            for v in line.split(","):
                v = v.strip()
                if v.startswith("//"):
                    break
                if v == "":
                    continue
                valstr = ""
                try:
                    if "=" in v:
                        val = int(v.split("=")[1].strip(), 0)
                    valstr = str(val)
                except Exception:
                    pass

                if "=" in v:
                    v = v.split("=")[0].strip()
                if is_visible(context):
                    add_desc(context)
                    values.append(EnumValue(name=v.strip(), desc=context, val=valstr))
                    if verbose:
                        print("enumv %s" % valstr)
                context = ""
                val += 1
        else:
            if verbose:
                print("??    %s" % lines[lno - 1])

        if start_brace > 0 and start_brace == end_brace:
            enum = Enum(file=filename[11:], name=name, values=values)
            return (enum, lno)

    if len(name) > 0:
        print(
            "\x1b[31mFAILED TO PARSE ENUM\x1b[0m %s\nline: %d\nfile: %s"
            % (name, lno, filename)
        )
    return (None, lno)


def consume_block(lno: int, lines: List[str]) -> int:
    start_brace = 0
    end_brace = 0

    while lno < len(lines):
        line = lines[lno].strip()
        if verbose:
            print("xx    %s" % line)
        lno += 1

        start_brace += line.count("{")
        end_brace += line.count("}")

        if start_brace > 0 and start_brace == end_brace:
            break
    return lno


def consume_comment(lno: int, lines: List[str]) -> int:
    while lno < len(lines):
        line = lines[lno].strip()
        if verbose:
            print("xx    %s" % line)
        lno += 1
        if "*/" in line:
            break

    return lno


def trim_define(line: str) -> str:
    return (
        line.replace("#ifndef", "")
        .replace("#ifdef", "")
        .replace("#if", "")
        .replace("defined", "")
        .replace("TORRENT_ABI_VERSION == 1", "")
        .replace("TORRENT_ABI_VERSION <= 2", "")
        .replace("TORRENT_ABI_VERSION < 3", "")
        .replace("TORRENT_ABI_VERSION < 4", "")
        .replace("||", "")
        .replace("&&", "")
        .replace("(", "")
        .replace(")", "")
        .replace("!", "")
        .replace("\\", "")
        .strip()
    )


def consume_ifdef(lno: int, lines: List[str], warn_on_ifdefs: bool = False) -> int:
    line = lines[lno].strip()
    lno += 1

    start_if = 1
    end_if = 0

    if verbose:
        print("prep  %s" % line)

    if warn_on_ifdefs and line.strip().startswith("#if"):
        while line.endswith("\\"):
            lno += 1
            line += lines[lno].strip()
            if verbose:
                print("prep  %s" % lines[lno].strip())
        define = trim_define(line)
        if "TORRENT_" in define and "TORRENT_ABI_VERSION" not in define:
            print(
                '\x1b[31mWARNING: possible ABI breakage in public struct! "%s" '
                "\x1b[34m %s:%d\x1b[0m" % (define, filename, lno)
            )
            # we've already warned once, no need to do it twice
            warn_on_ifdefs = False
        elif define != "":
            print(
                '\x1b[33msensitive define in public struct: "%s"\x1b[34m %s:%d\x1b[0m'
                % (define, filename, lno)
            )

    if (
        line.startswith("#if")
        and (
            " TORRENT_USE_ASSERTS" in line
            or " TORRENT_USE_INVARIANT_CHECKS" in line
            or " TORRENT_ASIO_DEBUGGING" in line
        )
        or line == "#if TORRENT_ABI_VERSION == 1"
        or line == "#if TORRENT_ABI_VERSION <= 2"
        or line == "#if TORRENT_ABI_VERSION < 3"
        or line == "#if TORRENT_ABI_VERSION < 4"
    ):
        while lno < len(lines):
            line = lines[lno].strip()
            lno += 1
            if verbose:
                print("prep  %s" % line)
            if line.startswith("#endif"):
                end_if += 1
            if line.startswith("#if"):
                start_if += 1
            if line == "#else" and start_if - end_if == 1:
                break
            if start_if - end_if == 0:
                break
        return lno
    else:
        while line.endswith("\\") and lno < len(lines):
            line = lines[lno].strip()
            lno += 1
            if verbose:
                print("prep  %s" % line)

    return lno


for filename in files:
    h = open(filename)
    lines = h.read().split("\n")

    if verbose:
        print("\n=== %s ===\n" % filename)

    blanks = 0
    lno = 0
    global orphaned_export
    orphaned_export = False

    while lno < len(lines):
        line = lines[lno].strip()

        if orphaned_export:
            print(
                "ERROR: TORRENT_EXPORT without function or class!\n%s:%d\n%s"
                % (filename, lno, line)
            )
            sys.exit(1)

        lno += 1

        if line == "":
            blanks += 1
            context = ""
            continue

        if (
            "TORRENT_EXPORT" in line.split()
            and "ifndef TORRENT_EXPORT" not in line
            and "define TORRENT_DEPRECATED_EXPORT TORRENT_EXPORT" not in line
            and "define TORRENT_EXPORT" not in line
            and "for TORRENT_EXPORT" not in line
            and "TORRENT_EXPORT TORRENT_CFG" not in line
            and "extern TORRENT_EXPORT " not in line
            and "struct TORRENT_EXPORT " not in line
        ):
            orphaned_export = True
            if verbose:
                print("maybe orphaned: %s\n" % line)

        if line.startswith("//") and line[2:].strip() == "OVERVIEW":
            # this is a section overview
            current_overview = ""
            while lno < len(lines):
                line = lines[lno].strip()
                lno += 1
                if not line.startswith("//"):
                    # end of overview
                    overviews[filename[11:]] = current_overview
                    current_overview = ""
                    break
                line = line[2:]
                if line.startswith(" "):
                    line = line[1:]
                current_overview += line + "\n"

        if line.startswith("//"):
            if verbose:
                print("desc  %s" % line)
            line = line[2:]
            if len(line) and line[0] == " ":
                line = line[1:]
            context += line + "\n"
            continue

        if line.startswith("/*"):
            lno = consume_comment(lno - 1, lines)
            continue

        if line.startswith("#"):
            lno = consume_ifdef(lno - 1, lines)
            continue

        if (
            line == "namespace aux {"
            or line == "namespace ssl {"
            or line == "namespace libtorrent { namespace aux {"
        ) and not internal:
            lno = consume_block(lno - 1, lines)
            context = ""
            continue

        if (
            "namespace aux" in line
            and "//" not in line.split("namespace")[0]
            and "}" not in line.split("namespace")[1]
        ):
            print(
                "ERROR: whitespace preceding namespace declaration: %s:%d"
                % (filename, lno)
            )
            sys.exit(1)

        if "TORRENT_DEPRECATED" in line:
            if ("class " in line or "struct " in line) and ";" not in line:
                lno = consume_block(lno - 1, lines)
                context = ""
            blanks += 1
            if verbose:
                print("xx    %s" % line)
            continue

        if looks_like_constant(line):
            if "constexpr static" in line:
                print(
                    'ERROR: found "constexpr static", use "static constexpr" '
                    "instead for consistency!\n%s:%d\n%s" % (filename, lno, line)
                )
                sys.exit(1)
            current_constant, lno = parse_constant(lno - 1, lines, filename)
            if current_constant is not None and is_visible(context):
                if "TODO: " in context:
                    print(
                        "TODO comment in public documentation: %s:%d" % (filename, lno)
                    )
                    sys.exit(1)
                current_constant.desc = context
                add_desc(context)
                if context == "":
                    print(
                        'WARNING: constant "%s" is not documented: \x1b[34m%s:%d\x1b[0m'
                        % (current_constant.name, filename, lno)
                    )
                t = current_constant.type
                if t in constants:
                    constants[t].append(current_constant)
                else:
                    constants[t] = [current_constant]
            continue

        if (
            "TORRENT_EXPORT " in line
            or line.startswith("inline ")
            or line.startswith("template")
            or internal
        ):
            if line.startswith("class ") or line.startswith("struct "):
                if not line.endswith(";"):
                    current_class, lno = parse_class(lno - 1, lines, filename)
                    if current_class is not None and is_visible(context):
                        if "TODO: " in context:
                            print(
                                "TODO comment in public documentation: %s:%d"
                                % (filename, lno)
                            )
                            sys.exit(1)
                        current_class.desc = context
                        add_desc(context)
                        if context == "":
                            print(
                                'WARNING: class "%s" is not documented: '
                                "\x1b[34m%s:%d\x1b[0m"
                                % (current_class.name, filename, lno)
                            )
                        classes.append(current_class)
                context = ""
                blanks += 1
                continue

            if looks_like_function(line):
                current_fun, lno = parse_function(lno - 1, lines, filename)
                if current_fun is not None and is_visible(context):
                    if context == "" and blanks == 0 and len(functions):
                        functions[-1].signatures.update(current_fun.signatures)
                        functions[-1].names.update(current_fun.names)
                    else:
                        if "TODO: " in context:
                            print(
                                "TODO comment in public documentation: %s:%d"
                                % (filename, lno)
                            )
                            sys.exit(1)
                        current_fun.desc = context
                        add_desc(context)
                        if context == "":
                            print(
                                'WARNING: function "%s" is not documented: '
                                "\x1b[34m%s:%d\x1b[0m"
                                % (sorted(current_fun.names)[0], filename, lno)
                            )
                        functions.append(current_fun)
                    context = ""
                    blanks = 0
                continue

        if (
            "enum class " not in line and "class " in line or "struct " in line
        ) and ";" not in line:
            lno = consume_block(lno - 1, lines)
            context = ""
            blanks += 1
            continue

        if line.startswith("enum "):
            if not is_visible(context):
                consume_block(lno - 1, lines)
            else:
                current_enum, lno = parse_enum(lno - 1, lines, filename)
                if current_enum is not None and is_visible(context):
                    if "TODO: " in context:
                        print(
                            "TODO comment in public documentation: %s:%d"
                            % (filename, lno)
                        )
                        sys.exit(1)
                    current_enum.desc = context
                    add_desc(context)
                    if context == "":
                        print(
                            'WARNING: enum "%s" is not documented: \x1b[34m%s:%d\x1b[0m'
                            % (current_enum.name, filename, lno)
                        )
                    enums.append(current_enum)
            context = ""
            blanks += 1
            continue

        blanks += 1
        if verbose:
            if (
                looks_like_forward_decl(line)
                or looks_like_blank(line)
                or looks_like_namespace(line)
            ):
                print("--    %s" % line)
            else:
                print("??    %s" % line)

        context = ""
    h.close()

# ====================================================================
#
#                               RENDER PART
#
# ====================================================================


class Category:
    def __init__(
        self,
        *,
        filename: str,
        classes: Iterable[Class] = (),
        functions: Iterable[Function] = (),
        enums: Iterable[Enum] = (),
        constants: Mapping[str, Iterable[Constant]] = None,
        overview: str = None,
    ):
        self.filename = filename
        self.classes = list(classes)
        self.functions = list(functions)
        self.enums = list(enums)
        self.constants = {k: list(values) for k, values in (constants or {}).items()}
        self.overview = overview


def new_category(cat: str) -> Category:
    return Category(filename="reference-%s.rst" % cat.replace(" ", "_"))


if dump:

    if verbose:
        print("\n===============================\n")

    for cls in classes:
        print("\x1b[4m%s\x1b[0m %s\n{" % (cls.type, cls.name))
        for func in cls.funs:
            for s in func.signatures:
                print("   %s" % s.replace("\n", "\n   "))

        if len(cls.funs) > 0 and len(cls.fields) > 0:
            print("")

        for field in cls.fields:
            for s in field.signatures:
                print("   %s" % s)

        if len(cls.fields) > 0 and len(cls.enums) > 0:
            print("")

        for e in cls.enums:
            print("   \x1b[4menum\x1b[0m %s\n   {" % e.name)
            for v in e.values:
                print("      %s" % v.name)
            print("   };")
        print("};\n")

    for func in functions:
        print("%s" % func.signatures)

    for e in enums:
        print("\x1b[4menum\x1b[0m %s\n{" % e.name)
        for v in e.values:
            print("   %s" % v.name)
        print("};")

    for constant_list in constants.values():
        for constant in constant_list:
            print("\x1b[4mconstant\x1b[0m %s %s\n" % (constant.type, constant.name))

categories: Dict[str, Category] = {}

for cls in classes:
    cat = categorize_symbol(cls.name, cls.file)
    if cat not in categories:
        categories[cat] = new_category(cat)

    if cls.file in overviews:
        categories[cat].overview = overviews[cls.file]

    filename = categories[cat].filename.replace(".rst", ".html") + "#"
    categories[cat].classes.append(cls)
    symbols[cls.name] = filename + cls.name
    for func in cls.funs:
        for n in func.names:
            symbols[n] = filename + n
            symbols[cls.name + "::" + n] = filename + n

    for field in cls.fields:
        for n in field.names:
            symbols[cls.name + "::" + n] = filename + n

    for e in cls.enums:
        symbols[e.name] = filename + e.name
        symbols[cls.name + "::" + e.name] = filename + e.name
        for v in e.values:
            # symbols[v['name']] = filename + v['name']
            symbols[e.name + "::" + v.name] = filename + v.name
            symbols[cls.name + "::" + v.name] = filename + v.name

for func in functions:
    cat = categorize_symbol(sorted(func.names)[0], func.file)
    if cat not in categories:
        categories[cat] = new_category(cat)

    if func.file in overviews:
        categories[cat].overview = overviews[func.file]

    for n in func.names:
        symbols[n] = categories[cat].filename.replace(".rst", ".html") + "#" + n
    categories[cat].functions.append(func)

for e in enums:
    cat = categorize_symbol(e.name, e.file)
    if cat not in categories:
        categories[cat] = new_category(cat)
    categories[cat].enums.append(e)
    filename = categories[cat].filename.replace(".rst", ".html") + "#"
    symbols[e.name] = filename + e.name
    for v in e.values:
        symbols[e.name + "::" + v.name] = filename + v.name

for t, constant_list in constants.items():
    for const in constant_list:
        cat = categorize_symbol(t, const.file)
        if cat not in categories:
            categories[cat] = new_category(cat)
        if t not in categories[cat].constants:
            categories[cat].constants[t] = [const]
        else:
            categories[cat].constants[t].append(const)
        filename = categories[cat].filename.replace(".rst", ".html") + "#"
        symbols[t + "::" + const.name] = filename + t + "::" + const.name
    symbols[t] = filename + t


def print_declared_in(out: IO[str], o: Declared) -> None:
    out.write('Declared in "%s"\n\n' % print_link(o.file, "include/%s" % o.file))
    print(dump_link_targets(), file=out)


# returns RST marked up string


def linkify_symbols(string: str) -> str:
    lines = string.split("\n")
    ret: List[str] = []
    in_literal = False
    lno = 0
    return_string = ""
    for line in lines:
        lno += 1
        # don't touch headlines, i.e. lines whose
        # next line entirely contains one of =, - or .
        if lno < len(lines) - 1:
            next_line = lines[lno]
        else:
            next_line = ""

        if ".. include:: " in line:
            return_string += "\n".join(ret)
            ret = [line]
            return_string += dump_link_targets() + "\n"
            continue

        if (
            len(next_line) > 0
            and lines[lno].replace("=", "").replace("-", "").replace(".", "") == ""
        ):
            ret.append(line)
            continue

        if line.startswith("|"):
            ret.append(line)
            continue
        if in_literal and not line.startswith("\t") and not line == "":
            # print('  end literal: "%s"' % line)
            in_literal = False
        if in_literal:
            # print('  literal: "%s"' % line)
            ret.append(line)
            continue
        if (
            line.strip() == ".. parsed-literal::"
            or line.strip().startswith(".. code::")
            or (not line.strip().startswith("..") and line.endswith("::"))
        ):
            # print('  start literal: "%s"' % line)
            in_literal = True
        words = line.split(" ")

        for i in range(len(words)):
            # it's important to preserve leading
            # tabs, since that's relevant for
            # rst markup

            leading = ""
            w = words[i]

            if len(w) == 0:
                continue

            while len(w) > 0 and w[0] in ["\t", " ", "(", "[", "{"]:
                leading += w[0]
                w = w[1:]

            # preserve commas and dots at the end
            w = w.strip()
            trailing = ""

            if len(w) == 0:
                continue

            while len(w) > 1 and w[-1] in [".", ",", ")"] and w[-2:] != "()":
                trailing = w[-1] + trailing
                w = w[:-1]

            link_name = w

            # print(w)

            if len(w) == 0:
                continue

            if link_name[-1] == "_":
                link_name = link_name[:-1]

            if w in symbols:
                link_name = link_name.replace("-", " ")
                # print('  found %s -> %s' % (w, link_name))
                words[i] = leading + print_link(link_name, symbols[w]) + trailing
        ret.append(" ".join(words))
    return_string += "\n".join(ret)
    return return_string


link_targets: List[str] = []


def print_link(name: str, target: str) -> str:
    global link_targets
    link_targets.append(target)
    return "`%s`__" % name


def dump_link_targets(indent: str = "") -> str:
    global link_targets
    ret = "\n"
    for link in link_targets:
        ret += "%s__ %s\n" % (indent, link)
    link_targets = []
    return ret


def heading(string: str, col: str, indent: str = "") -> str:
    string = string.strip()
    return "\n" + indent + string + "\n" + indent + (col * len(string)) + "\n"


def render_enums(
    out: IO[str],
    enums: Iterable[Enum],
    print_declared_reference: bool,
    header_level: str,
) -> None:
    for e in enums:
        print(".. raw:: html\n", file=out)
        print('\t<a name="%s"></a>' % e.name, file=out)
        print("", file=out)
        dump_report_issue("enum " + e.name, out)
        print(heading("enum %s" % e.name, header_level), file=out)

        print_declared_in(out, e)

        width = [len("name"), len("value"), len("description")]

        for i in range(len(e.values)):
            e.values[i].desc = linkify_symbols(e.values[i].desc)

        for v in e.values:
            width[0] = max(width[0], len(v.name))
            width[1] = max(width[1], len(v.val))
            for d in v.desc.split("\n"):
                width[2] = max(width[2], len(d))

        print(
            "+-"
            + ("-" * width[0])
            + "-+-"
            + ("-" * width[1])
            + "-+-"
            + ("-" * width[2])
            + "-+",
            file=out,
        )
        print(
            "| "
            + "name".ljust(width[0])
            + " | "
            + "value".ljust(width[1])
            + " | "
            + "description".ljust(width[2])
            + " |",
            file=out,
        )
        print(
            "+="
            + ("=" * width[0])
            + "=+="
            + ("=" * width[1])
            + "=+="
            + ("=" * width[2])
            + "=+",
            file=out,
        )
        for v in e.values:
            parts = v.desc.split("\n")
            if len(parts) == 0:
                parts = [""]
            print(
                "| "
                + v.name.ljust(width[0])
                + " | "
                + v.val.ljust(width[1])
                + " | "
                + parts[0].ljust(width[2])
                + " |",
                file=out,
            )
            for s in parts[1:]:
                print(
                    "| "
                    + (" " * width[0])
                    + " | "
                    + (" " * width[1])
                    + " | "
                    + s.ljust(width[2])
                    + " |",
                    file=out,
                )
            print(
                "+-"
                + ("-" * width[0])
                + "-+-"
                + ("-" * width[1])
                + "-+-"
                + ("-" * width[2])
                + "-+",
                file=out,
            )
        print("", file=out)

        print(dump_link_targets(), file=out)


sections = {
    "Core": 0,
    "DHT": 0,
    "Session": 0,
    "Torrent Handle": 0,
    "Torrent Info": 0,
    "Trackers": 0,
    "Settings": 0,
    "Torrent Status": 0,
    "Stats": 0,
    "Resume Data": 0,
    "Add Torrent": 0,
    "Bencoding": 1,
    "Bdecoding": 1,
    "Filter": 1,
    "Error Codes": 1,
    "Create Torrents": 1,
    "PeerClass": 2,
    "ed25519": 2,
    "Utility": 2,
    "Storage": 2,
    "Custom Storage": 2,
    "Plugins": 2,
    "Alerts": 3,
}


def print_toc(out: IO[str], categories: Mapping[str, Category], s: int) -> None:

    main_toc = False

    for cat in categories:
        if (s != 2 and cat not in sections) or (cat in sections and sections[cat] != s):
            continue

        if not main_toc:
            out.write(".. container:: main-toc\n\n")
            main_toc = True

        print("\t.. rubric:: %s\n" % cat, file=out)

        if categories[cat].overview is not None:
            print("\t| overview__", file=out)

        for cls in categories[cat].classes:
            print("\t| " + print_link(cls.name, symbols[cls.name]), file=out)
        for func in categories[cat].functions:
            for n in func.names:
                print("\t| " + print_link(n, symbols[n]), file=out)
        for e in categories[cat].enums:
            print("\t| " + print_link(e.name, symbols[e.name]), file=out)
        for t in categories[cat].constants:
            print("\t| " + print_link(t, symbols[t]), file=out)
        print("", file=out)

        if categories[cat].overview is not None:
            print(
                "\t__ %s#overview" % categories[cat].filename.replace(".rst", ".html"),
                file=out,
            )
        print(dump_link_targets("\t"), file=out)


def dump_report_issue(h: str, out: IO[str]) -> None:
    print(
        (
            '.. raw:: html\n\n\t<span class="report-issue">[<a '
            'href="http://github.com/arvidn/libtorrent/issues/new?'
            "title=docs:{0}&labels="
            'documentation&body={1}">report issue</a>]</span>\n\n'
        ).format(
            urllib.parse.quote_plus(h),
            urllib.parse.quote_plus(
                'Documentation under heading "' + h + '" could be improved'
            ),
        ),
        file=out,
    )


def render(out: IO[str], category: Category) -> None:

    classes = category.classes
    functions = category.functions
    enums = category.enums
    constants = category.constants

    if category.overview is not None:
        out.write("%s\n" % linkify_symbols(category.overview))

    for cls in classes:

        print(".. raw:: html\n", file=out)
        print('\t<a name="%s"></a>' % cls.name, file=out)
        print("", file=out)

        dump_report_issue("class " + cls.name, out)
        out.write("%s\n" % heading(cls.name, "-"))
        print_declared_in(out, cls)
        cls.desc = linkify_symbols(cls.desc)
        out.write("%s\n" % cls.desc)
        print(dump_link_targets(), file=out)

        print("\n.. parsed-literal::\n\t", file=out)

        block = "\n%s\n{\n" % cls.decl
        for func in cls.funs:
            for s in func.signatures:
                block += "   %s\n" % highlight_signature(s.replace("\n", "\n   "))

        if len(cls.funs) > 0 and len(cls.enums) > 0:
            block += "\n"

        first = True
        for e in cls.enums:
            if not first:
                block += "\n"
            first = False
            block += "   enum %s\n   {\n" % e.name
            for v in e.values:
                block += "      %s,\n" % v.name
            block += "   };\n"

        if len(cls.funs) + len(cls.enums) > 0 and len(cls.fields):
            block += "\n"

        for field in cls.fields:
            for s in field.signatures:
                block += "   %s\n" % highlight_name(s)

        block += "};"

        print(block.replace("\n", "\n\t") + "\n", file=out)

        for func in cls.funs:
            if func.desc == "":
                continue
            print(".. raw:: html\n", file=out)
            for n in func.names:
                print('\t<a name="%s"></a>' % n, file=out)
            print("", file=out)
            h = " ".join(func.names)
            dump_report_issue("%s::[%s]" % (cls.name, h), out)
            print(heading(h, "."), file=out)

            block = ".. parsed-literal::\n\n"

            for s in func.signatures:
                block += highlight_signature(s.replace("\n", "\n   ")) + "\n"
            print("%s\n" % block.replace("\n", "\n\t"), file=out)
            func.desc = linkify_symbols(func.desc)
            print("%s" % func.desc, file=out)

            print(dump_link_targets(), file=out)

        render_enums(out, cls.enums, False, ".")

        for field in cls.fields:
            if field.desc == "":
                continue

            print(".. raw:: html\n", file=out)
            for n in field.names:
                print('\t<a name="%s"></a>' % n, file=out)
            print("", file=out)
            h = " ".join(field.names)
            dump_report_issue("%s::[%s]" % (cls.name, h), out)
            print(h, file=out)
            field.desc = linkify_symbols(field.desc)
            print("\t%s" % field.desc.replace("\n", "\n\t"), file=out)

            print(dump_link_targets(), file=out)

    for func in functions:
        print(".. raw:: html\n", file=out)
        for n in func.names:
            print('\t<a name="%s"></a>' % n, file=out)
        print("", file=out)
        h = " ".join(func.names)
        dump_report_issue(h, out)
        print(heading(h, "-"), file=out)
        print_declared_in(out, func)

        block = ".. parsed-literal::\n\n"
        for s in func.signatures:
            block += highlight_signature(s) + "\n"

        print("%s\n" % block.replace("\n", "\n\t"), file=out)
        print(linkify_symbols(func.desc), file=out)

        print(dump_link_targets(), file=out)

    render_enums(out, enums, True, "-")

    for t, constant_list in constants.items():
        print(".. raw:: html\n", file=out)
        print('\t<a name="%s"></a>\n' % t, file=out)
        dump_report_issue(t, out)
        print(heading(t, "-"), file=out)
        print_declared_in(out, constant_list[0])

        for constant in constant_list:
            print(".. raw:: html\n", file=out)
            print('\t<a name="%s::%s"></a>\n' % (t, constant.name), file=out)
            print(constant.name, file=out)
            constant.desc = linkify_symbols(constant.desc)
            print("\t%s" % constant.desc.replace("\n", "\n\t"), file=out)
            print(dump_link_targets("\t"), file=out)

        print("", file=out)

    print(dump_link_targets(), file=out)

    for i in static_links:
        print(i, file=out)


if single_page_output:

    out = open("single-page-ref.rst", "w+")
    out.write(
        """.. include:: header.rst

`home`__

__ reference.html

.. contents:: Table of contents
  :depth: 2
  :backlinks: none

"""
    )

    for cat in categories:
        render(out, categories[cat])

    out.close()

else:

    out = open("reference.rst", "w+")
    out.write(
        """=======================
reference documentation
=======================

"""
    )

    out.write("`single-page version`__\n\n__ single-page-ref.html\n\n")

    for i in range(4):

        print_toc(out, categories, i)

    out.close()

    for cat in categories:
        out = open(categories[cat].filename, "w+")

        out.write(
            """.. include:: header.rst

`home`__

__ reference.html

.. contents:: Table of contents
  :depth: 2
  :backlinks: none

"""
        )

        render(out, categories[cat])

        out.close()

    #       for s in symbols:
    #           print(s)

    for in_name, out_name in list(preprocess_rst.items()):
        fp = open(in_name, "r")
        out = open(out_name, "w+")
        print("processing %s -> %s" % (in_name, out_name))
        link = linkify_symbols(fp.read())
        print(link, end=" ", file=out)

        print(dump_link_targets(), file=out)

        out.close()
        fp.close()
