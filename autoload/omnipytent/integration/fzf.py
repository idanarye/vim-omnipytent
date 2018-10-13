import vim

from omnipytent.async_execution import FuzzyChooser
from omnipytent.execution import FN, quote
from omnipytent.util import vim_repr, RawVim, load_companion_vim_file

class FZF(FuzzyChooser):
    def on_yield(self):
        params = {}
        params['source'] = list(map(str, self.source))

        sink = RawVim("function('omnipytent#integration#fzf#finish')")
        flags = []
        if self.multi:
            params['sink*'] = sink
            flags.append('--multi')
        else:
            params['sink'] = sink
        params['yieldedCommand'] = self.vim_obj

        params['down'] = '~40%'
        if self.prompt:
            flags.append('--prompt ' + quote(self.prompt))

        params['options'] = ' '.join(map(str, flags))
        FN['fzf#run'](params)

    def finish(self, choice):
        self.run_next_frame('resume_execution', choice)

    def resume_execution(self, choice):
        self.resume(choice)
