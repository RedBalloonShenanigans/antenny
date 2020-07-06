from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from nyan_pyboard import NyanPyboard

class NyanExplorer(MpFileExplorer, NyanPyboard):
    pass

class NyanExplorerCaching(MpFileExplorerCaching, NyanPyboard):
    pass

