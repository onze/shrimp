import gpiozero
import RPi.GPIO
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
    total_energy: float = 0
    _min_energy: float = -float('inf')
    _max_energy: float = float('inf')

    class_threaded_updater: typing.ClassVar[threaded_updater.ThreadedUpdater] = threaded_updater.ThreadedUpdater()

    def __post_init__(self):
        Engine.by_name[self.name] = self
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        for gpio in self.gpios:
            RPi.GPIO.setup(int(gpio), RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
            RPi.GPIO.setup(int(gpio), RPi.GPIO.OUT)
        self.motor = gpiozero.PhaseEnableMotor(*self.gpios)
        self._min_energy = local_storage.load(f'{self.name}.min_energy', self._min_energy)
        self._max_energy = local_storage.load(f'{self.name}.max_energy', self._max_energy)
        logger.debug(f'setup done for engine {self.name}')

    def run_action(self, action_name, **action_kwargs):
        callback = getattr(self.motor, action_name, None)
        if callback is None:
            raise Exception(f'callback not found in engine {self.name}: {action_name}')
        logger.debug(f'calling {self.name}->{action_name}(**{action_kwargs})')
        callback(**action_kwargs)
        Engine.class_threaded_updater.add_callback(self.aggregate_energy)

    def stop(self):
        self.motor.stop()
        Engine.class_threaded_updater.remove_callback(self.aggregate_energy)

    def aggregate_energy(self, meta: threaded_updater.CallbackMetadata):
        energy_delta = self.motor.value*meta.elapsed_since_last_time

        energy_based_stop = False
        # check lower bound
        if (energy_delta < 0
            and  self.min_energy is not None
            and self.total_energy - energy_delta <= self.min_energy
        ):
            logger.info(f'Lower-bound energy-based engine stop for {self.name} @ {self.total_energy}')
            energy_based_stop = True

        # check higher bound
        if (energy_delta > 0
            and self.max_energy is not None and
            self.total_energy + energy_delta >= self.max_energy
        ):
            logger.info(f'Higher-bound energy-based engine stop for {self.name} @ {self.total_energy}')
            energy_based_stop = True

        if energy_based_stop:
            self.stop()
            return

        self.total_energy += energy_delta
        logger.debug(f'Energy for {self.name}:{self.total_energy}')

        if self.motor.value == 0:
            Engine.class_threaded_updater.remove_callback(self.aggregate_energy)

    @property
    def min_energy(self):
        return self._min_energy

    @min_energy.setter
    def min_energy(self, value):
        self._min_energy = value
        local_storage.save(f'{self.name}.min_energy', self._min_energy)

    @property
    def max_energy(self):
        return self._max_energy

    @max_energy.setter
    def max_energy(self, value):
        self._max_energy = value
        local_storage.save(f'{self.name}.max_energy', self._max_energy)



