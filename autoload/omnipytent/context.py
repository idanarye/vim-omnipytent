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
            task = tasks_file[parts[1]]
            invocation_context = InvocationContext(tasks_file, task)
            return cls(tasks_file=tasks_file,
                       task=task(invocation_context),
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

