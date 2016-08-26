from __future__ import absolute_import

from plumbum import local

from omnipytent.execution import ShellCommandExecuter


def __rand__(self, cmd):
    return self(*map(ShellCommandExecuter.Raw, cmd.formulate(1)))
ShellCommandExecuter.__rand__ = __rand__

