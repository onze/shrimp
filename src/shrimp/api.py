'''
REST API for setup setup.
'''
import flask
import config
import flask_socketio
import logging
logger = logging.getLogger(__name__)

app = flask.Flask('shrimp')

# flask app init
socketio_engine = flask_socketio.SocketIO(
    logger=config.server.websocket.enable_logging,
    engineio_logger=config.server.websocket.enable_engine_logging,
)
socketio_engine.init_app(app)


def serve():
    socketio_engine.run(
        app,
        host=config.server.hostname,
        port=config.server.port,
        debug=config.server.debug,
    )
