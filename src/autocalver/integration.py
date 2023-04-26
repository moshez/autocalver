"""
Generate versions automatically based on version control commit log
"""
from __future__ import annotations

import datetime
from email import parser as email_parser
import os
import pathlib
import re
import shlex
import subprocess
import zoneinfo

from dateutil import parser as du_parser
import tomli
import setuptools


def _datetime_from_log(text):
    no_first_line = text.split("\n", 1)[1]
    headers = email_parser.Parser().parsestr(no_first_line)
    date_str = headers["Date"]
    if date_str is None:
        raise ValueError("no date", text)
    return du_parser.parse(date_str).astimezone(zoneinfo.ZoneInfo("UTC"))


def _version_from_datetime(when):
    day = when.date()
    beginning = datetime.datetime.combine(
        day, datetime.datetime.min.time(), tzinfo=when.tzinfo
    )
    seconds = (when - beginning) // datetime.timedelta(seconds=1)
    version = f"{when.year}.{when.month}.{when.day}.{seconds}"
    return version


def _get_suffix(branch_value, match):
    if branch_value == "":
        return "dev1"
    elif not re.match(match, branch_value):
        return "rc1"
    else:
        return ""


def get_configuration(dirname):
    """
    Get the [tool.autocalver] configuration from a pyproject.toml
    """
    try:
        contents = (pathlib.Path(dirname) / "pyproject.toml").read_text()
    except FileNotFoundError:
        contents = ""
    root = tomli.loads(contents)
    return root.get("tool", {}).get("autocalver", {})


def _get_log_contents(configuration):
    log = configuration["log"]
    log_file = pathlib.Path(log)
    log_file_read_text = log_file.read_text
    try:
        return log_file_read_text()
    except FileNotFoundError:
        command = configuration["log_command"]
        command_line = shlex.split(command)
        res = subprocess.run(command_line, check=True, text=True, capture_output=True)
        log_file.write_text(res.stdout)
        return log_file_read_text()


def set_dist_version(dist, *, configuration, environ):
    """
    Set version in distribution based on configuration and environment
    """
    if configuration.get("use", False) is not True:
        return
    log_contents = _get_log_contents(configuration)
    when = _datetime_from_log(log_contents)
    is_main_var = configuration["is_main_var"]
    is_main_match = configuration["is_main_match"]
    version = _version_from_datetime(when) + _get_suffix(
        environ.get(is_main_var, ""), is_main_match
    )
    dist.metadata.version = version


def guess_version(dist: setuptools.Distribution):  # pragma: no cover
    """
    setuptools entrypoint

    Set version in distribution based on configuration and environment.
    """
    configuration = get_configuration(".")
    set_dist_version(dist, configuration=configuration, environ=os.environ)


def find_files(path):
    """
    setuptools entrypoint

    Add the version control log to the data files
    """
    configuration = get_configuration(path)
    if configuration.get("use", False) is not True:
        return []
    log = configuration["log"]
    return [log]
