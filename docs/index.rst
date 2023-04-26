Autocalver
==========

.. toctree::
   :maxdepth: 2

Autocalver removes the need
to bump,
manually
*or*
automatically,
your versions.
Instead,
the version will be automatically generated.

Quick start
-----------

Autocalver is a setuptools plugin.
It needs to be
*installed*
and
*activated*.

The following is usually what needs to be copied to the
:code:`pyproject.toml`:

.. code::
    toml
    
    [build-system]
    requires = ["setuptools", "autocalver"]
    build-backend = "setuptools.build_meta"

    [project]
    # ...
    dynamic = ["version"]
    
    [tool.autocalver]
    use = true
    log_command = "git log -n 1 --date=iso > git-log-head"
    log = "git-log-head"
    is_main_var = "<env var with branch name>"
    is_main_match = "^main$"


The first part,
the
``build-system``,
adds
``autocalver``
to the dependencies.
The second part declares
``version``
as dynamic,
so it is not specified directly
in
``pyproject.toml``.

Finally,
the configuration for
``autocalver``:

* `use`: Enable autocalver. Change to `false` to disable.
* `log_command`: Command to generate a log if the log file does not exist.
* `log`: File containing the log of the latest commit.
* `is_main_var`: Sentinel environment variable to detect build environment.
* `is_main_match`: Regular expression that indicates this is a build of the main branch.

Version value
-------------

The "root" of the version is based on the latest commit.
It takes the commit date,
in UTC,
and manufactures the version
as follows:
``<Year>.<Month>.<Day>.<Seconds>``.
The
``seconds``
are counted since the beginning of the day.

The verion is modified as follows:

* If the sentinel environment variable is missing or empty,
  it generates a
  ``dev1``
  build.
  It is assumed to be a build that is done locally.
* If the sentinel environment variable exists and non-empty,
  but does not match a regular expression,
  it generates an
  ``rc1``
  build.
  It is assumed to be running from CI on a development branch.
* If the sentinel environment variable matches a regular expression,
  the
  "root"
  version is the one that is built.
