from itertools import count
import vim
import sys
import importlib
import re
import inspect

try:
    from abc import ABC
except ImportError:
    from abc import ABCMeta
    class ABC(object):
        __metaclass__ = ABCMeta

from abc import abstractmethod

from .execution import FN, VAR
from .util import vim_repr, RawVim, input_list, poor_mans_async

_IDX_COUNTER = count(1)


class AbortAsyncCommand(Exception):
    pass


class AsyncExecutor(object):
    def __init__(self, invocation_generator):
        self.invocation_generator = invocation_generator
        self.yielded_command = None

    @classmethod
    def spawn(cls, generator):
        if inspect.isgenerator(generator):
            cls(poor_mans_async(generator)).run_next()
        elif inspect.isgeneratorfunction(generator):
            cls(poor_mans_async(generator())).run_next()

    def run_next(self):
        while True:
            try:
                self.yielded_command = next(self.invocation_generator)
            except StopIteration:
                pass
            else:
                self.yielded_command.executor = self
                self.yielded_command._register()
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
    idx = None
    _returned_value = None

    @property
    def vim_obj(self):
        return RawVim.fmt('omnipytent#_yieldedCommand(%s,%s)', sys.version_info[0], self.idx)

    def _register(self):
        if self.idx is None:
            self.idx = next(_IDX_COUNTER)
            self.yielded[self.idx] = self

    def _unregister(self):
        del self.yielded[self.idx]
        self.idx = None

    def call(self, method, args):
        return getattr(self, method)(*args)

    def _resolve_returned_value(self, returned_value):
        """Override if the returned value is not something you can easily pass through Vimscript"""
        return returned_value

    def resume(self, returned_value=None):
        self._returned_value = self._resolve_returned_value(returned_value)
        if self._running_from_async_executor:
            raise AbortAsyncCommand
        else:
            vim.command('call %s._resumeExecutionInProperContex()' % (self.vim_obj,))
            self.vim_obj

    def run_next_frame(self, method, *args):
        vim.command('call omnipytent#_addNextFrameCommand(%s, %s, %s)' % (
            self.vim_obj,
            vim_repr(method),
            vim_repr(args)))

    @abstractmethod
    def on_yield(self):
        pass


class INPUT_BUFFER(AsyncCommand):
    def __init__(
        self,
        text=None,
        filetype=None,
        init=None,
        complete=None,
        complete_findstart=r'\w+',
    ):
        if isinstance(text, str):
            text = text.splitlines()
        self._text = text
        self._filetype = filetype
        self._init = init
        self._complete = complete
        self._buffer_commands = {}

        if isinstance(complete_findstart, str):
            complete_findstart = re.compile(complete_findstart)
        if isinstance(complete_findstart, re.Pattern):
            def complete_findstart(prefix, pattern=complete_findstart):
                for m in pattern.finditer(prefix):
                    if m.end() == len(prefix):
                        return m.start()
        if callable(complete_findstart):
            def complete_findstart(orig=complete_findstart):
                cursor_col = vim.current.window.cursor[1]
                prefix = vim.current.line[:cursor_col]
                start = orig(prefix)
                if isinstance(start, int):
                    return start
                else:
                    return -3

        self.complete_findstart = complete_findstart

    def on_yield(self):
        vim.command('belowright 10new')
        self.buffer = vim.current.buffer
        self.buffer[:] = self._text
        vim.command('set buftype=nofile')
        if self._filetype:
            VAR['&filetype'] = self._filetype
        if not self._init:
            pass
        elif callable(self._init):
            self._init()
        elif isinstance(self._init, str):
            vim.command(self._init)
        else:
            raise TypeError('Expected `init` to be callable or string - not %s' % (type(self._init)),)
        vim.command('autocmd omnipytent BufDelete <buffer> call %s.call("save_buffer_content")' % self.vim_obj)

        if self._complete:
            vim.command(
                """
                function b:.omnipytent_completeFunction(findstart, base) abort
                    return %s.call("_complete_function_vim_api", a:findstart, a:base)
                endfunction
                """ % self.vim_obj)
            vim.command('setlocal completefunc=omnipytent#_callBufferCompleteFunction')
            #  vim.command('autocmd omnipytent BufDelete <buffer> call %s.call("save_buffer_content")' % self.vim_obj)

        for command_name in self._buffer_commands.keys():
            vim.command('command -buffer %s call %s.call("run_buffer_command", %r)' % (
                command_name,
                self.vim_obj,
                command_name,
            ))

    def _complete_function_vim_api(self, findstart, base):
        if findstart:
            return self.complete_findstart()
        else:
            result = self._complete(base)
            if result is None:
                return None
            elif isinstance(result, str):
                return [result]
            else:
                return list(result)

    def save_buffer_content(self):
        self.content = self.buffer[:]
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.resume(self.content)

    def buffer_command(self, function):
        self._buffer_commands[function.__name__] = function

    def run_buffer_command(self, command_name):
        result = self._buffer_commands[command_name]()
        AsyncExecutor.spawn(result)


class SelectionUI(AsyncCommand):
    def __init__(self, source, multi=False, prompt=None, fmt=str, preview=None, score=None):
        self.source = list(source)
        if score:
            self.source.sort(key=score, reverse=True)
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
        choice = input_list(self.prompt or 'Choose:', self.source, self.fmt)
        if self.multi:
            choice = [choice]
        self.resume(choice)


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


def CHOOSE(source, multi=False, prompt=None, fmt=str, preview=None, score=None):
    try:
        selection_ui = VAR['g:omnipytent_selectionUI']
    except KeyError:
        selection_ui = __selection_ui()
    selection_ui_cls = __selection_ui_cls(selection_ui)

    return selection_ui_cls(source=source, multi=multi, prompt=prompt, fmt=fmt, preview=preview, score=score)


class WAIT_FOR_AUTOCMD(AsyncCommand):
    def __init__(self, autocmd, before_resume=lambda: None):
        self.autocmd = autocmd
        self.before_resume = before_resume

    def on_yield(self):
        vim.command('autocmd omnipytent %s ++once call %s.call("proceed")' % (
            self.autocmd, self.vim_obj))

    def proceed(self):
        self.resume(self.before_resume())
