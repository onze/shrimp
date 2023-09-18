import gpiozero
import RPi.GPIO
import munch
import dataclasses
import config
import typing
import threading
import logging
logger = logging.getLogger(__name__)

@dataclasses.dataclass
class Command:
    by_name: typing.ClassVar[dict[str, 'Command']] = {}

    name: str
    auto_reset: bool
    actions: list
    _run: typing.Callable[[], None] = None
    _reset_timer: threading.Timer = None
    _auto_reset_actions: dict[str, typing.Callable[[], None]] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self):
        Command.by_name[self.name] = self
        for action in self.actions:
            # set to True when called, then back to false when reset
            action['is_running'] = False
            action.setdefault('args', munch.Munch())

    def __call__(self):
        if self._run is None:
            def self_run():
                # {action name: reset callback}
                auto_reset_actions = self._auto_reset_actions.copy()
                for action in self.actions:
                    if action.callback == 'break':
                        action.is_running = True
                        import pdb;pdb.set_trace()
                        action.is_running = False
                    try:
                        engine: Engine = Engine.by_name.get(action.engine)
                        if engine is None:
                            raise Exception(f'engine not found: {action.engine}')
                        callback = getattr(engine.motor, action.callback, None)
                        if callback is None:
                            raise Exception(f'callback not found in engine {action.engine}: {action.callback}')

                        def reset():
                            logger.debug(f'auto resetting command {self.name} / action {action.name}')
                            engine.motor.stop()
                            action.is_running = False

                        logger.debug(f'calling command {self.name} / action {action.name}: {action.engine}->{action.callback}(**{action.args.toDict()})')
                        callback(**action.args)
                        action.is_running = True
                        auto_reset_actions[action.name] = reset
                    except Exception as e:
                        logger.error(f'In command {self.name} / action {action.name}:')
                        logger.exception(e)
                self._auto_reset_actions = auto_reset_actions

                if self.auto_reset:
                    if self._reset_timer is not None:
                        self._reset_timer.cancel()
                        self._reset_timer = None
                    self._reset_timer = threading.Timer(
                        interval=config.commander.command_reset_delay_ms/1000.,
                        function=self._do_auto_reset,
                    )
                    self._reset_timer.start()
            self._run = self_run
        return self._run()

    def _do_auto_reset(self):
        if not self.auto_reset:
            return
        auto_reset_actions = self._auto_reset_actions.copy()
        self._auto_reset_actions.clear()
        for action_name, cb in auto_reset_actions.items():
            try:
                cb()
            except Exception as e:
                logger.error(f'While resetting action {action_name}:')
                logger.exception(e)


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

