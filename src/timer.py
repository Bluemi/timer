#!/usr/bin/python3

import sys
import socket
import json
import time

IP = '127.0.0.1'
PORT = 4223


def parse_arguments():
    result = {
        'title': None,
        'duration': None,
        'list': False,
    }
    args = sys.argv[1:]
    if len(args) == 0:
        print_usage()
        sys.exit(0)
    else:
        if args[0] in ('-l', '--list'):
            result['list'] = True
        else:
            if len(args) == 1:
                result['title'] = args[0]
            elif len(args) == 2:
                result['duration'] = args[0]
                result['title'] = args[1]

    return result


def print_usage():
    print('USAGE: TODO')


def send_message(message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(json.dumps(message).encode('utf-8'), (IP, PORT))

        data, addr = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        if not response['success']:
            print(response['message'])
        return response


def parse_duration(duration):
    duration = str(duration).split(':')
    if len(duration) == 1:
        return int(duration[0]) * 60
    duration.reverse()
    seconds = 0
    multiplier = 1
    for part in duration:
        seconds += int(part) * multiplier
        multiplier *= 60
    return seconds


def format_duration(duration):
    duration = int(duration)
    hours = duration // 3600
    minutes = duration % 3600 // 60
    seconds = duration % 60
    if hours:
        return '{:02}:{:02}:{:02}'.format(hours, minutes, seconds)
    return '{:02}:{:02}'.format(minutes, seconds)


def main():
    args = parse_arguments()
    print('args: {}'.format(args))

    if args['list']:
        message = {
            'type': 'list'
        }
        response = send_message(message)
        if response['success']:
            timers = response['timers']
            if not timers:
                print('no current timers')
            else:
                print('{:10}{:20}'.format('Title', 'Duration left'))
                for timer in timers:
                    duration_left = format_duration(timer['end_time'] - time.time())
                    print('{:10}{:20}'.format(timer['title'], duration_left))
    elif args['title'] is not None:
        message = {
            'type': 'start',
            'title': args['title'],
        }
        if args['duration'] is not None:
            duration = parse_duration(args['duration'])
            message['duration'] = duration
        send_message(message)


if __name__ == '__main__':
    main()
