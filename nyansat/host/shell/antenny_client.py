# Client middle layer
import logging

from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.nyan_explorer import NyanExplorer
from nyansat.host.shell.errors import NotVisibleError, DeviceNotOpenError, NoAntKontrolError, PyboardError


def antkontrol_exception(func):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except NoAntKontrolError as e:
            print("Please run 'antkontrol start' to initialize the antenna.")
            logging.error(e)
        except DeviceNotOpenError as e:
            print("Not connected to device. Use 'open' first.")
            logging.error(e)
        except PyboardError as e:
            print("The AntKontrol object is not responding. Restart it with 'antkontrol start'")
            logging.error(e)

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

    def guard_open(self):
        if self.fe is None:
            raise DeviceNotOpenError
        else:
            return True

    def check_init(self):
        if not self.fe.is_antenna_initialized():
            raise NoAntKontrolError
        else:
            return True

    def check_open_and_init(self):
        # TODO: Update this based on how the two above will work
        self.guard_open()
        self.check_init()

    # Sample architecture for elevation.
    @antkontrol_exception
    def elevation(self, el):
        self.check_open_and_init()
        self.safemode_guard()
        self.fe.set_elevation_degree(el)



