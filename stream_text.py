import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue

from flask import Flask, Response, request

import time
import json


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
def hello_world():
    debug_template = """
     <html>
       <head>
       </head>
       <body>
         <h1>Server sent events</h1>
         <div id="event"></div>
         <script type="text/javascript">

         var eventOutputContainer = document.getElementById("event");
         var evtSrc = new EventSource("/subscribe");

         evtSrc.onmessage = function(e) {
             var jdata = JSON.parse(e.data);
             console.log(e.data);
             console.log(jdata.test);
             eventOutputContainer.innerHTML = e.data;
           
         };

         </script>
       </body>
     </html>
    """
    return(debug_template)

@app.route("/publish")
def publish():
    msg = str(time.time())
    msg = json.dumps(request.args)
    msg = json.dumps({"test": range(10)})

    def notify():
        for sub in subscriptions[:]:
            sub.put(msg)

    gevent.spawn(notify)

    return "OK"

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

def background():
    count = 0
    while True:
        print count
        count += 1
        msg = str(time.time())
        msg = json.dumps({"test": str(time.time())})
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

