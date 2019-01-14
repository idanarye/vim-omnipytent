__all__ = [
    'task',
    'CMD',
    'FN',
    'VAR',
    'OPT',
    'BANG',
    'SH',
    'INPUT_BUFFER',
    'CHOOSE',
    'CombineSources',
    'CombineSourcesMulti',
]

from .dsl import task
from .execution import CMD, FN, VAR, OPT, BANG, SH
from .async_execution import INPUT_BUFFER, CHOOSE
from .task_makers import CombineSources, CombineSourcesMulti

from . import _extending as __extending

try:
    from .execution import TERMINAL_TAB, TERMINAL_PANEL
    __all__.extend(['TERMINAL_TAB', 'TERMINAL_PANEL'])
except ImportError:
    pass

