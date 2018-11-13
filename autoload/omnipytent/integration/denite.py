import vim

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN

class DENITE(SelectionUI):
    def on_yield(self):
        FN['denite#start']([dict(
            name='omnipytent-choice',
            args=[],
        )], dict(
            yielded_command=str(self.vim_obj),
        ))

    def gen_entry(self, i, item):
        return dict(idx=i,
                    word=self.fmt(item))

    def finish(self, choice):
        self.run_next_frame('finish_indices', choice)
