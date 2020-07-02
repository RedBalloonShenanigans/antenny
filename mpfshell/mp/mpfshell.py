##
# The MIT License (MIT)
#
# Copyright (c) 2016 Stefan Wendler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##


import argparse
# import cmd2 as cmd
import cmd
import glob
import io
import logging
import os
import platform
import sys
import tempfile
import subprocess
import time

import colorama
import serial
from mp import version
from mp.conbase import ConError
from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching, RemoteIOError
from mp.pyboard import PyboardError
from mp.tokenizer import Tokenizer



class MpFileShell(cmd.Cmd):

    GYRO_CALIBRATION_MESSAGE = "To calibrate the gyroscope, let the sensor rest on a level surface for a few seconds."
    ACCEL_CALIBRATION_MESSAGE = "To calibrate the accelerometer, slowly move the sensor into >=6 distinct orientations, some perpendicular to the xyz axes."
    MAGNET_CALIBRATION_MESSAGE = "To calibrate the magnetometer, move the sensor in figure-8 shapes through the air a few times."

    def __init__(self, color=False, caching=False, reset=False):
        if color:
            colorama.init()
            cmd.Cmd.__init__(self, stdout=colorama.initialise.wrapped_stdout)
        else:
            cmd.Cmd.__init__(self)

        self.emptyline = lambda : None

        if platform.system() == "Windows":
            self.use_rawinput = False

        self.color = color
        self.caching = caching
        self.reset = reset

        self.fe = None
        self.repl = None
        self.tokenizer = Tokenizer()

        self.__intro()
        self.__set_prompt_path()

        # Change prompts to be more descriptive
        self.prompts = {
                "gps_uart_tx": ("GPS UART TX pin#: ", int),
                "gps_uart_rx": ("GPS UART RX pin#: ", int),
                "i2c_servo_scl": ("Servo SCL pin#: ", int),
                "i2c_servo_sda": ("Servo SDA pin#: ", int),
                "i2c_bno_scl": ("BNO055 SCL pin#: ", int),
                "i2c_bno_sda": ("BNO055 SDA pin#: ", int),
                "i2c_screen_scl": ("Screen SCL pin#: ", int),
                "i2c_screen_sda": ("Screen SDA pin#: ", int),
                "elevation_servo_index": ("Servo default elevation index: ", float),
                "azimuth_servo_index": ("Servo default azimuth index: ", float),
                "elevation_max_rate": ("Servo elevation max rate: ", float),
                "azimuth_max_rate": ("Servo azimuth max rate: ", float)
        }

    def __del__(self):
        self.__disconnect()

    def __intro(self):

        if self.color:
            self.intro = (
                "\n"
                + colorama.Fore.GREEN
                + "** FORKED Micropython File Shell v%s, sw@kaltpost.de ** " % version.FULL
                + colorama.Fore.RESET
                + "\n"
            )
        else:
            self.intro = (
                "\n** FORKED Micropython File Shell v%s, sw@kaltpost.de **\n" % version.FULL
            )

        self.intro += "-- Running on Python %d.%d using PySerial %s --\n" % (
            sys.version_info[0],
            sys.version_info[1],
            serial.VERSION,
        )

    def __set_prompt_path(self):

        if self.fe is not None:
            pwd = self.fe.pwd()
        else:
            pwd = "/"

        if self.color:
            self.prompt = (
                colorama.Fore.BLUE
                + "mpfs ["
                + colorama.Fore.YELLOW
                + pwd
                + colorama.Fore.BLUE
                + "]> "
                + colorama.Fore.RESET
            )
        else:
            self.prompt = "mpfs [" + pwd + "]> "

    def __error(self, msg):

        if self.color:
            print("\n" + colorama.Fore.RED + msg + colorama.Fore.RESET + "\n")
        else:
            print("\n" + msg + "\n")

    def __connect(self, port):

        try:
            self.__disconnect()

            if self.reset:
                print("Hard resetting device ...")
            if self.caching:
                self.fe = MpFileExplorerCaching(port, self.reset)
            else:
                self.fe = MpFileExplorer(port, self.reset)
            print("Connected to %s" % self.fe.sysname)
            self.__set_prompt_path()
            return True
        except PyboardError as e:
            logging.error(e)
            self.__error(str(e))
        except ConError as e:
            logging.error(e)
            self.__error("Failed to open: %s" % port)
        except AttributeError as e:
            logging.error(e)
            self.__error("Failed to open: %s" % port)
        return False

    def __disconnect(self):

        if self.fe is not None:
            try:
                self.fe.close()
                self.fe = None
                self.__set_prompt_path()
            except RemoteIOError as e:
                self.__error(str(e))

    def __is_open(self):

        if self.fe is None:
            self.__error("Not connected to device. Use 'open' first.")
            return False

        return True

    def __parse_file_names(self, args):

        tokens, rest = self.tokenizer.tokenize(args)

        if rest != "":
            self.__error("Invalid filename given: %s" % rest)
        else:
            return [token.value for token in tokens]

        return None

    def __config_set(self, key, val):
        if isinstance(val, int) or isinstance(val, float):
            self.do_exec("config.set(\"%s\", %d)" % (key, val))
        elif isinstance(val, str):
            self.do_exec("config.set(\"%s\", %s)" % (key, val))

    def __config_get(self, key):
        command = "config.get(\"{}\")".format(key)
        return self.fe.eval_string_expr(command)

    def __which_config(self):
        return self.fe.eval_string_expr("config.current_file()")

    def do_exit(self, args):
        """exit
        Exit this shell.
        """
        self.__disconnect()

        return True

    do_EOF = do_exit

    def do_open(self, args):
        """open <TARGET>
        Open connection to device with given target. TARGET might be:

        - a serial port, e.g.       ttyUSB0, ser:/dev/ttyUSB0
        - a telnet host, e.g        tn:192.168.1.1 or tn:192.168.1.1,login,passwd
        - a websocket host, e.g.    ws:192.168.1.1 or ws:192.168.1.1,passwd
        """

        if not len(args):
            self.__error("Missing argument: <PORT>")
            return False

        if (
            not args.startswith("ser:/dev/")
            and not args.startswith("ser:COM")
            and not args.startswith("tn:")
            and not args.startswith("ws:")
        ):

            if platform.system() == "Windows":
                args = "ser:" + args
            else:
                args = "ser:/dev/" + args

        return self.__connect(args)

    def complete_open(self, *args):
        ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        return [i[5:] for i in ports if i[5:].startswith(args[0])]

    def do_close(self, args):
        """close
        Close connection to device.
        """

        self.__disconnect()

    def do_ls(self, args):
        """ls
        List remote files.
        """
        if self.__is_open():
            try:
                files = self.fe.ls(add_details=True)

                if self.fe.pwd() != "/":
                    files = [("..", "D")] + files

                print("\nRemote files in '%s':\n" % self.fe.pwd())

                for elem, type in files:
                    if type == "F":
                        if self.color:
                            print(
                                colorama.Fore.CYAN
                                + ("       %s" % elem)
                                + colorama.Fore.RESET
                            )
                        else:
                            print("       %s" % elem)
                    else:
                        if self.color:
                            print(
                                colorama.Fore.MAGENTA
                                + (" <dir> %s" % elem)
                                + colorama.Fore.RESET
                            )
                        else:
                            print(" <dir> %s" % elem)

                print("")

            except IOError as e:
                self.__error(str(e))

    def do_pwd(self, args):
        """pwd
         Print current remote directory.
         """
        if self.__is_open():
            print(self.fe.pwd())

    def do_cd(self, args):
        """cd <TARGET DIR>
        Change current remote directory to given target.
        """
        if not len(args):
            self.__error("Missing argument: <REMOTE DIR>")
        elif self.__is_open():
            try:
                s_args = self.__parse_file_names(args)
                if not s_args:
                    return
                elif len(s_args) > 1:
                    self.__error("Only one argument allowed: <REMOTE DIR>")
                    return

                self.fe.cd(s_args[0])
                self.__set_prompt_path()
            except IOError as e:
                self.__error(str(e))

    def complete_cd(self, *args):

        try:
            files = self.fe.ls(add_files=False)
        except Exception:
            files = []

        return [i for i in files if i.startswith(args[0])]

    def do_md(self, args):
        """md <TARGET DIR>
        Create new remote directory.
        """
        if not len(args):
            self.__error("Missing argument: <REMOTE DIR>")
        elif self.__is_open():
            try:
                s_args = self.__parse_file_names(args)
                if not s_args:
                    return
                elif len(s_args) > 1:
                    self.__error("Only one argument allowed: <REMOTE DIR>")
                    return

                self.fe.md(s_args[0])
            except IOError as e:
                self.__error(str(e))

    def do_lls(self, args):
        """lls
        List files in current local directory.
        """

        files = os.listdir(".")

        print("\nLocal files:\n")

        for f in files:
            if os.path.isdir(f):
                if self.color:
                    print(
                        colorama.Fore.MAGENTA + (" <dir> %s" % f) + colorama.Fore.RESET
                    )
                else:
                    print(" <dir> %s" % f)
        for f in files:
            if os.path.isfile(f):
                if self.color:
                    print(colorama.Fore.CYAN + ("       %s" % f) + colorama.Fore.RESET)
                else:
                    print("       %s" % f)
        print("")

    def do_lcd(self, args):
        """lcd <TARGET DIR>
        Change current local directory to given target.
        """

        if not len(args):
            self.__error("Missing argument: <LOCAL DIR>")
        else:
            try:
                s_args = self.__parse_file_names(args)
                if not s_args:
                    return
                elif len(s_args) > 1:
                    self.__error("Only one argument allowed: <LOCAL DIR>")
                    return

                os.chdir(s_args[0])
            except OSError as e:
                self.__error(str(e).split("] ")[-1])

    def complete_lcd(self, *args):
        dirs = [o for o in os.listdir(".") if os.path.isdir(os.path.join(".", o))]
        return [i for i in dirs if i.startswith(args[0])]

    def do_lpwd(self, args):
        """lpwd
        Print current local directory.
        """

        print(os.getcwd())

    def do_put(self, args):
        """put <LOCAL FILE> [<REMOTE FILE>]
        Upload local file. If the second parameter is given,
        its value is used for the remote file name. Otherwise the
        remote file will be named the same as the local file.
        """

        if not len(args):
            self.__error("Missing arguments: <LOCAL FILE> [<REMOTE FILE>]")

        elif self.__is_open():

            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 2:
                self.__error(
                    "Only one ore two arguments allowed: <LOCAL FILE> [<REMOTE FILE>]"
                )
                return

            lfile_name = s_args[0]

            if len(s_args) > 1:
                rfile_name = s_args[1]
            else:
                rfile_name = lfile_name

            try:
                self.fe.put(lfile_name, rfile_name)
            except IOError as e:
                self.__error(str(e))

    def complete_put(self, *args):
        files = [o for o in os.listdir(".") if os.path.isfile(os.path.join(".", o))]
        return [i for i in files if i.startswith(args[0])]

    def do_mput(self, args):
        """mput <SELECTION REGEX>
        Upload all local files that match the given regular expression.
        The remote files will be named the same as the local files.

        "mput" does not get directories, and it is not recursive.
        """

        if not len(args):
            self.__error("Missing argument: <SELECTION REGEX>")

        elif self.__is_open():

            try:
                self.fe.mput(os.getcwd(), args, True)
            except IOError as e:
                self.__error(str(e))

    def do_get(self, args):
        """get <REMOTE FILE> [<LOCAL FILE>]
        Download remote file. If the second parameter is given,
        its value is used for the local file name. Otherwise the
        locale file will be named the same as the remote file.
        """

        if not len(args):
            self.__error("Missing arguments: <REMOTE FILE> [<LOCAL FILE>]")

        elif self.__is_open():

            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 2:
                self.__error(
                    "Only one ore two arguments allowed: <REMOTE FILE> [<LOCAL FILE>]"
                )
                return

            rfile_name = s_args[0]

            if len(s_args) > 1:
                lfile_name = s_args[1]
            else:
                lfile_name = rfile_name

            try:
                self.fe.get(rfile_name, lfile_name)
            except IOError as e:
                self.__error(str(e))

    def do_mget(self, args):
        """mget <SELECTION REGEX>
        Download all remote files that match the given regular expression.
        The local files will be named the same as the remote files.

        "mget" does not get directories, and it is not recursive.
        """

        if not len(args):
            self.__error("Missing argument: <SELECTION REGEX>")

        elif self.__is_open():

            try:
                self.fe.mget(os.getcwd(), args, True)
            except IOError as e:
                self.__error(str(e))

    def complete_get(self, *args):

        try:
            files = self.fe.ls(add_dirs=False)
        except Exception:
            files = []

        return [i for i in files if i.startswith(args[0])]

    def do_rm(self, args):
        """rm <REMOTE FILE or DIR>
        Delete a remote file or directory.

        Note: only empty directories could be removed.
        """

        if not len(args):
            self.__error("Missing argument: <REMOTE FILE>")
        elif self.__is_open():

            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 1:
                self.__error("Only one argument allowed: <REMOTE FILE>")
                return

            try:
                self.fe.rm(s_args[0])
            except IOError as e:
                self.__error(str(e))
            except PyboardError:
                self.__error("Unable to send request to %s" % self.fe.sysname)

    def do_mrm(self, args):
        """mrm <SELECTION REGEX>
        Delete all remote files that match the given regular expression.

        "mrm" does not delete directories, and it is not recursive.
        """

        if not len(args):
            self.__error("Missing argument: <SELECTION REGEX>")

        elif self.__is_open():

            try:
                self.fe.mrm(args, True)
            except IOError as e:
                self.__error(str(e))

    def complete_rm(self, *args):

        try:
            files = self.fe.ls()
        except Exception:
            files = []

        return [i for i in files if i.startswith(args[0])]

    def do_cat(self, args):
        """cat <REMOTE FILE>
        Print the contents of a remote file.
        """

        if not len(args):
            self.__error("Missing argument: <REMOTE FILE>")
        elif self.__is_open():

            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 1:
                self.__error("Only one argument allowed: <REMOTE FILE>")
                return

            try:
                print(self.fe.gets(s_args[0]))
            except IOError as e:
                self.__error(str(e))

    complete_cat = complete_get

    def do_exec(self, args):
        """exec <STATEMENT>
        Execute a Python statement on remote.
        """

        def data_consumer(data):
            data = str(data.decode("utf-8"))
            sys.stdout.write(data.strip("\x04"))

        if not len(args):
            self.__error("Missing argument: <STATEMENT>")
        elif self.__is_open():

            try:
                self.fe.exec_raw_no_follow(args + "\n")
                ret = self.fe.follow(None, data_consumer)
                if len(ret[-1]):
                    self.__error(ret[-1].decode("utf-8"))

            except IOError as e:
                self.__error(str(e))
            except PyboardError as e:
                self.__error(str(e))

    def do_repl(self, args):
        """repl
        Enter Micropython REPL.
        """

        import serial

        ver = serial.VERSION.split(".")

        if int(ver[0]) < 2 or (int(ver[0]) == 2 and int(ver[1]) < 7):
            self.__error(
                "REPL needs PySerial version >= 2.7, found %s" % serial.VERSION
            )
            return

        if self.__is_open():

            if self.repl is None:

                from mp.term import Term

                self.repl = Term(self.fe.con)

                if platform.system() == "Windows":
                    self.repl.exit_character = chr(0x11)
                else:
                    self.repl.exit_character = chr(0x1D)

                self.repl.raw = True
                self.repl.set_rx_encoding("UTF-8")
                self.repl.set_tx_encoding("UTF-8")

            else:
                self.repl.serial = self.fe.con

            pwd = self.fe.pwd()
            self.fe.teardown()
            self.repl.start()

            if self.repl.exit_character == chr(0x11):
                print("\n*** Exit REPL with Ctrl+Q ***")
            else:
                print("\n*** Exit REPL with Ctrl+] ***")

            try:
                self.repl.join(True)
            except Exception:
                pass

            self.repl.console.cleanup()

            if self.caching:
                # Clear the file explorer cache so we can see any new files.
                self.fe.cache = {}

            self.fe.setup()
            try:
                self.fe.cd(pwd)
            except RemoteIOError as e:
                # Working directory does not exist anymore
                self.__error(str(e))
            finally:
                self.__set_prompt_path()
            print("")

    def do_mpyc(self, args):
        """mpyc <LOCAL PYTHON FILE>
        Compile a Python file into byte-code by using mpy-cross (which needs to be in the path).
        The compiled file has the same name as the original file but with extension '.mpy'.
        """

        if not len(args):
            self.__error("Missing argument: <LOCAL FILE>")
        else:

            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 1:
                self.__error("Only one argument allowed: <LOCAL FILE>")
                return

            try:
                self.fe.mpy_cross(s_args[0])
            except IOError as e:
                self.__error(str(e))

    def complete_mpyc(self, *args):
        files = [
            o
            for o in os.listdir(".")
            if (os.path.isfile(os.path.join(".", o)) and o.endswith(".py"))
        ]
        return [i for i in files if i.startswith(args[0])]

    def do_putc(self, args):
        """mputc <LOCAL PYTHON FILE> [<REMOTE FILE>]
        Compile a Python file into byte-code by using mpy-cross (which needs to be in the
        path) and upload it. The compiled file has the same name as the original file but
        with extension '.mpy' by default.
        """
        if not len(args):
            self.__error("Missing arguments: <LOCAL FILE> [<REMOTE FILE>]")

        elif self.__is_open():
            s_args = self.__parse_file_names(args)
            if not s_args:
                return
            elif len(s_args) > 2:
                self.__error(
                    "Only one ore two arguments allowed: <LOCAL FILE> [<REMOTE FILE>]"
                )
                return

            lfile_name = s_args[0]

            if len(s_args) > 1:
                rfile_name = s_args[1]
            else:
                rfile_name = (
                    lfile_name[: lfile_name.rfind(".")]
                    if "." in lfile_name
                    else lfile_name
                ) + ".mpy"

            _, tmp = tempfile.mkstemp()

            try:
                self.fe.mpy_cross(src=lfile_name, dst=tmp)
                self.fe.put(tmp, rfile_name)
            except IOError as e:
                self.__error(str(e))

            os.unlink(tmp)

    complete_putc = complete_mpyc

    def do_edit(self, args):
        """edit <REMOTE FILE>
        Copies file over, opens it in your editor, copies back when done.
        """
        if not len(args):
            self.__error("Missing argument: <REMOTE_FILE>")

        elif self.__is_open():
            try:
                self.do_get(args)
            except IOError as e:
                if "No such file" in str(e):
                    # make new file locally, then copy
                    # Not implemented yet
                    self.__error(str(e))
                    pass

            rfile_name, = self.__parse_file_names(args)
            if platform.system() == 'Windows':
                EDITOR = os.environ.get('EDITOR', 'notepad')
                subprocess.call([EDITOR, rfile_name], shell=True)
            else:
                EDITOR = os.environ.get('EDITOR', 'vim')
                subprocess.call([EDITOR, rfile_name])
            self.do_put(rfile_name)

    complete_edit = complete_get

    def do_setup(self, args):
        """setup <CONFIG_FILE>
        Interactive script to populate a config file.
        Switches to new config after finishing setup.
        """
        if not len(args):
            self.__error("Missing argument: <CONFIG_FILE>")

        elif self.__is_open():
            s_args = self.__parse_file_names(args)
            name, = s_args
            current = self.__which_config()

            self.do_exec("config.new(\"{}\")".format(name))

            print(colorama.Fore.GREEN +
                    "Welcome to Antenny!" +
                    colorama.Fore.RESET)
            print("Please enter the following information about your hardware\n")

            for k,info in self.prompts.items():
                prompt_text, typ = info
                try:
                    new_val = typ(input(prompt_text))
                except ValueError:
                    self.__error("Invalid type, setting to default.\nUse \"set\" to" \
                            "change the parameter")
                    new_val = self.fe.eval_string_expr("config.get_default(\"{}\")".format(k))

                self.__config_set(k, new_val)

            if self.caching:
                self.fe.cache = {}

            print(colorama.Fore.GREEN +
                    "\nConfiguration set for \"{}\"!\n".format(name) +
                    colorama.Fore.RESET +
                    "You can use \"set\" to change individual parameters\n" \
                    "or \"edit\" to change the config file " \
                    "directly")



    def do_set(self, args):
        """set <CONFIG_PARAM> <NEW_VAL>
        Set a parameter in the configuration file to a new value."""
        if not len(args):
            self.__error("missing arguments: <config_param> <new_val>")

        elif self.__is_open():
            s_args = self.__parse_file_names(args)
            if len(s_args) < 2:
                self.__error("Missing argument: <new_val>")
                return

            key, new_val = s_args
            try:
                old_val = self.__config_get(key)
            except:
                self.__error("No such configuration parameter")
                return

            _, typ = self.prompts[key]
            try:
                new_val = typ(new_val)
            except ValueError:
                self.__error(str(e))
                return

            self.__config_set(key, new_val)
            print("Changed " + "\"" + key + "\" from " + str(old_val) + " --> " + str(new_val))

    def complete_set(self, *args):
        if self.__is_open():
            return [key for key in self.prompts.keys() if key.startswith(args[0])]
        else:
            return []

    def do_configs(self, args):
        """configs
        Print a list of all configuration parameters."""
        if self.__is_open():

            print(colorama.Fore.GREEN +
                    "-Config parameters-\n" +
                    colorama.Fore.CYAN +
                    "Using \"{}\"".format(self.__which_config()) +
                    colorama.Fore.RESET)
            for key in self.prompts.keys():
                print(key + ": " + self.__config_get(key))

    def do_clear(self, args):
        """clear
        Clear the currently used config file."""
        """
        if self.__is_open():
            self.do_exec("config.clear()")
        """
        pass

    def do_revert(self, args):
        """revert
        Switch to using the backup config file. Current config
        will be deleted."""
        """
        if self.__is_open():
            self.do_exec("config.revert()")
        """
        pass

    def do_switch(self, args):
        """switch <CONFIG_FILE>
        Switch to using a different config file."""
        if not len(args):
            self.__error("Missing arguments: <config_file>")

        elif self.__is_open():
            s_args = self.__parse_file_names(args)
            if len(s_args) > 1:
                self.__error("Usage: switch <CONFIG_FILE>")
                return
            name, = s_args
            files = self.fe.ls()
            if name not in files:
                self.__error("No such file")
                return
            current = self.__which_config()
            self.do_exec("config.switch(\"{}\")".format(name))
            print(colorama.Fore.GREEN +
                    "Switched from \"{}\"".format(current) +
                    "to \"{}\"".format(name))

    def complete_switch(self, *args):
        try:
            files = self.fe.ls(add_dirs=False)
        except Exception:
            files = []
        current = self.__which_config()
        return [f for f in files if f.startswith(args[0]) and f.endswith(".json")]

    def do_telemetry(self, args):
        """telemetry
        Print telemetry data directly from the board. Show data such as motor
        status, IMU status, etc.
        """
        print("Telemetry data:")
        print("IMU status: ", end="")
        print(self.fe.eval_string_expr("a.imu_status()"))
        print("Motor status: ", end="")
        print(self.fe.eval_string_expr("a.motor_status()"))

    def do_calibrate(self, args):
        """calibrate
        Detect IMU calibration status and provide instructions on how to calibrate if necessary.
        """
        if args:
            self.__error("Usage: calibrate does not take arguments.")
            return

        if self.__is_open():
            print("Detecting calibration status ...")
            data = eval(self.fe.eval_string_expr("calibration.calibration_status()"))
            if not data:
                self.__error("Error: BNO055 not detected.")
                return

            (system_calibration, gyro_calibration,
                accel_calibration, magnet_calibration) = data

            yes_display_string = colorama.Fore.GREEN + "YES" + colorama.Fore.RESET
            no_display_string = colorama.Fore.RED + "NO" + colorama.Fore.RESET

            print("System calibrated?", f"{yes_display_string}" if system_calibration else no_display_string)
            if not system_calibration:
                print("Gyroscope calibrated?",
                        yes_display_string if gyro_calibration else no_display_string)
                print("Accelerometer calibrated?",
                        yes_display_string if accel_calibration else no_display_string)
                print("Magnetometer calibrated?",
                        yes_display_string if magnet_calibration else no_display_string, "\n")

                if not gyro_calibration:
                    print(f" - {self.GYRO_CALIBRATION_MESSAGE}")
                if not accel_calibration:
                    print(f" - {self.ACCEL_CALIBRATION_MESSAGE}")
                if not magnet_calibration:
                    print(f" - {self.MAGNET_CALIBRATION_MESSAGE}")

    def do_save_calibration(self, args):
        """save_calibration
        Save current IMU calibration data to the current configuration.
        """
        if args:
            self.__error("Usage: save_calibration does not take arguments.")
            return

        if self.__is_open():
            status = self.fe.eval_string_expr("calibration.save_calibration()")
            if not status:
                self.__error("Error: BNO055 not detected or error in reading calibration registers.")

    def do_upload_calibration(self, args):
        """upload_calibration
        Upload the currently stored calibration data to the connected IMU.
        """
        if args:
            self.__error("Usage: upload_calibration does not take arguments.")
            return

        if self.__is_open():
            status = self.fe.eval_string_expr("calibration.upload_calibration()")
            if not status:
                self.__error("Error: BNO055 not detected or error in writing calibration registers.")


    def do_motortest(self, args):
        """motortest
        Test the motors to plot their accuracy against the measured IMU values.
        """
        print("Running motor testing routine...")
        print(self.fe.eval_string_expr("a.motor_test()"))

    def do_elevation(self, args):
        """elevation <ELEVATION>
        Set the elevation to the level given in degrees by the first argument.
        """
        if not len(args):
            self.__error("Missing argument: <ELEVATION>")
        try:
            el = float(args)
            print(self.fe.eval_string_expr("a.set_el_deg({})".format(el)))
        except ValueError:
            print("<ELEVATION> must be a floating point number!")

    def do_azimuth(self, args):
        """azimuth <AZIMUTH>
        Set the azimuth to the level given in degrees by the first argument.
        """
        if not len(args):
            self.__error("Missing argument: <AZIMUTH>")
        try:
            az = float(args)
            print(self.fe.eval_string_expr("a.set_az_deg({})".format(az)))
        except ValueError:
            print("<AZIMUTH> must be a floating point number!")

    def do_antkontrol(self, args):
        """antkontrol
        Create a new global AntKontrol instance
        """
        ret, ret_err = self.fe.exec_raw("import antenny")
        ret, ret_err = self.fe.exec_raw("a = antenny.AntKontrol()")
        print(ret.decode("utf-8"))
        print(ret_err.decode("utf-8"))

    def do_starttelemetry(self, args):
        """startelemetry
        Start a telemetry data sender on antenny over UDP. Restarts the
        telemetry thread if it is already running (which it is by default).
        """
        print("Stopping existing telemetry-sending thread...")
        ret, ret_err = self.fe.exec_raw("a._run_telem_thread = False")
        time.sleep(1)
        print("Starting a new telemetry-sending thread...")
        ret, ret_err = self.fe.exec_raw("a._run_telem_thread = True")
        self.fe.eval_string_expr("a._telem_thread = antenny._thread.start_new_thread(a.send_telem, ())")




