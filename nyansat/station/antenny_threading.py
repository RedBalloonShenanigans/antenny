import logging
import time

_DEFAULT_DELAY = 0.01
LOG = logging.getLogger('antenny.common')

_in_micro_python = 'machine' in globals()
try:
    import _thread
except ImportError:
    pass


class MPThread(object):
    """
    MicroPython threading wrapper
    """

    def __init__(
            self,
            target=None,
            args=None,
    ):
        self._task = None
        self._target = target
        self._args = args
        self.running = False

    def run(self):
        raise NotImplementedError

    def start(self):
        self.running = True
        self._task = _thread.start_new_thread(self.run, ())

    def join(self):
        pass

    def stop(self):
        self.running = False


class MPEmpty(Exception):
    """
    Replacement for queue.Empty
    """
    pass


try:
    from threading import Thread
    from queue import Queue, Empty

    Empty = Empty
except:
    Empty = MPEmpty
    Thread = MPThread


class VanillaThread(Thread):

    def __init__(
            self,
            target=None,
            args=None,
    ):
        super(VanillaThread, self).__init__(target=target, args=args)
        self.running = False

    def start(self):
        self.running = True
        super(VanillaThread, self).start()

    def join(self):
        super(VanillaThread, self).join()

    def stop(self):
        self.running = False
        self.join()


class MPQueue(object):

    def __init__(self):
        self._lock = _thread.allocate_lock()
        self._queue = []

    def get(
            self,
            timeout=None,
    ):
        if timeout is None:
            while True:
                try:
                    with self._lock:
                        return self._queue.pop()
                except IndexError:
                    pass
        delay = 0
        item = None
        while delay < timeout:
            try:
                with self._lock:
                    item = self._queue.pop()
            except IndexError:
                pass
            time.sleep(_DEFAULT_DELAY)
            delay += _DEFAULT_DELAY
        if item is None:
            raise Empty
        return item

    def put(self, item):
        with self._lock:
            self._queue.append(item)


try:
    import threading

    Thread = VanillaThread
except ImportError:
    Queue = MPQueue
