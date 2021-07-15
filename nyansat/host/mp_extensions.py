import logging
import os

from mp.mpfexp import MpFileExplorer, RemoteIOError
from mp.pyboard import PyboardError

from nyansat.host.exceptions import AntennyFilesystemException

LOG = logging.Logger("mp_extensions")


def _file_does_not_exist_error(exception):
    """
    Adopted from the _was_file_not_existing functon in mpfexp.py. Removes OSError as a condition, as this will
    trigger on a "isfile=True" condition, but not if the file does not exist.
    :param exception:
    :return:
    """
    stre = str(exception)
    return any(err in stre for err in ("ENOENT", "ENODEV", "EINVAL"))


def _file_exists_error(exception):
    stre = str(exception)
    return "OSError: 20" in stre


class AntennyMpFileExplorer(MpFileExplorer):

    def isdir(self, target):
        try:
            ret = self.eval("len([item for item in uos.listdir(\"{}\")])>=0".format(os.path.join(self.pwd(), target)))
        except PyboardError as e:
            if _file_does_not_exist_error(e):
                LOG.error("The file or directory {} does not exist".format(target), exc_info=True)
                raise AntennyFilesystemException("No such directory: {}".format(self.dir))
            elif _file_exists_error(e):
                ret = False
                pass
            else:
                LOG.error("Unexpected error!", exc_info=True)
                raise e

        return ret
