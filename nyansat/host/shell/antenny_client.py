# Client middle layer
from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.nyan_explorer import NyanExplorer, NyanExplorerError


def antkontrol_exception(func):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except NyanExplorerError as e:
            # TODO: Fix to use self.printer (decorator must be part of the AntennyClient class somehow)
            print("The AntKontrol object is not responding. Restart it with 'antkontrol start'")
            print(e)

    return wrapper


class AntennyClient(object):

    def __init__(self, fe: NyanExplorer, printer: TerminalPrinter):
        self.fe = fe
        self.printer = printer

    def safemode_guard(self):
        """Warns user if AntKontrol is in SAFE MODE while using motor-class commands"""
        if self.fe.is_safemode():
            self.printer.print_error("AntKontrol is in SAFE MODE. Attached motors will not move")
            print("If you did not intend to be in SAFE MODE, check your configuration and run "
                  "'antkontrol start'")

    # TODO: Should be decorator?
    def check_open(self):
        if self.fe is None:
            self.printer.print_error("Not connected to device. Use 'open' first.")
            # TODO: Raise error
            return False
        else:
            return True

    # TODO: Should be decorator?
    def check_init(self):
        if self.fe.is_antenna_initialized():
            return True
        else:
            self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            # TODO: Raise error
            return False

    def check_open_and_init(self):
        # TODO: Update this based on how the two above will work
        self.check_open()
        self.check_init()

    # Sample architecture for elevation.
    @antkontrol_exception
    def elevation(self, el):
        self.check_open_and_init()
        self.safemode_guard()
        self.fe.set_elevation_degree(el)
        """
        if self.check_open():
            try:
                if self.fe.is_antenna_initialized():
                    self.safemode_guard()
                    self.fe.set_elevation_degree(el)
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                    e
                )
        """
        pass



