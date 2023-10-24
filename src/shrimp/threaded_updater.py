import threading
import typing
import dataclasses
import time

@dataclasses.dataclass
class CallbackMetadata:
    t0: float = 0.
    last_t: float = 0.

    def __post_init__(self):
        self.t0 = time.time()
        self.last_t = self.t0

    @property
    def elapsed_since_created(self) -> float:
        '''time since the callback was registered, in seconds.'''
        return time.time() - self.t0

    @property
    def elapsed_since_last_time(self) -> float:
        '''time since the call to this same function, in seconds.'''
        now = time.time()
        value = now - self.last_t
        self.last_t = now
        return value

class ThreadedUpdater:
    def __init__(self):
        # in Hz (doesn't account for callback processing time)
        self.run_freq = 12.
        self.callbacks: dict[typing.Callable[[CallbackMetadata], None], ] = {}
        self.thread = threading.Thread(target=self.threaded_run)
        self.thread.start()

    def add_callback(self, cb):
        self.callbacks[cb] = CallbackMetadata(t0=time.time())

    def remove_callback(self, cb):
        self.callbacks.pop(cb, None)

    def threaded_run(self):
        while True:
            for callback, meta in self.callbacks.copy().items():
                if callback in self.callbacks:
                    callback(meta)
            time.sleep(1./self.run_freq)
