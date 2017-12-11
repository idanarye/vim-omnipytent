import vim

from itertools import chain
from contextlib import contextmanager

from .util import vim_repr, vim_eval

if vim.eval('has("win32")'):
    from subprocess import list2cmdline

    def quote(s):
        return list2cmdline([s])
else:
    try:
        from shlex import quote
    except ImportError:
        from pipes import quote


def __singleton(cls):
    return cls()


class VimCommand(object):
    _quoter = str

    def __init__(self, command):
        self._command = command

    def __call__(self, *args):
        vim.command(' '.join(chain([self._command], map(self._quoter, args))))

    @property
    def bang(self):
        return self.__class__('%s!' % self._command)


@__singleton
class CMD(object):
    def __getattr__(self, command):
        return VimCommand(command)

    def __getitem__(self, command):
        return VimCommand(command)


class VimFunction(object):
    def __init__(self, function):
        self._function = function

    def __call__(self, *args):
        func_expr = '%s(%s)' % (self._function, ', '.join(map(vim_repr, args)))
        return vim_eval(func_expr)


@__singleton
class FN(object):
    def __getattr__(self, function):
        return VimFunction(function)

    def __getitem__(self, function):
        return VimFunction(function)



@__singleton
class VAR(object):
    def __contains__(self, varname):
        return bool(int(vim.eval('exists(%s)' % vim_repr(varname))))

    def __getitem__(self, varname):
        try:
            return vim_eval(varname)
        except Exception as e:
            if varname not in self:
                raise KeyError('No Vim variable %r - %s' % (varname, e))
            raise

    def __setitem__(self, varname, value):
        let_expr = 'let %s = %s' % (varname, vim_repr(value))
        vim.command(let_expr)
        return value

    def __delitem__(self, varname):
        del_expr = 'unlet %s' % (varname)
        vim.command(del_expr)

    @contextmanager
    def changed(self, **kwargs):
        old = {}
        nonexistent = []

        for k, v in kwargs.items():
            try:
                old[k] = self[k]
            except KeyError:
                nonexistent.append(k)

        try:
            for k, v in kwargs.items():
                self[k] = v
            yield
        finally:
            for k, v in old.items():
                self[k] = v
            for k in nonexistent:
                del self[k]




@__singleton
class OPT(object):
    def __init__(self, prefix=None):
        if prefix:
            self.__dict__['_prefix'] = prefix
        else:
            self.__dict__['_prefix'] = '&'
            self.__dict__['l'] = type(self)(prefix='&l:')
            self.__dict__['g'] = type(self)(prefix='&g:')

    def __getattr__(self, optname):
        return vim_eval(self._prefix + optname)

    __getitem__ = __getattr__

    def __setattr__(self, optname, value):
        let_expr = 'let %s%s = %s' % (self._prefix, optname, vim_repr(value))
        vim.command(let_expr)
        return value

    __setitem__ = __setattr__

    @contextmanager
    def changed(self, **kwargs):
        if self._prefix == '&':
            with self.l.changed(**kwargs), self.g.changed(**kwargs):
                yield
            return
        old = dict((k, self[k]) for k in kwargs.keys())

        try:
            for k, v in kwargs.items():
                self[k] = v
            yield
        finally:
            for k, v in old.items():
                self[k] = v




class ShellCommandExecuter(object):
    class Raw(str):
        pass

    def __init__(self, func):
        self.send_raw = func
        self.parameters = {}

    def __lshift__(self, raw_text):
        return self.send_raw(raw_text)

    def _quote(self, arg):
        if isinstance(arg, self.Raw):
            return str(arg)
        else:
            return quote(str(arg))

    def _with_parameters(self, **parameters):
        result = type(self)(self.send_raw)
        result.parameters.update(self.parameters)
        result.parameters.update(parameters)
        return result

    def __call__(self, *args, **parameters):
        if parameters and not args:
            return self._with_parameters(**parameters)
        for k, v in self.parameters.items():
            if k not in parameters:
                parameters[k] = v
        return self.send_raw(' '.join(self._quote(arg) for arg in args), **parameters)


@ShellCommandExecuter
def BANG(command):
    vim.command('!%s' % command)
    return int(vim.eval('v:shell_error'))


@ShellCommandExecuter
def SH(command):
    vim.command('!%s' % command)
    shell_error = int(vim.eval('v:shell_error'))
    if shell_error:
        raise Exception('Shell error %s while executing `%s`' % (shell_error, command))


from .terminal import Terminal
if hasattr(Terminal, 'start'):
    @ShellCommandExecuter
    def TERMINAL_TAB(command):
        vim.command('tabnew')
        return Terminal.start(command)

    class TERMINAL_PANEL(ShellCommandExecuter):
        def size(self, size):
            return self(size=size)

    @TERMINAL_PANEL
    def TERMINAL_PANEL(command, size=5):
        vim.command('redraw')  # Release 'Press ENTER or type command to continue'
        old_win_view = vim.eval('winsaveview()')
        vim.command('botright new')
        vim.command('call winrestview(%s)' % (old_win_view,))
        vim.command('resize %s' % (size,))
        return Terminal.start(command)
