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
    def __init__(self):
        self.websocat = None
        self.healthcheck_thread = None

    @property
    def log_file(self):
        return f'{config.tmp_dir}/logs/websocat.out'
    @property
    def err_file(self):
        return f'{config.tmp_dir}/logs/websocat.err'

    def start(self):
        # get the shrimp to start streaming
        response: requests.Response = requests.get(
            f'http://{config.shrimp.hostname}:{config.shrimp.rest_api_port}/videofeed/start',
        )
        if not response.ok:
            raise Exception(f'{response.status_code}/{response.reason}')
        payload = munch.munchify(response.json())
        if payload.code != 0:
            raise Exception(f'Could not get camera stream up: {payload.reason}')

        feed_hostname = payload.get('feed_hostname')
        feed_port = payload.get('feed_port')
        if None in (feed_hostname, feed_port):
            raise Exception(f'Missing feed_url|feed_port from camera stream: {payload}')
        # hotfix for websocat: it doesn't seem to be able to do hostname resolution
        # so let's do it for them.
        feed_hostname = socket.gethostbyname(feed_hostname)
        feed_url = f'{feed_hostname}:{feed_port}'

        try:
            os.system(f'/usr/bin/pkill websocat')
        except: pass

        # start websocat to wrap the stream in a websocket
        self.websocat = subprocess.Popen(
            [
                'websocat',
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
        logger.info(f'Running websocat relay: {" ".join(self.websocat.args)}')
        self.websocket_url = f'ws://{config.server.hostname}:{config.server.videofeed_port}'
        # TODO healthcheck thread that stops websocat whenever streaming has stopped
        self.healthcheck_thread = threading.Thread(target=self.healthcheck_websocat)
        self.healthcheck_thread.start()

    def healthcheck_websocat(self):
        while self.websocat is not None:
            rcode = self.websocat.poll()
            if rcode is not None:
                with open(self.log_file, 'r') as f:
                    logging.getLogger(__name__+'.websocat.out').info('\n'.join(f.readlines()))
                with open(self.err_file, 'r') as f:
                    logging.getLogger(__name__+'.websocat.err').error('\n'.join(f.readlines()))
                self.healthcheck_thread = None
                self.stop()
                break
            time.sleep(config.server.subprocess_polling_period_ms/1000.)

    def stop(self):
        try:
            requests.get(
                f'{config.shrimp.hostname}:{config.shrimp.rest_api_port}/videofeed/stop',
            )
        except: pass

        if self.websocat:
            websocat = self.websocat
            self.websocat = None
            try:
                websocat.terminate()
                websocat.wait(timeout=3)
            except TimeoutError:
                try:
                    websocat.kill()
                except: pass
        if self.healthcheck_thread:
            self.healthcheck_thread.join()
            self.healthcheck_thread = None
