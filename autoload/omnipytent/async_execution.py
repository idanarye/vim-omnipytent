from itertools import count
import vim
import sys

try:
    from abc import ABC
except ImportError:
    from abc import ABCMeta
    class ABC(object):
        __metaclass__ = ABCMeta

from abc import abstractmethod

_IDX_COUNTER = count(1)


class AsyncExecutor(object):
    _pending = {}

    def __init__(self, invocation_generator):
        self.idx = next(_IDX_COUNTER)
        self.invocation_generator = invocation_generator
        self.yielded_command = None

    @property
    def ident(self):
        return '%s:%s' % (sys.version_info[0], self.idx)

    @property
    def resume_vim_function_call(self):
        return 'omnipytent#resume(%r)' % self.ident

    @classmethod
    def get_pending(cls, idx):
        return cls._pending.pop(idx)

    def run_next(self):
        if self.yielded_command is not None:
            self.yielded_command.returned_value = self.yielded_command.on_resume()
            self.yielded_command = None
        try:
            self.yielded_command = next(self.invocation_generator)
        except StopIteration:
            pass
        else:
            self._pending[self.idx] = self
            self.yielded_command.on_yield(self)


class AsyncCommand(ABC):
    @abstractmethod
    def on_yield(self, executor):
        pass

    @abstractmethod
    def on_resume(self):
        pass


class INPUT_BUFFER(AsyncCommand):
    def on_yield(self, executor):
        vim.command('new')
        self.buffer = vim.current.buffer
        vim.command('set buftype=nofile')
        vim.command('autocmd BufDelete <buffer> call ' + executor.resume_vim_function_call)

    def on_resume(self):
        return self.buffer[:]
