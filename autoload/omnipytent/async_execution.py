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

from .util import vim_repr

_IDX_COUNTER = count(1)


class AsyncExecutor(object):
    def __init__(self, invocation_generator):
        self.invocation_generator = invocation_generator
        self.yielded_command = None

    def run_next(self):
        try:
            self.yielded_command = next(self.invocation_generator)
        except StopIteration:
            pass
        else:
            self.yielded_command.register(self)
            self.yielded_command.on_yield()


class AsyncCommand(ABC):
    yielded = {}

    @property
    def vim_obj(self):
        return 'omnipytent#_yieldedCommand(%s,%s)' % (sys.version_info[0], self.idx)

    def register(self, executor):
        self.executor = executor
        self.idx = next(_IDX_COUNTER)
        self.yielded[self.idx] = self
        self.returned_value = None

    def notify(self, method, args):
        return getattr(self, method)(*args)

    def resume(self, returned_value=None):
        del self.yielded[self.idx]
        self.returned_value = returned_value
        self.executor.run_next()

    def run_next_frame(self, method, *args):
        vim.command('call omnipytent#_addNextFrameCommand(%s, %s, %s)' % (
            self.vim_obj,
            vim_repr(method),
            vim_repr(args)))

    @abstractmethod
    def on_yield(self):
        pass


class INPUT_BUFFER(AsyncCommand):
    def on_yield(self):
        vim.command('new')
        self.buffer = vim.current.buffer
        vim.command('set buftype=nofile')
        vim.command('autocmd omnipytent BufDelete <buffer> call %s.notify("save_buffer_content")' % self.vim_obj)

    def save_buffer_content(self):
        self.content = self.buffer[:]
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.resume(self.content)
