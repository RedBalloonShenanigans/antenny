"""
Antenny installer
"""
import argparse
import getpass
import json
import os
import sys
import time
import logging

from mp.mpfexp import RemoteIOError, ConError
from mp.pyboard import PyboardError
from typing import List

from nyansat.host.exceptions import AntennyFilesystemException, AntennyHardwareException, AntennyInstallationException
from nyansat.host.mp_extensions import AntennyMpFileExplorer

PASSWORD_KEY = 'key'
SSID_KEY = 'ssid'
WIFI_CONFIG_PATH = 'configs/wifi_config.json'
WEBREPL_CONFIG_PATH = 'webrepl_cfg.py'
REPO_NAME = 'antenny'
UP_ONE_DIRECTORY = '..'
STATION_CODE_RELATIVE_PATH = 'nyansat/station'

PACKAGES_TO_INSTALL = [
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

    def connect(
            self,
            num_connection_retries=3
    ):
        """
        Connect to the antenny device, update the FileExplorer.
        """
        for retry_count in range(num_connection_retries):
            try:
                self._file_explorer = AntennyMpFileExplorer(f'ser:{self._serial_path}')
                LOG.info("Connected to ground station")
                break
            except ConError as e:
                if retry_count < num_connection_retries-1:
                    LOG.warning(f"Retrying to connect to the ground station device, attempt "
                            f"{retry_count}/{num_connection_retries}")
                else:
                    LOG.error(f"Failed to connect to Antenny board", exc_info=True)
                    raise AntennyHardwareException("Failed to connect to Antenny board")

    def _clean_files(
            self,
            in_subdirectory: bool = False,
            ignore_lib: bool = False,
            ignore_configs: bool = False,
            components: list = None
    ):
        """
        Clean up the existing files on the device.
        """
        if not in_subdirectory:
            LOG.info("Entering root")
            self._file_explorer.cd("/")
        files = self._file_explorer.ls()
        libs = set([os.path.basename(f) for f in LIBRARY_FILES])
        if not in_subdirectory:
            LOG.info(f"Cleaning {len(files)} file(s) on the device")
        for file_ in files:
            if ignore_lib and not in_subdirectory and (os.path.basename(file_) in libs or file_ == "lib"):
                continue

            if ignore_configs and file_ == "configs":
                continue

            if self._file_explorer.isdir(file_):
                if components is not None and file_ not in components:
                    continue
                LOG.info("Attempting to clean directory {}".format(file_))
                self._file_explorer.cd(file_)
                self._clean_files(in_subdirectory=True)

            LOG.info("Remvoing file {}".format(file_))
            self._file_explorer.rm(file_)

        if in_subdirectory:
            self._file_explorer.cd('..')
        else:
            LOG.info("Done cleaning FS")

    def _recursive_put_files(
            self,
            sub_directory=None,
            ignore_configs=False,
            components: list = None
    ):
        """
        Recursively copy all files from a starting directory to the pyboard.
        """
        current_path = os.path.basename(os.getcwd())
        if components is not None and current_path not in components + ["station"]:
            return
        LOG.info("Copying files from the directory {}".format(current_path))
        for path_ in os.listdir():
            if path_.startswith('.'):
                LOG.warning("Dotfile found, skipping file {}".format(path_))
                continue

            if path_.startswith('__'):
                LOG.warning("Python reserved file found, skipping file {}".format(path_))
                continue

            if ignore_configs and path_ == "configs":
                continue

            if sub_directory is not None:
                path_ = os.path.join(sub_directory, path_)

            filename_ = os.path.basename(path_)

            if os.path.isdir(filename_):
                if components is None or filename_ in components:
                    try:
                        self._file_explorer.md(path_)
                    except RemoteIOError:
                        LOG.error("Failed to make directory {} on antenny board, see mpf error information for more details"
                                  "".format(path_), exc_info=True)
                        raise AntennyFilesystemException("Failed to make directory {} on antenny board".format(path_))
                    except PyboardError:
                        LOG.error("A problem was detected with the antenny board while trying to put files", exc_info=True)
                        raise AntennyHardwareException("A problem was detected with the antenny board while trying to put files")

                    os.chdir(filename_)
                    self._recursive_put_files(
                            sub_directory=path_,
                    )
            else:
                try:
                    if sub_directory is not None:
                        LOG.info("Adding file {}".format(path_))
                        self._file_explorer.put(filename_, path_)
                    else:
                        self._file_explorer.put(filename_)
                except Exception as e:
                    LOG.error("Failed to put file {}".format(path_))
                    raise AntennyFilesystemException("Could not find file {}".format(path_))
        if sub_directory is not None:
                os.chdir(UP_ONE_DIRECTORY)

    def _put_antenny_files_on_device(self, ignore_configs=False, components: list = None):
        """
        Copy antenny source files to the device
        """
        curr_working_dir = os.getcwd()
        LOG.info("Executing file copy from {}".format(curr_working_dir))
        if os.path.basename(curr_working_dir) != REPO_NAME:
            if REPO_NAME not in curr_working_dir:
                raise RuntimeError(
                    "Cannot find the antenny repository, please run this from the root "
                    "of that directory."
                )
            # walk back up the directory tree, it's in the current working dir
            while os.path.basename(os.getcwd()) != REPO_NAME:
                os.chdir(UP_ONE_DIRECTORY)
        os.chdir(STATION_CODE_RELATIVE_PATH)
        self._recursive_put_files(ignore_configs=ignore_configs, components=components)

    #TODO: Should not have to edit this script to add more libraries, seperate station and host libraries. 
    def _put_library_files_on_device(self):
        """
        Copy required antenny library files.
        """
        LOG.info(f"Putting {len(LIBRARY_FILES)} library files on the device.")
        for file_ in LIBRARY_FILES:
            try:
                LOG.info("Putting {} onto device".format(file_))
                start = time.time()
                self._file_explorer.put(file_, os.path.basename(file_))
                LOG.info("Took {} seconds".format(time.time()-start))
            except Exception as e:
                LOG.error("Failed to put library file {}".format(file_))
                raise AntennyInstallationException("Failed to install libraryy file {}".format(file_))
        LOG.info("Library files installed")
        return True

    def _query_user_for_wifi_credentials(self):
        """
        Optional: Query user for their login credentials (wifi & webrepl)
        """
        LOG.info("Gathering WiFi credentials")
        use_cached = False
        if os.path.exists(WIFI_CONFIG_PATH):
            with open(WIFI_CONFIG_PATH, 'r') as f:
                wifi_config = json.load(f)
            ssid, password = wifi_config.get(SSID_KEY, ''), wifi_config.get(PASSWORD_KEY, '')
            printed_password = '*' * len(password)
            use_cached = input(
                    "Do you want to proceed with these wifi credentials - "
                    "{}:{} (Y/n)?".format(ssid, printed_password).strip().lower() in ("y", "")
            )
        if use_cached:
            self._file_explorer.put(WIFI_CONFIG_PATH)
            return True
        else:
            LOG.info("Please enter WiFi credentials, or use [ctrl-C] to exit.")
            LOG.info("Wifi credentials can be changed after setup by editing {} through the MPFShell".format(WIFI_CONFIG_PATH))
            try:
                wifi_config = {
                    SSID_KEY: input("WiFi SSID: "),
                    PASSWORD_KEY: getpass.getpass("Wifi password: "),
                }
            except KeyboardInterrupt:
                LOG.warning("No WFi selected, dependencies will not be installed")
                return False
            with open(WIFI_CONFIG_PATH, 'w') as f:
                json.dump(wifi_config, f)
            self._file_explorer.put(WIFI_CONFIG_PATH)
            return True

    def _query_user_for_webrepl_creation(self):
        """
        Ask the user for new webrepl credentials.
        """
        LOG.info("Getting webREPL credentials")
        if os.path.exists(WEBREPL_CONFIG_PATH):
            self._file_explorer.put(WEBREPL_CONFIG_PATH)
            return True
        else:
            try:
                webrepl_pass = getpass.getpass('Create WiFi console password: ')
            except KeyboardInterrupt:
                LOG.warning("Skipping WiFi console creation")
                return False
            with open(WEBREPL_CONFIG_PATH, 'w') as f:
                f.write("PASS = '{}'\n".format(webrepl_pass))
            self._file_explorer.put(WEBREPL_CONFIG_PATH)
            return True

    def _install_upip(self, timeout=0):
        start = time.time()
        while True:
            try:
                self._file_explorer.exec("import upip")
                return True
            except PyboardError:
                LOG.warning("Failed to import upip")
                pass
            if (time.time() - start) > timeout:
                LOG.error("Importing upip has timed out!")
                return False
            else:
                LOG.warning("Retrying")

    def _install_package(self, package, timeout=0.0):
        start = time.time()
        while True:
            try:
                self._file_explorer.exec_raw("upip.install('{}')".format(package), timeout=30)
                try:
                    self._file_explorer.exec_raw("import {}".format(package))
                    LOG.info("Successfully installed and imported {}".format(package))
                    return True
                except Exception as e:
                    LOG.error("Failed to import package {} after installation".format(package))
                    raise
            except Exception as e:
                LOG.warning("Failed to import {}".format(package))
            if (time.time() - start) > timeout:
                LOG.error("Importing {} has timed out!".format(package))
                raise AntennyInstallationException
            else:
                LOG.warning("Retrying")

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
        if len(packages) == 0:
            return True
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
            self._install_upip(timeout=reboot_timeout)
            for package in packages:
                LOG.info(f"Installing {package}")
                self._install_package(package, timeout=.5)
        except:
            LOG.warning("Unable to install packages, please double check internet connectivity!")
            return False
        return True

    def install(
            self,
            package_install_retry: int = 3,
            ignore_lib: bool = False,
            ignore_configs: bool = False,
            components: list = None
    ):
        """
        Perform the antenny installation.
        """

        self._clean_files(ignore_lib=ignore_lib, ignore_configs=ignore_configs, components=components)
        if not ignore_lib and components is None:
            self._put_library_files_on_device()
        self._put_antenny_files_on_device(ignore_configs=ignore_configs, components=components)
        has_wifi = self._query_user_for_wifi_credentials()
        has_web_repl = self._query_user_for_webrepl_creation()
        if has_wifi and not ignore_lib:
            num_retries = 0
            packages_installed = False
            while not packages_installed:
                try:
                    packages_installed = self._install_packages(PACKAGES_TO_INSTALL)
                    return True
                except:
                    LOG.warning("Failed to install packages")
                num_retries += 1
                if num_retries > package_install_retry:
                    raise AntennyInstallationException(
                        "Some packages weren't installed. To fix this, please run `import upip; "
                        "upip.install('logging')` from the REPL after you have successfully "
                        "connected to WiFi."
                    )
                else:
                    LOG.warning("Retrying")
        else:
            LOG.error("WiFi is required to install external packages, please enter your WiFi credentials and try "
                      "again.")
            return False


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
    installer.connect()
    LOG.info("Connected, welcome to the Antenny installer!")
    ignore_configs = input("Do you want to keep the configs on the device? (Y/n)").strip().lower() in ('y', '')
    fresh_install = input("Do you want to do an installation of all components?(Y/n)").strip().lower() in ('y', '')
    if fresh_install:
        confirm = input(f"Are you sure you want to erase all files on the device? (y/N) ").strip().lower() == 'y'
        if not confirm:
            print("Exiting installer; please backup existing files before running the installer!")
            sys.exit(0)
        installer.install(ignore_lib=args.core_install, ignore_configs=ignore_configs)
    else:
        done = False
        components = []
        while not done:
            components.append(input("Name a component you wish to install: ").strip().lower())
            done = input("Do you wish to install more? (y/N)").strip().lower() in ("n", "")
            if not ignore_configs:
                components.append("configs")
        installer.install(ignore_lib=True, ignore_configs=ignore_configs, components=components)
    LOG.info("Installation complete!")
