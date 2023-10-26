import logging
logger = logging.getLogger(__name__)
# socketIO server lib (phone -> station)
import flask_socketio
# socketIO client lib (station -> shrimp)
import socketio
import config


class ControllerWebSocketServer(flask_socketio.Namespace):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shrimp_sio = None
        self.shrimp_controller_ns = '/ws/controller'

    def on_connect(self):
        logger.info(f'new inbound connection. Connecting to shrimp controller...')
        self.shrimp_sio = socketio.Client()
        shrimp_controller_url = f'http://{config.shrimp.hostname}:{config.shrimp.web_api_port}'

        @self.shrimp_sio.on('status')
        def shrimp_on_status(data):
            self.shrimp_sio.emit('shrimp_status', data)

        @self.shrimp_sio.event
        def connect():
            logger.info(f'connected to shrimp at {shrimp_controller_url}')
        @self.shrimp_sio.event
        def connect_error(data):
            logger.info(f'could not connect to shrimp at {shrimp_controller_url}: {data}')

        @self.shrimp_sio.event
        def disconnect():
            logger.info(f'disconnected from shrimp at {shrimp_controller_url}')

        self.shrimp_sio.connect(
            url=shrimp_controller_url,
            namespaces=[self.shrimp_controller_ns],
        )
        if not self.shrimp_sio.connected:
            logger.error('not connected to shrimp at {shrimp_controller_url}')

        @self.shrimp_sio.on('*')
        def shrimp_on_event(data):
            logger.info(f'unhandled shrimp controller event: {data}')


    def on_disconnect(self):
        logger.info(f'lost inbound connection')

    def on_commands(self, data):
        logger.info(f'relaying commands: {data}')
        self.shrimp_sio.emit('commands', data, namespace=self.shrimp_controller_ns)

    def on_set_engine_energy_limit(self, data):
        logger.info(f'relaying set_engine_energy_limit: {data}')
        self.shrimp_sio.emit('set_engine_energy_limit', data, namespace=self.shrimp_controller_ns)

    def on_reset_engine_energy_limit(self, data):
        logger.info(f'relaying reset_engine_energy_limit: {data}')
        self.shrimp_sio.emit('reset_engine_energy_limit', data, namespace=self.shrimp_controller_ns)


def init(socketio_engine):
    socketio_engine.on_namespace(ControllerWebSocketServer('/ws/controller'))
