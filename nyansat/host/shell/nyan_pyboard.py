from mp.pyboard import Pyboard


class NyanPyboard(Pyboard):
    """Wrapper for Pyboard that adds eval_string_expr."""

    def eval_string_expr(self, expr_string):
        """Return the result of a command string that will run on the ESP32.

        Arguments:
        expr_string -- A string containing the command to execute on the ESP32
        """
        command = expr_string.encode('utf-8')
        ret = self.exec_("print(eval({}))".format(command))
        ret = ret.strip()
        return ret.decode()
