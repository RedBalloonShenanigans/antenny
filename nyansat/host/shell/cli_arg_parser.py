# Arg Parser
import shlex

from nyansat.host.shell.errors import ParameterError, NumArgsError


class CLIArgumentProperty(object):
    def __init__(
            self,
            arg_type,  # type: Type
            choices,  # type: Optional[Set[str]]
    ):
        self.arg_type = arg_type
        self.choices = choices


def parse_cli_args(
        args,  # type: #Tuple[str]
        function_name: str,
        num_expected_args,  # type: int
        argument_properties,  # type: List[CLIArgumentProperty]
):
    split_args = shlex.split(args)
    if len(split_args) != num_expected_args:
        raise NumArgsError('{} only takes {} args, got {}!'.format(
                function_name,
                num_expected_args,
                len(split_args)
        ))
    parsed_args = []
    for split_arg, argument_property in zip(split_args, argument_properties):
        try:
            converted = argument_property.arg_type(split_arg)
        except ValueError:
            raise ParameterError
        if argument_property.choices is not None:
            if converted not in argument_property.choices:
                raise ParameterError(
                        '{} not a choice, expected {}'.format(converted, argument_property.choices)
                )
        parsed_args.append(converted)
    return parsed_args


if __name__ == '__main__':
    arg_properties = [
        CLIArgumentProperty(
                str,
                {
                    'start',
                }
        ),
    ]
    from_the_cmd_class = 'start'
    parsed_args = parse_cli_args(from_the_cmd_class, 'antkontrol', 1, arg_properties)
    assert parsed_args[0] == 'start'
    bad_value_from_the_cmd_class = 'start dsfjsdf'
    try:
        parsed_args = parse_cli_args(bad_value_from_the_cmd_class, 'antkontrol', 1, arg_properties)
        print("not working")
    except:
        print("Working")
