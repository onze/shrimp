import logging
import os

logger = logging.getLogger(__name__)
import time
import flask
import config

import api
import subprocess
import threading
import typing

# side process that does the streaming
global streaming_process
streaming_process: typing.Optional[subprocess.Popen] = None
global healthcheck_thread
healthcheck_thread: typing.Optional[threading.Thread] = None


def log_file():
    return f'{config.tmp_dir}/logs/{config.videofeed_out.streaming_binary}.out'
def err_file():
    return f'{config.tmp_dir}/logs/{config.videofeed_out.streaming_binary}.err'


@api.app.route('/videofeed/start')
def get_videofeed_start():
    global streaming_process
    if streaming_process is not None:
        return flask.jsonify(dict(
            code=0,
            reason='already started',
            feed_hostname=config.server.hostname,
            feed_port=config.videofeed_out.port,
        ))

    width = flask.request.args.get('width', default=400, type=int)
    height = flask.request.args.get('height', default=300, type=int)
    fps = flask.request.args.get('fps', default=24, type=int)

    try:
        os.system(f'/usr/bin/pkill {config.videofeed_out.streaming_binary}')
    except Exception: pass

    if config.videofeed_out.streaming_binary == 'libcamera-vid':
        bin_args = [
            '/usr/bin/libcamera-vid',
            '--nopreview',
            '-t', '0', # no timeout
            '--inline', # Force PPS/SPS header with every I frame (h264 only)
            '--listen', # Listen for an incoming client before sending data
            #'--info-text', '%fps fps', # Sets the information string on the titlebar.
            '--width', str(width),
            '--height', str(height),
            '--framerate', str(fps),
            # https://en.wikipedia.org/wiki/Advanced_Video_Coding#Profiles
            '--profile', 'main',
            # not much freedom here
            # https://github.com/raspberrypi/libcamera-apps/blob/e4b2a50359e2e95ece3b33f865707ddc5dde20fa/encoder/h264_encoder.cpp#L78
            '--level', '4.2',
            '--flush', '1',
            '-o', f'tcp://0.0.0.0:{config.videofeed_out.port}'
        ]
    elif config.videofeed_out.streaming_binary == 'ffmpeg':
        bin_args = [
            'ffmpeg',
            '-r', str(fps),
            '-f', 'video4linux2',
            '-i', '/dev/video0',
            '-f', 'h264', '-preset', 'ultrafast',
            '-tune', 'zerolatency', '-x264opts', 'keyint=7',
            '-movflags', '+faststart', '-r', str(fps),
            '-fflags', 'nobuffer',
            f'tcp://0.0.0.0:{config.videofeed_out.port}?listen',
         ]
    else:
        raise Exception(f'unsupported config.videofeed_out.streaming_binary in {config}')
    streaming_process = subprocess.Popen(
        bin_args,
        bufsize=1, #line buffered
        text=True,
        universal_newlines=True,
        stdin=None,
        stdout=open(log_file(), 'wt'),
        stderr=open(err_file(), 'wt'),
        close_fds=True,
    )
    logger.info(f'Running streamer: {" ".join(streaming_process.args)}')
    # give leave it time to get ready
    # time.sleep(1.)

    global healthcheck_thread
    healthcheck_thread = threading.Thread(target=healthcheck_streamer)
    healthcheck_thread.start()

    return flask.jsonify(dict(
        code=0,
        feed_hostname=config.server.hostname,
        feed_port=config.videofeed_out.port,
    ))


def healthcheck_streamer():
    global streaming_process
    while streaming_process is not None:
        rcode = streaming_process.poll()
        if rcode is not None:
            logger.debug('Streamer relay terminated')
            global healthcheck_thread
            healthcheck_thread = None
            stop_videofeed()
            with open(log_file(), 'r') as f:
                logging.getLogger(__name__+'.streamer.out').info('\n'.join(f.readlines()))
            with open(err_file(), 'r') as f:
                logging.getLogger(__name__+'.streamer.err').error('\n'.join(f.readlines()))
            break
        time.sleep(config.server.subprocess_polling_period_ms/1000.)


@api.app.route('/videofeed/stop')
def get_videofeed_stop():
    stop_videofeed()
    return flask.jsonify(dict(code=0))


def stop_videofeed():
    global streaming_process
    if streaming_process is None:
        return
    local_streaming_process = streaming_process
    streaming_process = None
    local_streaming_process.terminate()
    try:
        local_streaming_process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        local_streaming_process.kill()
    global healthcheck_thread
    if healthcheck_thread:
        healthcheck_thread.join()
        healthcheck_thread = None
    logger.debug('streamer stopped')
