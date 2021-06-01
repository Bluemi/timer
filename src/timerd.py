#!/usr/bin/python3


import os
import queue
import time
import socket
import json
import threading
from queue import Queue

from plyer import notification
from ruamel.yaml import YAML


IP = '127.0.0.1'
PORT = 4223
CHECK_INTERVAL = 1
HOME_DIR = os.path.expanduser('~')
CONFIG_FILES = [
    os.path.join(HOME_DIR, '.config', 'timer', 'timerd.yml'),
    os.path.join(HOME_DIR, '.timerd_config')
]
yaml = YAML(typ='safe')


class Timer:
    def __init__(self, title, start_time, end_time):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time

    def to_dict(self):
        return {'title': self.title, 'start_time': self.start_time, 'end_time': self.end_time}


class Config:
    class Preset:
        def __init__(self, title, duration):
            self.title = title
            self.duration = duration

        def to_dict(self):
            return {
                'title': self.title,
                'duration': self.duration,
            }

        @staticmethod
        def from_dict(d):
            return Config.Preset(title=d['title'], duration=d['duration'])

    def __init__(self, config_path, presets=None):
        self.config_path = config_path
        if presets is None:
            presets = []
        self.presets = presets

    @staticmethod
    def load():
        for config_file in CONFIG_FILES:
            if os.path.isfile(config_file):
                with open(config_file, 'r') as conf_f:
                    config = yaml.load(conf_f)
                    presets = list(map(Config.Preset.from_dict, config['presets']))
                    return Config(config_file, presets=presets)
        return Config(CONFIG_FILES[0])

    def dump(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        with open(self.config_path, 'w') as conf_f:
            yaml.dump(self.to_dict, conf_f)

    def to_dict(self):
        presets = list(map(Config.Preset.to_dict, self.presets))
        return {
            'presets': presets
        }

    def load_duration_from_title(self, title):
        for preset in self.presets:
            if preset.title == title:
                return preset.duration
        raise NoDurationFoundException('Could not find preset for "{}"'.format(title))


class TickThread(threading.Thread):
    def __init__(self):
        super(TickThread, self).__init__()
        self.timers = []
        self.running = True
        self.timer_queue = Queue()

    def run(self):
        while self.running:
            # add timers from queue
            while True:
                try:
                    timer = self.timer_queue.get_nowait()
                except queue.Empty:
                    break
                self.timers.append(timer)

            # check timers
            now = time.time()
            for timer in self.timers:
                if now >= timer.end_time:
                    notification.notify(
                        title=timer.title,
                        timeout=3
                    )

            self.timers = list(filter(lambda t: now < t.end_time, self.timers))
            time.sleep(CHECK_INTERVAL)


def new_timer(title, duration):
    start_time = time.time()
    return Timer(title, start_time, start_time + duration)


def new_timer_from_message(message, config):
    duration = message.get('duration')
    title = message['title']
    if duration is None:
        duration = config.load_duration_from_title(title)
    return new_timer(title, duration)


def handle_message(message, tick_thread, config):
    if message['type'] == 'start':
        timer = new_timer_from_message(message, config)
        print('got new timer: title={} duration={}'.format(timer.title, timer.end_time - timer.start_time))
        tick_thread.timer_queue.put(timer)
        return {'success': True, 'message': None}
    elif message['type'] == 'list':
        print('got list message')
        timers = list(map(Timer.to_dict, tick_thread.timers))
        return {'success': True, 'message': 'List of timers', 'timers': timers}


def main():
    config = Config.load()

    tick_thread = TickThread()
    tick_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((IP, PORT))

        while True:
            data, addr = sock.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            try:
                response = handle_message(message, tick_thread, config)
                if response is not None:
                    sock.sendto(json.dumps(response).encode('utf-8'), addr)
            except NoDurationFoundException as e:
                sock.sendto(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'), addr)


class NoDurationFoundException(Exception):
    pass


if __name__ == '__main__':
    main()
