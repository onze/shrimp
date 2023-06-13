import config
import logging
logger = logging.getLogger(__name__)
import api
import flask_socketio


class ControllerWebSocketServer(flask_socketio.Namespace):
    def on_connect(self):
        logger.info(f'new connection')

    def on_disconnect(self):
        logger.info(f'lost connection')

    def on_commands(self, data):
        logger.info(f'commands: {data}')
        # flask_socketio.emit('commands', data)


# flask app init
socketio = flask_socketio.SocketIO(
    logger=config.server.websocket.enable_logging,
    engineio_logger=config.server.websocket.enable_engine_logging,
)
socketio.on_namespace(ControllerWebSocketServer('/ws/controller'))
socketio.init_app(api.app)
