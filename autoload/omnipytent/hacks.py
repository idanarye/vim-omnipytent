
import bdb
from collections import OrderedDict


class _FunctionContextReader(bdb.Bdb):
    def user_return(self, frame, value):
        self.last_frame = frame


def function_locals(func, *args, **kwargs):
    function_context_reader = _FunctionContextReader()
    function_context_reader.runcall(func, *args, **kwargs)
    frame = function_context_reader.last_frame
    func_locals = OrderedDict()
    for identifier in frame.f_code.co_varnames:
        if identifier in frame.f_locals:
            func_locals[identifier] = frame.f_locals[identifier]
    return func_locals

