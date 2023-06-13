import flask
import config
import os.path
import logging
logger = logging.getLogger(__name__)

THIS_DIR = os.path.dirname(__file__)
template_folder=os.path.abspath(f'{THIS_DIR}/../templates')
logger.debug(f'template_folder={template_folder}')

app = flask.Flask(
    __name__,
    #template_folder='templates',
)
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route("/")
def get_root():
    context = dict(
        SERVER_SOCKET= f'ws://{config.server.hostname}:{config.server.websocket.port}'
    )
    return flask.render_template(
        './index.html',
        **context
    )
