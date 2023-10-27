'''
websocket that receives command from the shrimp station and relays them to motors.
'''
import json
import mergedeep
import logging
logger = logging.getLogger(__name__)
import flask_socketio
import config
import command
import engine

#https://python-socketio.readthedocs.io/en/latest/intro.html#client-examples

class ControllerWebSocketServer(flask_socketio.Namespace):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, props in config.engines.items():
            engine.Engine(
                name=name,
                gpios=props.gpios,
                is_energy_bound=props.is_energy_bound,
            )
        for name, props in config.commands.items():
            command.Command(
                name=name,
                auto_reset=props.get('auto_reset', command.Command.auto_reset),
                actions=props.actions,
            )

    def on_connect(self):
        engines_statuses = dict()
        for eng in engine.Engine.by_name.values():
            engines_statuses[eng.name] = eng.status

        logger.info(f'new connection, engine statuses: {engines_statuses}')
        self.emit('status', dict(
            engines=engines_statuses
        ))

    def on_disconnect(self):
        logger.info(f'lost connection')

    def on_commands(self, data):
        try:
            commands_in = json.loads(data)
        except Exception as e:
            logger.error(f'while parsing commands {data}:')
            logger.exception(e)
            commands_in = []
        # what's returned to the station/remote controller
        feedback = dict()
        for command_in in commands_in:
            cmd = command.Command.by_name.get(command_in, lambda: None)
            fb = cmd()
            if fb:
                mergedeep.merge(feedback, fb, strategy=mergedeep.Strategy.REPLACE)
        return feedback

    def on_set_engine_energy_limit(self, data):
        engine_name = data.get('engine')
        limit_name = data.get('limit')
        if None in (engine_name, limit_name):
            return logger.warning(f'Missing params in on_set_engine_energy_limit: {data}')
        assert limit_name in ('min', 'max')
        eng: engine.Engine = engine.Engine.by_name.get(engine_name)
        if eng is None:
            return logger.error(f'Engine not found in command on_set_engine_energy_limit: {engine_name}')
        logger.info(f'Setting {engine_name}.{limit_name}_energy = {eng.current_energy}')
        setattr(eng, f'{limit_name}_energy', eng.current_energy)

    def on_reset_engine_energy_limit(self, data):
        engine_name = data.get('engine')
        if None in (engine_name,):
            return logger.warning(f'Missing params in reset_engine_energy_limit: {data}')
        eng: engine.Engine = engine.Engine.by_name.get(engine_name)
        if eng is None:
            return logger.error(f'Engine not found in command on_reset_engine_energy_limit: {engine_name}')
        logger.info(f'Resetting {engine_name} energy limits')
        eng.min_energy = -float('inf')
        eng.max_energy = float('inf')



def init(socketio_engine):
    socketio_engine.on_namespace(ControllerWebSocketServer('/ws/controller'))
