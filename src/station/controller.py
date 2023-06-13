import logging
logger = logging.getLogger(__name__)
import flask_socketio


class ControllerWebSocketServer(flask_socketio.Namespace):
    def on_connect(self):
        logger.info(f'new connection')

    def on_disconnect(self):
        logger.info(f'lost connection')

    def on_commands(self, data):
        logger.info(f'commands: {data}')
        # flask_socketio.emit('commands', data)


def init(socketio_engine):
    socketio_engine.on_namespace(ControllerWebSocketServer('/ws/controller'))
