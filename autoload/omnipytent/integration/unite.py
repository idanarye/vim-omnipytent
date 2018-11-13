import vim

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN

class UNITE(SelectionUI):
    def on_yield(self):
        FN['unite#start'](['omnipytent_choice'], dict(
            omnipytent__yieldedCommand=self.vim_obj,
            buffer_name=self.prompt or '',
        ))

    def gen_entry(self, i, item):
        return dict(idx=i,
                    word=self.fmt(item),
                    kind='omnipytent_choice')

    def set_result(self, result):
        self.result = result

    def finish(self):
        # NOTE: we will only get the proper self.result in the next frame
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.finish_indices(getattr(self, 'result', []))
