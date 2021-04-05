#!/usr/bin/python3


import os
import time
import socket
import json
import threading
from plyer import notification


IP = '127.0.0.1'
PORT = 4223
CHECK_INTERVAL = 1


class Timer:
    def __init__(self, title, start_time, end_time):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time


class TickThread(threading.Thread):
    def __init__(self):
        super(TickThread, self).__init__()
        self.timers = []
        self.running = True


    def run(self):
        while self.running:
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


def load_duration_from_title(title):
    config_file = os.path.join(os.path.expanduser('~'), '.config', 'timer', 'config.json')
    if not os.path.isfile(config_file):
        raise NoDurationFoundException('Could not load config file')

    with open(config_file, 'r') as f:
        config = json.load(f)
    duration = config.get(title)
    if duration is None:
        raise NoDurationFoundException('Could not find config for "{}"'.format(title))
    return duration


def new_timer_from_message(message):
    duration = message.get('duration')
    title = message['title']
    if duration is None:
        duration = load_duration_from_title(title)
    return new_timer(title, duration)


def main():
    tick_thread = TickThread()
    tick_thread.start()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((IP, PORT))

        while True:
            data, addr = sock.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            try:
                if message['type'] == 'start':
                    timer = new_timer_from_message(message)
                    print('got new timer: title={} duration={}'.format(timer.title, timer.end_time - timer.start_time))
                    tick_thread.timers.append(timer)
                    sock.sendto(json.dumps({'success': True, 'message': None}).encode('utf-8'), addr)
            except NoDurationFoundException as e:
                sock.sendto(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'), addr)


class NoDurationFoundException(Exception):
    pass


if __name__ == '__main__':
    main()
