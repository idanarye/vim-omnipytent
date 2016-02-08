import vim


def input_list(prompt, options):
    take_from = 0
    while take_from < len(options):
        take_this_time = int(vim.eval('&lines')) - 2
        more_items_remaining = take_from + take_this_time < len(options)
        if more_items_remaining:
            take_this_time -= 1

        options_slice = options[take_from:(take_from + take_this_time)]
        take_from += take_this_time

        number_length = len(str(len(options_slice)))

        def iteration_items_generator():
            for option in options_slice:
                yield option
            if more_items_remaining:
                yield '*MORE*'

        def list_for_input_query_generator():
            yield prompt
            for index, option in enumerate(iteration_items_generator()):
                index_text = str(index + 1)
                yield '%s)%s %s' % (index_text,
                                    ' ' * (number_length - len(index_text)),
                                    option)
        list_for_input_query = list(list_for_input_query_generator())
        chosen_option_number = int(vim.eval("inputlist(%s)" % repr(list_for_input_query)))

        if more_items_remaining and chosen_option_number == len(options_slice) + 1:
            print(' ')
        elif chosen_option_number < 1 or len(options_slice) < chosen_option_number:
            return None
        else:
            return options_slice[chosen_option_number - 1]

