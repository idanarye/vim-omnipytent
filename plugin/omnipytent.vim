command! -range -complete=customlist,omnipytent#completeIncludeTaskArgs -nargs=* OP call omnipytent#invoke(0, <line1>, <line2>, <count>, <f-args>)
command! -range -complete=customlist,omnipytent#complete2IncludeTaskArgs -nargs=* OP2 call omnipytent#invoke(2, <line1>, <line2>, <count>, <f-args>)
command! -range -complete=customlist,omnipytent#complete3IncludeTaskArgs -nargs=* OP3 call omnipytent#invoke(3, <line1>, <line2>, <count>, <f-args>)

command! -complete=customlist,omnipytent#complete -nargs=? OPedit call omnipytent#editTask(0, '', <q-args>)
command! -complete=customlist,omnipytent#complete2 -nargs=? OP2edit call omnipytent#editTask(2, '', <q-args>)
command! -complete=customlist,omnipytent#complete3 -nargs=? OP3edit call omnipytent#editTask(3, '', <q-args>)

command! -complete=customlist,omnipytent#complete -nargs=? OPsedit call omnipytent#editTask(0, 'split', <q-args>)
command! -complete=customlist,omnipytent#complete2 -nargs=? OP2sedit call omnipytent#editTask(2, 'split', <q-args>)
command! -complete=customlist,omnipytent#complete3 -nargs=? OP3sedit call omnipytent#editTask(3, 'split', <q-args>)

command! -complete=customlist,omnipytent#complete -nargs=? OPvedit call omnipytent#editTask(0, 'vsplit', <q-args>)
command! -complete=customlist,omnipytent#complete2 -nargs=? OP2vedit call omnipytent#editTask(2, 'vsplit', <q-args>)
command! -complete=customlist,omnipytent#complete3 -nargs=? OP3vedit call omnipytent#editTask(3, 'vsplit', <q-args>)

command! -complete=customlist,omnipytent#complete -nargs=? OPtedit call omnipytent#editTask(0, 'tabnew', <q-args>)
command! -complete=customlist,omnipytent#complete2 -nargs=? OP2tedit call omnipytent#editTask(2, 'tabnew', <q-args>)
command! -complete=customlist,omnipytent#complete3 -nargs=? OP3tedit call omnipytent#editTask(3, 'tabnew', <q-args>)

command! OPconvertTasksFilePythonVersion call omnipytent#convertTasksFilePythonVersion()
