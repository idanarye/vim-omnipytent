function! omnipytent#integration#fzf#finish(result) dict abort
    call self.yieldedCommand.call('finish', a:result)
endfunction
