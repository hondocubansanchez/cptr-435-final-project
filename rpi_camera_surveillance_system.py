import io
import picamera
import logging
import socketserver
##import RPi.GPIO as GPIO
from threading import Condition
from http import server
from gpiozero import Button, MotionSensor
from picamera import PiCamera
from time import sleep
##from signal import pause

##def main():

    # tell the GPIO module that we want to use the 
    # chip's pin numbering scheme
##    GPIO.setmode(GPIO.BCM)

    # setup pin 25 as an output
##    GPIO.setup(2,GPIO.IN)
##    GPIO.setup(pir_sensor, GPIO.IN)


##    GPIO.input(pir_sensor,True)

##    while True:
##        if GPIO.input(2):
             # the button is being pressed, so turn on the green LED
             # and turn off the red LED
##             GPIO.input(pir_sensor,False)
##             print ("button true")
##        else:
##             # the button isn't being pressed, so turn off the green LED
             # and turn on the red LED
##             GPIO.input(pir_sensor,True)
##             print ("button false")

##        time.sleep(0.1)

##    print ("button pushed")

##    GPIO.cleanup()

#create objects that refer to a button,
#a motion sensor and the PiCamera
button = Button(2)
pir = MotionSensor(4)
#camera = PiCamera()

#image image names
i = 0



PAGE="""\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""

def take_photo():
    global i
    i = i + 1
    camera.capture('/home/pi/Desktop/Pictures/image_%s.jpg' % i)
    print('A photo has been taken')
    sleep(10)
    
pir.when_motion = take_photo


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = 180
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('192.168.0.105', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()