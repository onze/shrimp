import config
import dataclasses
import munch
import engine

import threading
import typing
import logging
logger = logging.getLogger(__name__)

@dataclasses.dataclass
class Command:
    by_name: typing.ClassVar[dict[str, 'Command']] = {}

    name: str
    actions: list
    auto_reset: bool = False
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
        # {action name: reset callback}
        auto_reset_actions = self._auto_reset_actions.copy()
        eng = None
        for action in self.actions:
            if action.callback == 'break':
                action.is_running = True
                import pdb;pdb.set_trace()
                action.is_running = False
            try:
                eng: engine.Engine = engine.Engine.by_name.get(action.engine)
                if eng is None:
                    raise Exception(f'engine not found: {action.engine}')

                eng.run_action(action.callback, **action.args)

                def reset():
                    logger.debug(f'auto resetting command {self.name} / action {action.name}')
                    eng.stop()
                    action.is_running = False

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

        return dict(
            engines={
                eng.name: eng.status if eng is not None else {}
            }
        )

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