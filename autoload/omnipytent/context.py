import vim

import re
import os.path


class InvocationContext(object):
    def __init__(self, task_file, main_task):
        self.dep_data = {}
        self.task_file = task_file
        self.main_task = main_task
        self.start_dir = vim.eval('getcwd()')
        self.start_window = vim.current.window
        self.start_buffer = vim.current.buffer

    def for_task(self, task):
        return task.TaskContext(self, task)


class TaskContext(object):
    def __init__(self, parent, task):
        self._parent = parent
        self.task = task
        self.dep = DepDataFetcher(self)

    def __repr__(self):
        return '<TaskContext: %s>' % self.task.name

    @property
    def task_file(self):
        return self._parent.task_file

    @property
    def has_passed_data(self):
        return self.task in self._parent.dep_data

    @property
    def passed_data(self):
        return self._parent.dep_data[self.task]

    def pass_data(self, data):
        self._parent.dep_data[self.task] = data

    @property
    def cache(self):
        return self.task_file.get_task_cache(self.task)

    @property
    def is_main(self):
        return self._parent.main_task == self.task

    @property
    def task_dir(self):
        return self.task_file.tasks_dir

    proj_dir = task_dir

    @property
    def file_dir(self):
        filename = self._parent.start_buffer.name
        if filename:
            return os.path.dirname(filename)
        else:
            return self.cur_dir

    @property
    def cur_dir(self):
        return self._parent.start_dir


class DepDataFetcher:
    def __init__(self, task_context):
        self.__task_context = task_context

    def __getattr__(self, name):
        for dependency in self.__task_context.task.dependencies:
            if dependency.name == name:
                try:
                    return self.__task_context._parent.dep_data[dependency]
                except KeyError:
                    raise AttributeError('%s did not pass data' % dependency)
        raise AttributeError('%s has no dependency named "%s"' % (self.__task_context.task, name))

    def _get_by_task(self, task):
        return self.__task_context._parent.dep_data[task]

    def _get_indirect(self, name):
        for task, value in self.__task_context._parent.dep_data.items():
            if task.name == name:
                return value
        raise KeyError('task %r did not pass data' % (name,))


class CompletionContext:
    @classmethod
    def from_vim_completion_args(cls, tasks_file, arg_lead, cmd_line, cursor_pos):
        cmd_line_before_cursor = cmd_line[:cursor_pos]
        parts = re.findall(r'(?:[^\\\s]|(?:\\\\)|(?:\\\s))+', cmd_line_before_cursor)
        if cmd_line_before_cursor.endswith(' '):
            parts.append('')

        assert 2 <= len(parts)
        if len(parts) == 2:  # task name completion
            return cls(tasks_file=tasks_file,
                       task=None,
                       arg_index=None,
                       arg_prefix=parts[1],
                       prev_args=[],
                       cmd_line=cmd_line,
                       cursor_pos=cursor_pos)
        else:
            return cls(tasks_file=tasks_file,
                       task=tasks_file[parts[1]],
                       arg_index=len(parts) - 3,
                       arg_prefix=parts[-1],
                       prev_args=parts[2:-1],
                       cmd_line=cmd_line,
                       cursor_pos=cursor_pos)

    def __init__(self, tasks_file, task, arg_index, arg_prefix, prev_args, cmd_line, cursor_pos):
        self.tasks_file = tasks_file
        self.task = task
        self.arg_index = arg_index
        self.arg_prefix = arg_prefix
        self.prev_args = prev_args
        self.cmd_line = cmd_line
        self.cursor_pos = cursor_pos

    @property
    def arg_name(self):
        if self.arg_index is None:
            return None
        else:
            assert 0 <= self.arg_index
            try:
                return self.task._task_args[self.arg_index]
            except IndexError:
                return self.task._task_varargs  # may be None - but that just means the argument is None

