from datetime import datetime

from common.structures import Message


def connected_message(name):
    return Message(
        user='Оповещение',
        text=f'{name} вошел(а) в чат!',
        time=datetime.now()
    ).to_json(ensure_ascii=False)


def disconnected_message(name):
    return Message(
        user='Оповещение',
        text=f'{name} покинул(а) чат :(',
        time=datetime.now()
    ).to_json(ensure_ascii=False)
