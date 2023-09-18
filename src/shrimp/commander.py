'''
websocket that receives command from the shrimp station and relays them to motors.
'''
import json
import logging
logger = logging.getLogger(__name__)
import flask_socketio
import config
import engine

#https://python-socketio.readthedocs.io/en/latest/intro.html#client-examples

class ControllerWebSocketServer(flask_socketio.Namespace):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, props in config.engines.items():
            engine.Engine(
                name=name,
                gpios=props.gpios,
            )
        for name, props in config.commands.items():
            engine.Command(
                name=name,
                auto_reset=props.get('auto_reset', False),
                actions=props.actions,
            )

    def on_connect(self):
        logger.info(f'new connection')

    def on_disconnect(self):
        logger.info(f'lost connection')

    def on_commands(self, data):
        try:
            commands_in = json.loads(data)
        except Exception as e:
            logger.error(f'while parsing commands {data}:')
            logger.exception(e)
        # flask_socketio.emit('commands', data)
        for command_in in commands_in:
            command = engine.Command.by_name.get(command_in, lambda: None)
            command()

def init(socketio_engine):
    socketio_engine.on_namespace(ControllerWebSocketServer('/ws/controller'))
