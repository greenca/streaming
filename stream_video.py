import gevent
from gevent.pywsgi import WSGIServer

from flask import Flask, render_template, Response

import cv2
import numpy as np
from matplotlib import pyplot as plt

app = Flask(__name__)
cap = cv2.VideoCapture(0)

@app.route('/')
def index():
    return render_template('vidstream.html')

def gen():
    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        spectrum = np.mean(gray, 0)
        plt.plot(spectrum)
        plt.savefig('spectrum.jpg')
        plt.close()
        jpg_frame = cv2.imencode('.jpg', frame)[1].tostring()
        gevent.sleep(0.1)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg_frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_spectrum():
    while True:
        jpg_frame = open('spectrum.jpg', 'rb').read()
        gevent.sleep(0.1)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg_frame + b'\r\n')        

@app.route('/spectrum')
def spectrum():
    return Response(gen_spectrum(), mimetype='multipart/x-mixed-replace; boundary=frame')
    

if __name__ == '__main__':
    server = WSGIServer(("", 5000), app)
    server.serve_forever()
