from mp.pyboard import Pyboard

class NyanPyboard(Pyboard):

    def eval_string_expr(self, expr_string):
        command = expr_string.encode('utf-8')
        ret = self.exec_("print(eval({}))".format(command))
        ret = ret.strip()
        return ret.decode()
