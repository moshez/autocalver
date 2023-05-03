# autocalver

.. image:: https://badge.fury.io/py/autocalver.svg
    :target: https://badge.fury.io/py/autocalver

.. image:: https://badge.fury.io/gh/moshez%2Fautocalver.svg
    :target: https://badge.fury.io/gh/moshez%2Fautocalver


Tired of
"bumping versions"?
Sick of commits,
pull requests,
tags,
and a lot of manual work just to release
the code that is already in the main branch?

The
`autocalver`
package is here to automatically generate
"calendar versions",
and chew gum,
and it's all out of gum.

It automatically produces a calver based on a commit log.
The version depends on the
time of the *commit*,
not the time of the build.
The version format is
`<year>.<month>.<day>.<seconds from beginning of day>`.
The time is always converted to UTC first.

## Configuration

The right way to make sure
`autocalver`
is installed is to require it in
`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "autocalver"]
```

Note that
`autocalver`
will
*not*
run any version-control commands.
Before using
`autocalver`,
run a command to pull a prefix of the commit log,
and save it to a file.
For example,
with
`git`,
you can use

```shell
git log -n 1 --date=iso > git-log-head
```

One advantage of separating the stages like that is that it is possible
to have the package builder itself running in an environent that does not
have access to the version control metadata,
only the source files and the prefix of the commit log.
Failing to produce the log will cause the package build to fail.

The tool overrides the version in the
`setup.cfg`.
Configuration is done via
`pyproject.toml`.
For example,
a configuration appropriate to
pipeline CI might be:

```toml
[tool.autocalver]
use = true
log = "git-log-head"
is_main_var = "BUILD_BRANCH_REF"
is_main_match = ".*/main$"
```

Note that if you use the
`[project]`
entry in
`pyproject.toml`,
it must:

* Not have
  `version`
* Explicitly declare
  `dynamic = ["version"]`

## Building packages

Based on the given environment variable
and its value
the version is produced as development,
rc,
or a full-release.
This allows checking against a release-system's
environment variables for the branch,
pull request,
or workflow name.

With this configuration,
the following versions will be produced
(asssuming the time of the latest commit is
October 10, 2021, 8:39:44 in Pacific time).

Local build:

```console
$ python -m build -n --wheel 2>& 1| tail -1
Successfully built fake_package-2021.10.10.56384.dev1-py3-none-any.whl
```

Note that the version has a
`dev1`
in its name.


Simulate tagged build:

```console
$ GITHUB_REF=refs/tags/test-fix-PROJ-121 python -m build -n --wheel 2>& 1| tail -1
Successfully built fake_package-2021.10.10.56384rc1-py3-none-any.whl
```

This version has an
`rc1`
in the name,
marking it as a pre-release.
This allows pushing tags to produce packages
and test fixes.
However,
since tag pushes are not reviewed,
these do not produce releases.

Simulate merge to main:

```console
$ GITHUB_REF=refs/heads/main python -m build -n --wheel 2>& 1| tail -1
Successfully built fake_package-2021.10.10.56384-py3-none-any.whl
```

Note that without
`use = true`,
the tool will not replace the version.
If
`use = true`
is there,
missing any of the other variables
will cause an
*error*
during the build,
as a non-existing build
is better than a broken when.
