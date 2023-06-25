import logging
import os
import socket

logger = logging.getLogger(__name__)
import time
import socket
import threading
import subprocess
import requests
import munch
import config

class VideoFeedManager:
    '''
    Manages a pair of processes:
    - remote shrimp's ffmpeg streamer
    - local websocat call to relay the stream
    '''

    instance = None

    def __init__(self):
        if VideoFeedManager.instance:
            logger.debug('Stopping previous video feed manager...')
            VideoFeedManager.instance.stop()
            logger.debug('Stopped previous video feed manager...')
        VideoFeedManager.instance = self
        self.websocat = None
        self.healthcheck_thread = None

    @property
    def log_file(self):
        return f'{config.tmp_dir}/logs/websocat.out'
    @property
    def err_file(self):
        return f'{config.tmp_dir}/logs/websocat.err'

    def start(self, width:int, height:int, fps: int, level:str):
        # get the shrimp to start streaming
        response: requests.Response = requests.get(
            f'http://{config.shrimp.hostname}:{config.shrimp.rest_api_port}/videofeed/start',
            params=dict(width=width, height=height, fps=fps, level=level),
        )
        if not response.ok:
            raise Exception(f'{response.status_code}/{response.reason}')
        payload = munch.munchify(response.json())
        if payload.code != 0:
            raise Exception(f'Could not get camera stream up: {payload.reason}')

        try:
            os.system(f'/usr/bin/pkill websocat')
        except: pass

        feed_hostname = payload.get('feed_hostname')
        feed_port = payload.get('feed_port')
        if None in (feed_hostname, feed_port):
            raise Exception(f'Missing feed_url|feed_port from camera stream: {payload}')
        # hotfix for websocat: it doesn't seem to be able to do hostname resolution
        # so let's do it for them.
        feed_hostname = socket.gethostbyname(feed_hostname)
        feed_url = f'{feed_hostname}:{feed_port}'

        # start websocat to wrap the stream in a websocket
        self.websocat = subprocess.Popen(
            [
                '/home/onze/.local/bin/websocat',
                '--oneshot', '-b',
                f'ws-l:0.0.0.0:{config.server.videofeed_port}', # out
                f'tcp:{feed_url}', # in
            ],
            bufsize=1, #line buffered
            text=True,
            universal_newlines=True,
            stdin=None,
            stdout=open(self.log_file, 'wt'),
            stderr=open(self.err_file, 'wt'),
            close_fds=True,
        )
        logger.info(f'Started websocat relay: {" ".join(self.websocat.args)}')
        # give it time to get ready
        time.sleep(5.)

        self.websocket_url = f'ws://{config.server.hostname}:{config.server.videofeed_port}'
        # healthcheck thread that stops websocat whenever streaming has stopped
        self.healthcheck_thread = threading.Thread(target=self.healthcheck_websocat)
        self.healthcheck_thread.start()

    def healthcheck_websocat(self):
        while self.websocat is not None:
            try:
                rcode = self.websocat.poll()
            except Exception as e:
                logger.error(f'While polling websocat:')
                logger.exception(e)
                break

            if rcode is not None:
                logger.debug(f'websocat terminated ({rcode})')
                self.healthcheck_thread = None
                self.stop()
                with open(self.log_file, 'r') as f:
                    logging.getLogger(__name__+'.websocat.out').info('\n'.join(f.readlines()))
                with open(self.err_file, 'r') as f:
                    logging.getLogger(__name__+'.websocat.err').error('\n'.join(f.readlines()))
                break

            time.sleep(config.server.subprocess_polling_period_ms/1000.)

    def stop(self):
        logger.info('Stopping original feed')
        try:
            requests.get(
                f'http://{config.shrimp.hostname}:{config.shrimp.rest_api_port}/videofeed/stop',
            )
        except Exception as e:
            logger.exception(e)

        websocat = None
        if self.websocat:
            websocat = self.websocat
            self.websocat = None
            try:
                logger.debug('terminating websocat...')
                websocat.terminate()
                websocat.wait(1)
            except subprocess.TimeoutExpired as _:
                websocat.kill()
            except Exception as e:
                logger.exception(e)

        if self.healthcheck_thread:
            self.healthcheck_thread.join(timeout=3)
            self.healthcheck_thread = None
        VideoFeedManager.instance = None
        logger.debug('videofeed closed')

