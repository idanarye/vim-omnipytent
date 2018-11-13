import vim

from tempfile import NamedTemporaryFile

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN

class DENITE(SelectionUI):
    _preview_file = None

    def on_yield(self):
        FN['denite#start']([dict(
            name='omnipytent-choice',
            args=[],
        )], dict(
            yielded_command=str(self.vim_obj),
            auto_preview=1 if self.preview else 0,
        ))

    def gen_entry(self, i, item):
        return dict(idx=i,
                    word=self.fmt(item))

    def create_preview_file(self, index):
        # TODO: somehow merge this with UNITE. The problem is how to clear the file
        if self._preview_file is None:
            self._preview_file = NamedTemporaryFile()

        self._preview_file.file.seek(0)
        self._preview_file.file.truncate(0)
        self._preview_file.file.writelines([self._bytes_for_preview(index)])
        self._preview_file.file.flush()
        return self._preview_file.name

    def finish(self, choice):
        if self._preview_file:
            self._preview_file.close()
        self.run_next_frame('finish_indices', choice)
