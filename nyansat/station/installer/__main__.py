"""
Antenny installer
"""
import argparse
import getpass
import json
import logging
import os
import sys
import time

from mp.mpfexp import MpFileExplorer, RemoteIOError
from mp.pyboard import PyboardError
from typing import List

PASSWORD_KEY = 'key'
SSID_KEY = 'ssid'
WIFI_CONFIG_PATH = 'wifi_config.json'
WEBREPL_CONFIG_PATH = 'webrepl_cfg.py'
REPO_NAME = 'antenny'
UP_ONE_DIRECTORY = '..'
STATION_CODE_RELATIVE_PATH = 'nyansat/station'

PACKAGES_TO_INSTALL = [
    "logging"
]
# File paths in the antenny repo, not on the board
LIBRARY_FILES = [
    'lib/BNO055/bno055.py',
    'lib/BNO055/bno055_base.py',
    'lib/PCA9685/pca9685.py',
    'lib/micropython/drivers/display/ssd1306.py',
    'lib/micropygps/micropyGPS.py',
    'lib/simple-pid/simple_pid/PID.py',
]

LOG = logging.getLogger('antenny_installer')


class AntennyInstaller(object):
    """
    Install the antenny source code
    """

    def __init__(
            self,
            serial_path: str,
    ):
        self._serial_path = serial_path
        self._file_explorer = None
        self._connect()

    def _connect(
            self,
            num_connection_retries=3
    ):
        """
        Connect to the antenny device, update the FileExplorer.
        """
        for retry_count in range(num_connection_retries):
            try:
                self._file_explorer = MpFileExplorer(f'ser:{self._serial_path}')
                break
            except:
                LOG.warning(f"Retrying to connect to the ESP32 device, attempt "
                            f"{retry_count}/{num_connection_retries}")

    def _clean_files(
            self,
            in_subdirectory: bool = False,
            ignore_lib: bool = False,
    ):
        """
        Clean up the existing files on the device.
        """
        files = self._file_explorer.ls()
        libs = set([os.path.basename(f) for f in LIBRARY_FILES])
        if not in_subdirectory:
            LOG.info(f"Cleaning {len(files)} file(s) on the device")
        for file_ in files:
            if ignore_lib and not in_subdirectory and (file_ in libs or file_ == "lib"):
                continue
            try:
                self._file_explorer.rm(file_)
            except Exception as e:
                # Try to explore subdirectory
                LOG.info(f"Attempting to clean directory {file_}")
                self._file_explorer.cd(file_)
                self._clean_files(in_subdirectory=True)
        if in_subdirectory:
            self._file_explorer.cd('..')
        else:
            LOG.info("Done cleaning FS")

    def _ensure_directory(self):
        """
        Ensure we're in the main antenny directory.
        """
        curr_working_dir = os.getcwd()
        if os.path.basename(curr_working_dir) != REPO_NAME:
            if REPO_NAME not in curr_working_dir:
                # TODO: should we clone the git repo instead?
                raise RuntimeError(
                        "Cannot find the antenny repository, please run this from the root "
                        "of that directory."
                )
            # walk back up the directory tree, it's in the current working dir
            while os.path.basename(os.getcwd()) != REPO_NAME:
                os.chdir(UP_ONE_DIRECTORY)
        os.chdir(STATION_CODE_RELATIVE_PATH)

    def _recursive_put_files(self, is_subdirectory=False, sub_directory_name=None):
        """
        Recursively copy all files from a starting directory to the pyboard.
        """
        current_path = os.path.basename(os.getcwd())
        LOG.info(f"Copying files from the directory '{current_path}'")
        for path_ in os.listdir():
            # Skip dotfiles and __pycache__
            if path_.startswith('.') or path_.startswith('__'):
                continue
            if os.path.isdir(path_):
                if sub_directory_name is not None:
                    dir_name = os.path.join(sub_directory_name, path_)
                else:
                    dir_name = path_
                try:
                    self._file_explorer.md(dir_name)
                except Exception as e:
                    print(e)
                os.chdir(dir_name.split(os.path.sep)[-1])
                self._recursive_put_files(
                        is_subdirectory=True,
                        sub_directory_name=dir_name,
                )
            else:
                try:
                    if sub_directory_name is not None:
                        self._file_explorer.put(path_, os.path.join(sub_directory_name, path_))
                    else:
                        self._file_explorer.put(path_)
                except RemoteIOError as e:
                    print(path_, e)
        if is_subdirectory:
            os.chdir(UP_ONE_DIRECTORY)

    def _put_antenny_files_on_device(self):
        """
        Copy antenny source files to the device
        """
        self._ensure_directory()
        self._recursive_put_files()

    def _put_library_files_on_device(self):
        """
        Copy required antenny library files.
        """
        LOG.info(f"Putting {len(LIBRARY_FILES)} library files on the device.")
        for file_ in LIBRARY_FILES:
            try:
                self._file_explorer.put(file_, os.path.basename(file_))
            except Exception as e:
                print(f"Didn't put library file {file_} on the device: {e}")
        LOG.info("Library files installed")

    def _query_user_for_wifi_credentials(self):
        """
        Optional: Query user for their login credentials (wifi & webrepl)
        """
        LOG.info("Credentials gathering [ctrl-c to skip]")
        try:
            if os.path.exists(WIFI_CONFIG_PATH):
                with open(WIFI_CONFIG_PATH, 'r') as f:
                    wifi_config = json.load(f)
                ssid, password = wifi_config.get(SSID_KEY, ''), wifi_config.get(PASSWORD_KEY, '')
                printed_password = '*' * len(password)
                use_cached = input(
                        f"Do you want to proceed with these wifi credentials - "
                        f"{ssid}:{printed_password} (Y/n)?"
                )
                use_cached = use_cached == '' or use_cached == 'y' or use_cached == 'Y'
                if use_cached:
                    self._file_explorer.put(WIFI_CONFIG_PATH)
                    return True
            wifi_config = {
                SSID_KEY: input("WiFi SSID: "),
                PASSWORD_KEY: getpass.getpass("Wifi password: "),
            }
            with open(WIFI_CONFIG_PATH, 'w') as f:
                json.dump(wifi_config, f)
            self._file_explorer.put(WIFI_CONFIG_PATH)
            return True
        except KeyboardInterrupt:
            print(f"Skipping! You can change {WIFI_CONFIG_PATH} on the device after installation!")
        return False

    def _query_user_for_webrepl_creation(self):
        """
        Ask the user for new webrepl credentials.
        """
        LOG.info("Getting webREPL credentials")
        try:
            if os.path.exists(WEBREPL_CONFIG_PATH):
                self._file_explorer.put(WEBREPL_CONFIG_PATH)
                return True
            webrepl_pass = getpass.getpass('Create WiFi console password: ')
            with open(WEBREPL_CONFIG_PATH, 'w') as f:
                f.write("PASS = '{}'\n".format(webrepl_pass))
            self._file_explorer.put(WEBREPL_CONFIG_PATH)
            return True
        except KeyboardInterrupt:
            return False

    def _install_packages(
            self,
            packages: List[str],
            reboot_timeout=60,
            wifi_connect_timeout=60,
    ):
        """
        Install packages required by antenny.
        """
        LOG.info(f"Installing {len(packages)} packages.")
        try:
            LOG.info("Resetting the device in order to trigger boot.py + WiFi connection logic.")
            self._file_explorer.exec("import sys")
            self._file_explorer.exec("sys.exit()")
        except Exception as e:
            LOG.critical(f"Unable to reboot the device! {e}")
            return False

        try:
            self._file_explorer.exec("from boot import Connection")
            LOG.info(f"Connecting the device to WiFi (this can take up to {wifi_connect_timeout} "
                     "seconds in some cases)")
            self._file_explorer.exec_raw("Connection()", timeout=wifi_connect_timeout)
            LOG.info("connected!")
        except Exception as e:
            LOG.warning(f"Unable to create a WiFi connection, please check wifi_config.json: {e}")
            return False

        try:
            start = time.time()
            while (time.time() - start) < reboot_timeout:
                try:
                    self._file_explorer.exec("import upip")
                    break
                except PyboardError:
                    continue
            for package in packages:
                LOG.info(f"Installing {package}")
                try:
                    t1 = time.time()
                    self._file_explorer.exec_raw(f"upip.install('{package}')", timeout=30)
                    elapsed = time.time() - t1
                    if elapsed < .5:
                        LOG.warning("Package installed too quickly, retrying")
                        self._file_explorer.exec_raw(f"upip.install('{package}')", timeout=30)
                except Exception as e:
                    print("Issue with insalling: {}".format(e))
        except:
            LOG.warning("Unable to install packages, please double check internet connectivity!")
            return False
        return True

    def install(
            self,
            package_install_retry: int = 3,
            only_core_reinstall: bool = False,
    ):
        """
        Perform the antenny installation.
        """
        self._clean_files(ignore_lib=only_core_reinstall)
        if not only_core_reinstall:
            self._put_library_files_on_device()
        self._put_antenny_files_on_device()
        has_wifi = self._query_user_for_wifi_credentials()
        has_web_repl = self._query_user_for_webrepl_creation()
        if has_wifi and not only_core_reinstall:
            num_retries = 0
            packages_installed = False
            while not packages_installed:
                try:
                    packages_installed = self._install_packages(PACKAGES_TO_INSTALL)
                except:
                    pass
                num_retries += 1
                if num_retries > package_install_retry:
                    raise RuntimeError(
                        "Some packages weren't installed. To fix this, please run `import upip; "
                        "upip.install('logging')` from the REPL after you have successfully "
                        "connected to WiFi."
                    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-c",
            "--core_install",
            action="store_true",
            help="Install only core antenny code, no libraries"
    )
    parser.add_argument(
            'serial_path',
            help='Path to the ESP serial device',
            type=str,
    )
    args = parser.parse_args()
    LOG.info(f"Connecting to the device at {args.serial_path}")
    installer = AntennyInstaller(args.serial_path)
    LOG.info("Connected, welcome to the Antenny installer!")
    confirm = input(
            f"Are you sure you want to erase all files on the device at {args.serial_path}? ("
            "y/N) "
    ).strip().lower() == 'y'
    if not confirm:
        print("Exiting installer; please backup existing files before running the installer!")
        sys.exit(0)
    installer.install(only_core_reinstall=args.core_install)
    LOG.info("Installation complete!")
