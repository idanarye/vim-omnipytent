import vim

import sys
import os
import os.path
import glob
import imp
from contextlib import contextmanager

from .tasks import Task
from .context import CompletionContext


class TasksFile:
    def __init__(self):
        self.filename = self.find_tasks_file(self.default_name())
        self.last_modified = None
        self._tasks_cache = {}

    @staticmethod
    def find_tasks_file(filename):
        def search_upward(delegate):
            check_dir = os.path.abspath(vim.eval('getcwd()'))
            while True:
                result = delegate(check_dir)
                if result:
                    return result

                parent_dir = os.path.abspath(os.path.join(check_dir, os.pardir))
                if len(check_dir) <= len(parent_dir):
                    break
                check_dir = parent_dir

        @search_upward
        def tasks_file_path(check_dir):
            tasks_file_path = os.path.abspath(os.path.join(check_dir, filename))
            if os.path.isfile(tasks_file_path):
                return tasks_file_path

        if tasks_file_path:
            return tasks_file_path

        try:
            project_root_markers = vim.eval('g:omnipytent_projectRootMarkers')
        except Exception as e:
            pass
        else:
            if not isinstance(project_root_markers, list):
                raise Exception('g:omnipytent_projectRootMarkers is not a list')

            @search_upward
            def project_root_path(check_dir):
                for pattern in project_root_markers:
                    for found in glob.iglob(os.path.join(check_dir, pattern)):
                        return os.path.join(check_dir, filename)

            if project_root_path:
                return project_root_path

        return os.path.abspath(os.path.join(vim.eval('getcwd()'), filename))

    def open(self, on_task=None):
        vim.command('edit %s' % self.filename)
        if not os.path.exists(self.filename):
            vim.current.buffer[:] = ['import vim',
                                     'from omnipytent import *']
            if on_task:
                self._create_task_in_current_buffer(on_task)
            else:
                vim.command(str(len(vim.current.buffer)))
        else:
            if on_task:
                if self.is_stale:
                    self.load()
                try:
                    task = self.tasks[on_task]
                    line = task.func.__code__.co_firstlineno
                    vim.command('edit %s' % self.filename)
                    vim.command(str(line))
                except KeyError:
                    self._create_task_in_current_buffer(on_task)

    def _create_task_in_current_buffer(self, taskname):
        last_line = len(vim.current.buffer) - 1
        while 0 < last_line and not vim.current.buffer[last_line].strip():
            last_line -= 1

        lines_to_put_at_end_of_file = ['',
                                       '',
                                       '@task',
                                       'def %s(ctx):' % taskname,
                                       '    ']

        if last_line + 1 == len(vim.current.buffer):
            vim.current.buffer.append(lines_to_put_at_end_of_file)
        else:
            vim.current.buffer[last_line + 1:] = lines_to_put_at_end_of_file

        vim.command(str(len(vim.current.buffer)))
        vim.command('startinsert!')

    def load(self):
        # Clear old stuff(old tasks) from the module
        try:
            self.module.__dict__.clear()
        except AttributeError:
            pass

        self.tasks = {}
        old_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            self.module = imp.load_source('_omnypytent_tasksfile', self.filename)
        finally:
            sys.dont_write_bytecode = old_dont_write_bytecode
        try:
            module_iteritems = self.module.__dict__.iteritems()
        except AttributeError:
            module_iteritems = self.module.__dict__.items()
        for ident, value in module_iteritems:
            if isinstance(value, Task):
                for name, subtask in value.gen_self_with_subtasks(ident):
                    self.tasks[name] = subtask
                    for alias in subtask.aliases:
                        self.tasks[alias] = subtask
        self.last_modified = os.path.getmtime(self.filename)
        self._tasks_cache = self._tasks_cache
        for key in list(self._tasks_cache.keys()):
            if key not in self.tasks:
                del self._tasks_cache[key]

    def __getitem__(self, key):
        return self.tasks[key]

    def get_task_cache(self, task):
        if self[task.name] is not task:
            raise TypeError("%r cannot use the cache - not the %r in the tasks file" % (task, task.name))
        try:
            return self._tasks_cache[task.name]
        except KeyError:
            return self._tasks_cache.setdefault(task.name, _TaskCache())

    @staticmethod
    def default_name():
        try:
            return '%s.omnipytent.%s.py' % (vim.eval('g:omnipytent_filePrefix'), sys.version_info.major)
        except Exception:
            raise Exception('g:omnipytent_filePrefix not set')

    @property
    def is_stale(self):
        try:
            return self.last_modified != os.path.getmtime(self.filename)
        except OSError:
            return True

    def load_if_stale(self):
        if self.is_stale:
            self.load()

    def completion_context(self, arg_lead, cmd_line, cursor_pos):
        return CompletionContext.from_vim_completion_args(tasks_file=self,
                                                          arg_lead=arg_lead,
                                                          cmd_line=cmd_line,
                                                          cursor_pos=cursor_pos)

    @property
    def tasks_dir(self):
        return os.path.dirname(self.filename)

    @contextmanager
    def in_tasks_dir_context(self):
        origdir_python = os.getcwd()
        origdir_vim = vim.eval('getcwd()')
        tasks_dir = self.tasks_dir

        if tasks_dir != origdir_vim:
            vim.command('cd ' + tasks_dir)

        if tasks_dir != origdir_python:
            os.chdir(tasks_dir)

        yield

        if tasks_dir != origdir_vim and vim.eval('getcwd()') == tasks_dir:
            vim.command('cd ' + origdir_vim)

        if tasks_dir != origdir_python and os.getcwd() == tasks_dir:
            os.chdir(origdir_python)


__last_tasks_file = [None]


def get_tasks_file():
    if __last_tasks_file[0] is None:
        __last_tasks_file[0] = TasksFile()
    elif __last_tasks_file[0].filename != TasksFile.find_tasks_file(TasksFile.default_name()):
        __last_tasks_file[0] = TasksFile()
    return __last_tasks_file[0]


class _TaskCache:
    pass
