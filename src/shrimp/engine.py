import gpiozero
import RPi.GPIO
import dataclasses
import config
import typing
import logging
logger = logging.getLogger(__name__)




@dataclasses.dataclass
class Engine:
    by_name: typing.ClassVar[dict[str, 'Engine']] = {}

    name: str
    gpios: list[int]
    motor: gpiozero.PhaseEnableMotor = dataclasses.field(init=False)

    def __post_init__(self):
        Engine.by_name[self.name] = self
        RPi.GPIO.setmode(RPi.GPIO.BCM)
        for gpio in self.gpios:
            RPi.GPIO.setup(int(gpio), RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_DOWN)
            RPi.GPIO.setup(int(gpio), RPi.GPIO.OUT)
        self.motor = gpiozero.PhaseEnableMotor(*self.gpios)
        logger.debug(f'setup done for engine {self.name}')

