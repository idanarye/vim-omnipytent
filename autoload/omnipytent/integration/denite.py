import vim

from omnipytent.async_execution import FuzzyChooser
from omnipytent.execution import FN

class DENITE(FuzzyChooser):
    def on_yield(self):
        FN['denite#start']([dict(
            name='omnipytent',
            args=[],
        )], dict(
            yielded_command=str(self.vim_obj),
        ))

    def get_source(self):
        return [dict(word=item, idx=i) for i, item in enumerate(self.source)]

    def finish(self, choice):
        self.run_next_frame('resume_execution', choice)

    def resume_execution(self, choice):
        if self.multi:
            self.resume([self.source[i] for i in choice])
        else:
            # TODO: make this an error if there are more than one
            index, = choice
            self.resume(self.source[index])
