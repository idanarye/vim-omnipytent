import vim
import os

from omnipytent.async_execution import FuzzyChooser
from omnipytent.execution import FN

class CTRLP(FuzzyChooser):
    def on_yield(self):
        FN['ctrlp#omnipytent#start'](self.vim_obj)
        # FN['ctrlp#init'](FN['ctrlp#omnipytent#id']())
        # FN['unite#start'](['omnipytent'], dict(
            # omnipytent__yieldedCommand=self.vim_obj,
            # buffer_name=self.prompt or '',
        # ))

    # def __gen_source(self):
        # for item in self.source:
            # yield dict(
                # word=item,
                # kind='omnipytent',
            # )

    def get_source(self):
        return self.source

    # def set_result(self, result):
        # self.result = result

    def finish(self, choice):
        self.resume(choice)
        # self.run_next_frame('resume_execution')

    # def resume_execution(self):
        # self.resume(getattr(self, 'result', []))
