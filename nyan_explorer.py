from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from nyan_pyboard import NyanPyboard

class NyanExplorer(MpFileExplorer, NyanPyboard):
    """Wrapper for MpFileExplorer that includes the new NyanPyboard functionality."""
    pass

class NyanExplorerCaching(MpFileExplorerCaching, NyanPyboard):
    """Wrapper for MpFileExplorerCaching that includes the new NyanPyboard functionality."""
    pass

