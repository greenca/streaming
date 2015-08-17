import gevent
from gevent.pywsgi import WSGIServer
from gevent.queue import Queue

from flask import Flask, Response, request, render_template

import time
import json

import cv2
import numpy as np


class ServerSentEvent(object):

    def __init__(self, data):
        self.data = data
        self.event = None
        self.id = None
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k)
                 for k, v in self.desc_map.iteritems() if k]
        return "%s\n\n" % "\n".join(lines)


app = Flask(__name__)
subscriptions = []


@app.route('/')
def index():
    return render_template('imgstream.html')


@app.route("/subscribe")
def subscribe():
    def gen():
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit:
            subscriptions.remove(q)

    return Response(gen(), mimetype="text/event-stream")


cap = cv2.VideoCapture(0)

def background():
    count = 0
    while True:
        print count
        count += 1
        
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        spectrum = np.mean(gray, 0)

        msg = json.dumps({"blue": frame[:,:,0].tolist(),
                          "green": frame[:,:,1].tolist(),
                          "red": frame[:,:,2].tolist(),
                          "gray": gray.tolist(),
                          "spectrum": spectrum.tolist()})

        for sub in subscriptions[:]:
            sub.put(msg)
        gevent.sleep(1)


if __name__ == '__main__':
    app.debug = True
    server = WSGIServer(("", 5000), app)
    srv_greenlet = gevent.spawn(server.start)
    background_task = gevent.spawn(background)
    try:
        gevent.joinall([srv_greenlet, background_task])
    except KeyboardInterrupt:
        print "Exiting"

