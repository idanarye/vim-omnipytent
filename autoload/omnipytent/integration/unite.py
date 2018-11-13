import vim

from tempfile import NamedTemporaryFile

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN

class UNITE(SelectionUI):
    _preview_file = None

    def on_yield(self):
        FN['unite#start'](['omnipytent_choice'], dict(
            omnipytent__yieldedCommand=self.vim_obj,
            buffer_name=self.prompt or '',
            auto_preview=1 if self.preview else 0,
        ))

    def gen_entry(self, i, item):
        return dict(idx=i,
                    word=self.fmt(item),
                    kind='omnipytent_choice')

    def set_result(self, result):
        self.result = result

    def create_preview_file(self, index):
        if self._preview_file is None:
            self._preview_file = NamedTemporaryFile()

        self._preview_file.file.seek(0)
        self._preview_file.file.truncate(0)
        self._preview_file.file.writelines([self._bytes_for_preview(index)])
        self._preview_file.file.flush()
        return self._preview_file.name

    def finish(self):
        if self._preview_file:
            self._preview_file.close()
        # NOTE: we will only get the proper self.result in the next frame
        self.run_next_frame('resume_execution')

    def resume_execution(self):
        self.finish_indices(getattr(self, 'result', []))
