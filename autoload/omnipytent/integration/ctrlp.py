import vim
import os

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN

class CTRLP(SelectionUI):
    def on_yield(self):
        FN['ctrlp#omnipytent#start'](self.vim_obj)

    def gen_entry(self, i, item):
        return item

    def finish(self, choice):
        self.resume(choice)
