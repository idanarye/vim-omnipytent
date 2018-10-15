import vim

from omnipytent.async_execution import FuzzyChooser
from omnipytent.execution import FN

class UNITE(FuzzyChooser):
    def on_yield(self):
        FN['unite#start'](['omnipytent'], dict(
            omnipytent__yieldedCommand=self.vim_obj,
            buffer_name=self.prompt or '',
        ))

    def __gen_source(self):
        for item in self.source:
            yield dict(
                word=item,
                kind='omnipytent',
            )

    def get_source(self):
        return list(self.__gen_source())

    def set_result(self, result):
        self.result = result

    def finish(self):
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.resume(getattr(self, 'result', []))
