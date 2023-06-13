'''
REST API and websockets setup.
'''
import flask
import config
import os.path
import videofeed_manager
import flask_socketio
import logging
logger = logging.getLogger(__name__)

THIS_DIR = os.path.dirname(__file__)
template_folder=os.path.abspath(f'{THIS_DIR}/../templates')
logger.debug(f'template_folder={template_folder}')

app = flask.Flask('shrimp_station')
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# flask app init
socketio_engine = flask_socketio.SocketIO(
    app=app,
    logger=config.server.websocket.enable_logging,
    engineio_logger=config.server.websocket.enable_engine_logging,
)

def serve():
    socketio_engine.run(
        app,
        host=config.server.hostname,
        port=config.server.port,
        debug=config.server.debug,
    )

@app.route("/")
def get_root():
    context = dict(
        SERVER_URL= f'{config.server.hostname}:{config.server.port}',
        #SERVER_SOCKET= f'ws://{config.server.hostname}:{config.server.websocket.commands_port}',
    )
    return flask.render_template(
        './index.html',
        **context
    )


videofeed_managers = []


@app.route('/videofeed/start')
def get_videofeed_start():
    while videofeed_managers:
        try:
            videofeed_managers.pop().stop()
        except Exception as e:
            logger.error(f'while stopping VideoFeedManager: {e}')

    vfm = videofeed_manager.VideoFeedManager()
    try:
        vfm.start()
    except Exception as e:
        logger.exception(e)
        return flask.jsonify(dict(code=1, error=str(e)))
    videofeed_managers.append(vfm)
    return flask.jsonify(dict(code=0, videofeed_url=vfm.websocket_url))
