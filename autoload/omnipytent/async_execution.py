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

from .util import vim_repr, RawVim

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
        return RawVim.fmt('omnipytent#_yieldedCommand(%s,%s)', sys.version_info[0], self.idx)

    def register(self, executor):
        self.executor = executor
        self.idx = next(_IDX_COUNTER)
        self.yielded[self.idx] = self
        self.returned_value = None

    def call(self, method, args):
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
    def __init__(self, text=None):
        if isinstance(text, str):
            text = text.splitlines()
        self.text = text

    def on_yield(self):
        vim.command('new')
        self.buffer = vim.current.buffer
        self.buffer[:] = self.text
        vim.command('set buftype=nofile')
        vim.command('autocmd omnipytent BufDelete <buffer> call %s.call("save_buffer_content")' % self.vim_obj)

    def save_buffer_content(self):
        self.content = self.buffer[:]
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.resume(self.content)


class FuzzyChooser(AsyncCommand):
    def __init__(self, source, multi=False, prompt=None):
        self.source = list(source)
        self.multi = multi
        self.prompt = prompt


def CHOOSE(source, multi=False, prompt=None):
    from omnipytent.integration.fzf import FZF
    from omnipytent.integration.denite import DENITE
    from omnipytent.integration.unite import UNITE
    from omnipytent.integration.ctrlp import CTRLP
    return FZF(source=source, multi=multi, prompt=prompt)
