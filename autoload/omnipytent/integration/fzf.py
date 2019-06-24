import vim

import sys

from omnipytent.async_execution import SelectionUI
from omnipytent.execution import FN, quote
from omnipytent.util import RawVim
from omnipytent import simple_tcp_loopback_server

class FZF(SelectionUI):
    def gen_entry(self, i, item):
        return '%s %s' % (i, self.fmt(item))

    def on_yield(self):
        params = {}
        params['source'] = self.get_source()

        sink = RawVim("function('omnipytent#integration#fzf#finish')")
        flags = []
        flags.append('--with-nth=2..')
        if self.multi:
            params['sink*'] = sink
            flags.append('--multi')
        else:
            params['sink'] = sink
        params['yieldedCommand'] = self.vim_obj

        params['down'] = '~40%'
        if self.prompt:
            flags.append('--prompt ' + quote(self.prompt))

        if self.preview:
            self.preview_server_cm = simple_tcp_loopback_server.socket_bound(self._bytes_for_preview)
            preview_server_port = self.preview_server_cm.__enter__()
            flags.append('--preview ' + quote('%s %s %d {1}' % (
                quote(sys.executable),
                quote(simple_tcp_loopback_server.__file__),
                preview_server_port)))
        else:
            self.preview_server_cm = None

        params['options'] = ' '.join(map(str, flags))
        FN['fzf#run'](params)

    def finish(self, choice):
        if self.preview_server_cm:
            self.preview_server_cm.__exit__(None, None, None)
        self.run_next_frame('finish_indices', choice)
