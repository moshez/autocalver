"""
Test automatic versioning calculations
"""

import pathlib
import tempfile
import textwrap
import shlex
from unittest import mock

import pytest

from autocalver import integration


def test_get_configuration():
    """
    Configuration is read from [tool.autocalver] section of pyrproject.toml
    """
    configuration = textwrap.dedent(
        """
    [tool.autocalver]
    use = true
    log = "git-log-head"
    is_main_var = "BUILD_BRANCH_REF"
    is_main_match = ".*/main$"
    """
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject = pathlib.Path(tmpdir) / "pyproject.toml"
        pyproject.write_text(configuration)
        parsed = integration.get_configuration(tmpdir)
    assert "use" in parsed
    assert parsed.pop("use") is True
    assert "log" in parsed
    assert parsed.pop("log") == "git-log-head"
    assert set(parsed.keys()) == {"is_main_var", "is_main_match"}


def test_get_no_configuration():
    """
    With no pyproject.toml, configuration is empty.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        parsed = integration.get_configuration(tmpdir)
    assert parsed == {}


def test_get_empty_configuration():
    """
    Without relevant section in pyproject.toml, configuration is empty.
    """
    configuration = textwrap.dedent(
        """
    [tool.not-autocalver]
    clowns = "not funny"
    """
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject = pathlib.Path(tmpdir) / "pyproject.toml"
        pyproject.write_text(configuration)
        parsed = integration.get_configuration(tmpdir)
    assert parsed == {}


def test_no_use_no_version():
    """
    When tool is explicitly disabled, it does not update the version.
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    configuration = {"use": False}
    integration.set_dist_version(dist, configuration=configuration, environ={})
    assert dist.metadata.version == "1.2.3.4"


def test_no_config_no_version():
    """
    When explicit configuration is not enabled, tool is disabled.
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    configuration = {}
    integration.set_dist_version(dist, configuration=configuration, environ={})
    assert dist.metadata.version == "1.2.3.4"


def test_release():
    """
    Release versions are based the date from the log file.
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    with tempfile.NamedTemporaryFile(mode="w+") as fpin:
        fpin.write(
            textwrap.dedent(
                """\
        commit 5b540c54b5c62d365472e1f1cf42a1ffaef60334 (HEAD -> main, origin/main, origin/HEAD)
        Author: Person Name An E-mail <moshe@example.com>
        Date:   2021-10-11 08:11:13 -0100

            stuff accomplished
        """
            )
        )
        fpin.flush()
        configuration = dict(
            use=True,
            log=fpin.name,
            is_main_var="BRANCH",
            is_main_match="main$",
        )
        integration.set_dist_version(
            dist, configuration=configuration, environ=dict(BRANCH="main")
        )
    parts = dist.metadata.version.split(".")
    assert parts[-1].strip("0123456789") == ""
    year, month, day, seconds = map(int, parts)
    assert (year, month, day) == (2021, 10, 11)
    minutes, seconds = divmod(seconds, 60)
    assert seconds == 13
    hours, minutes = divmod(minutes, 60)
    assert minutes == 11
    hours -= 1  # TZ offset
    assert hours == 8


def test_release_candidate():
    """
    RC versions have an "rc<N>" at the end
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    with tempfile.NamedTemporaryFile(mode="w+") as fpin:
        fpin.write(
            textwrap.dedent(
                """\
        commit 5b540c54b5c62d365472e1f1cf42a1ffaef60334 (HEAD -> main, origin/main, origin/HEAD)
        Author: Person Name An E-mail <moshe@example.com>
        Date:   2021-10-11 08:11:13 -0100

            stuff accomplished
        """
            )
        )
        fpin.flush()
        configuration = dict(
            use=True,
            log=fpin.name,
            is_main_var="BRANCH",
            is_main_match="main$",
        )
        integration.set_dist_version(
            dist, configuration=configuration, environ=dict(BRANCH="proj-121")
        )
    parts = dist.metadata.version.split(".")
    assert parts[-1].strip("0123456789") == "rc"
    year, month, day = map(int, parts[:-1])
    seconds = int(parts[-1].split("rc")[0])
    assert (year, month, day) == (2021, 10, 11)
    minutes, seconds = divmod(seconds, 60)
    assert seconds == 13
    hours, minutes = divmod(minutes, 60)
    assert minutes == 11
    hours -= 1  # TZ offset
    assert hours == 8


def test_local_build():
    """
    Local versions have a "<dev>N" at the end.
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    with tempfile.NamedTemporaryFile(mode="w+") as fpin:
        fpin.write(
            textwrap.dedent(
                """\
        commit 5b540c54b5c62d365472e1f1cf42a1ffaef60334 (HEAD -> main, origin/main, origin/HEAD)
        Author: Person Name An E-mail <moshe@example.com>
        Date:   2021-10-11 08:11:13 -0100

            stuff accomplished
        """
            )
        )
        fpin.flush()
        configuration = dict(
            use=True,
            log=fpin.name,
            is_main_var="BRANCH",
            is_main_match="main$",
        )
        integration.set_dist_version(dist, configuration=configuration, environ={})
    parts = dist.metadata.version.split(".")
    assert parts[-1].strip("0123456789") == "dev"
    year, month, day = map(int, parts[:-1])
    seconds = int(parts[-1].split("dev")[0])
    assert (year, month, day) == (2021, 10, 11)
    minutes, seconds = divmod(seconds, 60)
    assert seconds == 13
    hours, minutes = divmod(minutes, 60)
    assert minutes == 11
    hours -= 1  # TZ offset
    assert hours == 8


def test_no_date():
    """
    When the log has no date, an exception is raised.
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    with tempfile.NamedTemporaryFile(mode="w+") as fpin:
        fpin.write(
            textwrap.dedent(
                """\
        commit 5b540c54b5c62d365472e1f1cf42a1ffaef60334 (HEAD -> main, origin/main, origin/HEAD)
        Author: Person Name An E-mail <moshe@example.com>

            stuff accomplished
        """
            )
        )
        fpin.flush()
        configuration = dict(
            use=True,
            log=fpin.name,
            is_main_var="BRANCH",
            is_main_match="main$",
        )
        with pytest.raises(ValueError):
            integration.set_dist_version(dist, configuration=configuration, environ={})


def test_no_log():
    """
    Without a log, the log command is being run
    """
    dist = mock.Mock(name="dist")
    dist.metadata.version = "1.2.3.4"
    with tempfile.TemporaryDirectory() as dirname:
        log_name = dirname + "/git-log-head"
        command = shlex.join(
            [
                "python",
                "-c",
                textwrap.dedent(
                    """\
            print("----ignored-line")
            print("Date:   2021-10-11 08:11:13 -0100")
            print("")
            print("    a comment")
        """
                ),
            ]
        )
        configuration = dict(
            use=True,
            log=log_name,
            log_command=command,
            is_main_var="BRANCH",
            is_main_match="main$",
        )
        integration.set_dist_version(dist, configuration=configuration, environ={})
    parts = dist.metadata.version.split(".")
    assert parts[-1].strip("0123456789") == "dev"
    year, month, day = map(int, parts[:-1])
    seconds = int(parts[-1].split("dev")[0])
    assert (year, month, day) == (2021, 10, 11)
    minutes, seconds = divmod(seconds, 60)
    assert seconds == 13
    hours, minutes = divmod(minutes, 60)
    assert minutes == 11
    hours -= 1  # TZ offset
    assert hours == 8


def test_find_files_no_use():
    """
    Find files returns empty if use is not true
    """
    configuration = textwrap.dedent(
        """
    [tool.autocalver]
    use = false
    log = "git-log-head"
    is_main_var = "BUILD_BRANCH_REF"
    is_main_match = ".*/main$"
    """
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject = pathlib.Path(tmpdir) / "pyproject.toml"
        pyproject.write_text(configuration)
        found = integration.find_files(tmpdir)
    assert found == []


def test_find_files_use_git_log_head():
    """
    Find files returns log if use is true
    """
    configuration = textwrap.dedent(
        """
    [tool.autocalver]
    use = true
    log = "git-log-head"
    is_main_var = "BUILD_BRANCH_REF"
    is_main_match = ".*/main$"
    """
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        pyproject = pathlib.Path(tmpdir) / "pyproject.toml"
        pyproject.write_text(configuration)
        found = integration.find_files(tmpdir)
    assert found == ["git-log-head"]
