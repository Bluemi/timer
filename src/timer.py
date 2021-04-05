#!/usr/bin/python3

import argparse
import socket
import json


IP = '127.0.0.1'
PORT = 4223


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('duration', type=str, nargs='?')
    parser.add_argument('title', type=str)

    return parser.parse_args()


def send_message(message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(json.dumps(message).encode('utf-8'), (IP, PORT))

        data, addr = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        if not response['success']:
            print(response['message'])



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



def main():
    args = parse_arguments()
    print(args)
    if args.duration is not None:
        duration = parse_duration(args.duration)
        title = args.title
        message = {
                'type': 'start',
                'duration': int(duration),
                'title': args.title
            }
        send_message(message)
    if args.duration is None:
        message = {
                'type': 'start',
                'title': args.title
                }
        send_message(message)


if __name__ == '__main__':
    main()
