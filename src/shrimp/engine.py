import gpiozero
import RPi.GPIO
import dataclasses
import config
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

    class_threaded_updater: typing.ClassVar[threaded_updater.ThreadedUpdater] = threaded_updater.ThreadedUpdater()

    def __post_init__(self):
        Engine.by_name[self.name] = self
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        for gpio in self.gpios:
            RPi.GPIO.setup(int(gpio), RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
            RPi.GPIO.setup(int(gpio), RPi.GPIO.OUT)
        self.motor = gpiozero.PhaseEnableMotor(*self.gpios)
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

    def aggregate_energy(self, meta:threaded_updater.CallbackMetadata):
        self.total_energy += self.motor.value*meta.elapsed_since_last_time
        logger.debug(f'Energy for {self.name}:{self.total_energy}')
        if self.motor.value == 0:
            Engine.class_threaded_updater.remove_callback(self.aggregate_energy)



