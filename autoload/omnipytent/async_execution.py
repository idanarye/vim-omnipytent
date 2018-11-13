from itertools import count
import vim
import sys
import importlib

try:
    from abc import ABC
except ImportError:
    from abc import ABCMeta
    class ABC(object):
        __metaclass__ = ABCMeta

from abc import abstractmethod

from .execution import FN, VAR
from .util import vim_repr, RawVim, input_list

_IDX_COUNTER = count(1)


class AbortAsyncCommand(Exception):
    pass


class AsyncExecutor(object):
    def __init__(self, invocation_generator):
        self.invocation_generator = invocation_generator
        self.yielded_command = None

    def run_next(self):
        while True:
            try:
                self.yielded_command = next(self.invocation_generator)
            except StopIteration:
                pass
            else:
                self.yielded_command._register(self)
                try:
                    self.yielded_command._running_from_async_executor = True
                    self.yielded_command.on_yield()
                    self.yielded_command._running_from_async_executor = False
                except AbortAsyncCommand:
                    self.yielded_command._unregister()
                    continue
            break


class AsyncCommand(ABC):
    yielded = {}

    @property
    def vim_obj(self):
        return RawVim.fmt('omnipytent#_yieldedCommand(%s,%s)', sys.version_info[0], self.idx)

    def _register(self, executor):
        self.executor = executor
        self.idx = next(_IDX_COUNTER)
        self.yielded[self.idx] = self
        self._returned_value = None

    def _unregister(self):
        del self.yielded[self.idx]

    def call(self, method, args):
        return getattr(self, method)(*args)

    def resume(self, returned_value=None):
        self._returned_value = returned_value
        if self._running_from_async_executor:
            raise AbortAsyncCommand
        else:
            self._unregister()
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
    def __init__(self,
                 text=None,
                 filetype=None,
                 init=None):
        if isinstance(text, str):
            text = text.splitlines()
        self.text = text
        self.filetype = filetype
        self.init = init

    def on_yield(self):
        vim.command('belowright 10new')
        self.buffer = vim.current.buffer
        self.buffer[:] = self.text
        vim.command('set buftype=nofile')
        if self.filetype:
            VAR['&filetype'] = self.filetype
        if not self.init:
            pass
        elif callable(self.init):
            self.init()
        elif isinstance(self.init, str):
            vim.command(self.init)
        else:
            raise TypeError('Expected `init` to be callable or string - not %s' % (type(self.init)),)
        vim.command('autocmd omnipytent BufDelete <buffer> call %s.call("save_buffer_content")' % self.vim_obj)

    def save_buffer_content(self):
        self.content = self.buffer[:]
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.resume(self.content)


class SelectionUI(AsyncCommand):
    def __init__(self, source, multi=False, prompt=None, fmt=str, preview=None):
        self.source = list(source)
        self.multi = multi
        self.prompt = prompt
        self.fmt = fmt
        self.preview = preview

    @abstractmethod
    def gen_entry(self, i, item):
        pass

    def get_source(self):
        return [self.gen_entry(i, item) for i, item in enumerate(self.source)]

    def finish_indices(self, indices):
        if self.multi:
            self.resume([self.source[i] for i in indices])
        else:
            # TODO: make this an error if there are more than one
            index, = indices
            self.resume(self.source[index])

    def _bytes_for_preview(self, index):
        try:
            index = int(index)
            item = self.source[index]
            preview = self.preview(item)
            if not isinstance(preview, bytes):
                preview = str(preview).encode('utf8')
            return preview
        except Exception as e:
            return ("Got exception:\n%s" % (e,)).encode('utf8')


class InputListSelectionUI(SelectionUI):
    def gen_entry(self, i, item):
        pass

    def on_yield(self):
        self.resume(input_list(self.prompt or 'Choose:', self.source, self.fmt))


def __selection_ui():
    if '1' == vim.eval('exists("*fzf#run")'):
        return 'fzf'
    elif '2' == vim.eval('exists(":Denite")'):
        return 'denite'
    elif '2' == vim.eval('exists(":Unite")'):
        return 'unite'
    elif '2' == vim.eval('exists(":CtrlP")'):
        return 'ctrlp'
    else:
        return 'inputlist'


def __selection_ui_cls(selection_ui):
    if selection_ui == 'fzf':
        from omnipytent.integration.fzf import FZF
        return FZF
    elif selection_ui == 'denite':
        from omnipytent.integration.denite import DENITE
        return DENITE
    elif selection_ui == 'unite':
        from omnipytent.integration.unite import UNITE
        return UNITE
    elif selection_ui == 'ctrlp':
        from omnipytent.integration.ctrlp import CTRLP
        return CTRLP
    elif selection_ui == 'inputlist':
        return InputListSelectionUI
    else:
        module_name, class_name = selection_ui.rsplit('.', 1)
        return getattr(importlib.import_module(module_name), class_name)


def CHOOSE(source, multi=False, prompt=None, fmt=str, preview=None):
    selection_ui = vim.vars.get('omnipytent_selectionUI') or __selection_ui()
    selection_ui_cls = __selection_ui_cls(selection_ui)

    return selection_ui_cls(source=source, multi=multi, prompt=prompt, fmt=fmt, preview=preview)

