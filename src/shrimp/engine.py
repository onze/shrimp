import gpiozero
import dataclasses
import config
import local_storage
import threaded_updater
import typing
import logging
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Engine:
    by_name: typing.ClassVar[dict[str, 'Engine']] = {}

    name: str
    gpios: list[int]
    motor: gpiozero.PhaseEnableMotor = dataclasses.field(init=False)

    # energy (value*dt) since started
    is_energy_bound: bool = False
    _current_energy: float = 0
    _min_energy: float = -float('inf')
    _max_energy: float = float('inf')
    # set to True whenever we'd move past a limit
    has_reached_energy_limit: bool = False

    class_threaded_updater: typing.ClassVar[threaded_updater.ThreadedUpdater] = threaded_updater.ThreadedUpdater()

    def __post_init__(self):
        import RPi.GPIO
        Engine.by_name[self.name] = self
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        for gpio in self.gpios:
            RPi.GPIO.setup(int(gpio), RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
            RPi.GPIO.setup(int(gpio), RPi.GPIO.OUT)
        self.motor = gpiozero.PhaseEnableMotor(*self.gpios)
        if self.is_energy_bound:
            self._current_energy = local_storage.load(f'{self.name}.current_energy', self._current_energy)
            self._min_energy = local_storage.load(f'{self.name}.min_energy', self._min_energy)
            self._max_energy = local_storage.load(f'{self.name}.max_energy', self._max_energy)
            logger.debug(f'setup done for engine {self.name} (∑∈[{self.min_energy}, {self.max_energy}])')
        else:
            logger.debug(f'setup done for engine {self.name}')

    def run_action(self, action_name, **action_kwargs):
        callback = getattr(self.motor, action_name, None)
        if callback is None:
            raise Exception(f'callback not found in engine {self.name}: {action_name}')
        logger.debug(f'calling {self.name}->{action_name}(**{action_kwargs})')
        callback(**action_kwargs)
        if self.is_energy_bound:
            Engine.class_threaded_updater.add_callback(self.aggregate_energy)

    def stop(self):
        self.motor.stop()
        local_storage.save(f'{self.name}.current_energy', self._current_energy)
        if self.is_energy_bound:
            Engine.class_threaded_updater.remove_callback(self.aggregate_energy)

    def aggregate_energy(self, meta: threaded_updater.CallbackMetadata):
        assert self.is_energy_bound
        energy_delta = self.motor.value*meta.elapsed_since_last_time

        self.has_reached_energy_limit = False
        # check lower bound
        if (energy_delta < 0
            and  self.min_energy is not None
            and self.current_energy - energy_delta <= self.min_energy
        ):
            logger.info(f'Lower-bound energy-based engine stop for {self.name} @ {self.current_energy}')
            self.has_reached_energy_limit = True

        # check higher bound
        if (energy_delta > 0
            and self.max_energy is not None and
            self.current_energy + energy_delta >= self.max_energy
        ):
            logger.info(f'Higher-bound energy-based engine stop for {self.name} @ {self.current_energy}')
            self.has_reached_energy_limit = True

        if self.has_reached_energy_limit:
            self.stop()
            return

        self._current_energy += energy_delta
        logger.debug(f'Energy for {self.name}:{self._current_energy}')

        if self.motor.value == 0:
            Engine.class_threaded_updater.remove_callback(self.aggregate_energy)

    @property
    def current_energy(self):
        return self._current_energy

    @property
    def min_energy(self):
        return self._min_energy if self.is_energy_bound else -float('inf')

    @min_energy.setter
    def min_energy(self, value):
        if not self.is_energy_bound:
            return
        self._min_energy = value
        local_storage.save(f'{self.name}.min_energy', self._min_energy)

    @property
    def max_energy(self):
        return self._max_energy if self.is_energy_bound else float('inf')

    @max_energy.setter
    def max_energy(self, value):
        if not self.is_energy_bound:
            return
        self._max_energy = value
        local_storage.save(f'{self.name}.max_energy', self._max_energy)

    @property
    def status(self):
        if self.is_energy_bound:
            return dict(
                # within [0,1], can be NaN when limits aren't set.
                energy_percentage=(self.current_energy - self.min_energy) / (self.max_energy - self.min_energy),
                has_reached_energy_limit=self.has_reached_energy_limit,
            )
        return {}