def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--command",
        help="execute given commands (separated by ;)",
        default=None,
        nargs="*",
    )
    parser.add_argument(
        "-s", "--script", help="execute commands from file", default=None
    )
    parser.add_argument(
        "-n",
        "--noninteractive",
        help="non interactive mode (don't enter shell)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--nocolor", help="disable color", action="store_true", default=False
    )
    parser.add_argument(
        "--nocache", help="disable cache", action="store_true", default=False
    )

    parser.add_argument("--logfile", help="write log to file", default=None)
    parser.add_argument(
        "--loglevel",
        help="loglevel (CRITICAL, ERROR, WARNING, INFO, DEBUG)",
        default="INFO",
    )

    parser.add_argument(
        "--reset",
        help="hard reset device via DTR (serial connection only)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-o",
        "--open",
        help="directly opens board",
        metavar="BOARD",
        action="store",
        default=None,
    )
    parser.add_argument(
        "board", help="directly opens board", nargs="?", action="store", default=None
    )

    args = parser.parse_args()

    format = "%(asctime)s\t%(levelname)s\t%(message)s"

    if args.logfile is not None:
        logging.basicConfig(format=format, filename=args.logfile, level=args.loglevel)
    else:
        logging.basicConfig(format=format, level=logging.CRITICAL)

    logging.info("Micropython File Shell v%s started" % version.FULL)
    logging.info(
        "Running on Python %d.%d using PySerial %s"
        % (sys.version_info[0], sys.version_info[1], serial.VERSION)
    )

    mpfs = MpFileShell(not args.nocolor, not args.nocache, args.reset)

    if args.open is not None:
        if args.board is None:
            if not mpfs.do_open(args.open):
                return 1
        else:
            print(
                "Positional argument ({}) takes precedence over --open.".format(
                    args.board
                )
            )
    if args.board is not None:
        mpfs.do_open(args.board)

    if args.command is not None:

        for acmd in " ".join(args.command).split(";"):
            scmd = acmd.strip()
            if len(scmd) > 0 and not scmd.startswith("#"):
                mpfs.onecmd(scmd)

    elif args.script is not None:

        f = open(args.script, "r")
        script = ""

        for line in f:

            sline = line.strip()

            if len(sline) > 0 and not sline.startswith("#"):
                script += sline + "\n"

        if sys.version_info < (3, 0):
            sys.stdin = io.StringIO(script.decode("utf-8"))
        else:
            sys.stdin = io.StringIO(script)

        mpfs.intro = ""
        mpfs.prompt = ""

    if not args.noninteractive:

        try:
            mpfs.cmdloop()
        except KeyboardInterrupt:
            print("")


if __name__ == "__main__":

    sys.exit(main())
