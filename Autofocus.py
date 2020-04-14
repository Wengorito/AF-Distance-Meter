import cv2 #sudo apt-get install python-opencv
import numpy as py
import os
import time
import io

try:
    import picamera
    from picamera.array import PiRGBArray
except:
    sys.exit(0)
    
def focusing(val):
    value = (val << 4) & 0x3ff0
    data1 = (value >> 8) & 0x3f
    data2 = value & 0xf0
    os.system("i2cset -y 0 0x0c %d %d" % (data1,data2))
    
def sobel(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    img_sobel = cv2.Sobel(img_gray,cv2.CV_16U,1,1)
    return cv2.mean(img_sobel)[0]

def laplacian(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U)
    return cv2.mean(img_sobel)[0]
    

def calculation(camera):
    rawCapture = PiRGBArray(camera) 
    camera.capture(rawCapture,format="bgr", use_video_port=True)
    image = rawCapture.array
    rawCapture.truncate(0)
    imCrop = image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]
    return laplacian(imCrop)

#calibrated relation of max_index parameter and the actual object distance
def equation (y) :
    x = 1642.98/(y-149.6)
    return x
    
if __name__ == "__main__":
    #open camera
    camera = picamera.PiCamera()
    #set camera resolution to 640x480(Small resolution for faster speeds.)
    camera.resolution = (640, 480)    

    # Create the in-memory stream
    stream = io.BytesIO()
    
    #output = py.empty((480, 640))
    camera.capture(stream, format='jpeg')
    # Construct a numpy array from the stream
    data = py.fromstring(stream.getvalue(), dtype=py.uint8)
    # "Decode" the image from the array, preserving colour
    image = cv2.imdecode(data, 1)
    # OpenCV returns an array with data in BGR order. If you want RGB instead
    # use the following...
    image = image[:, :, ::-1]

    #wybor zaznaczenia - ROI selection
    r = cv2.selectROI(image)
    imCrop = image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]

    #open camera preview
    camera.start_preview()
    


    print("Start focusing")
    
    max_index = 10
    max_value = 0.0
    last_value = 0.0
    dec_count = 0
    focal_distance = 10
    
    while True:
        #Adjust focus
        focusing(focal_distance)
        #Take image and calculate image clarity
        val = calculation(camera)
        #Find the maximum image clarity
        if val > max_value:
            max_index = focal_distance
            max_value = val
            
        #If the image clarity starts to decrease
        if val < last_value:
            dec_count += 1
        else:
            dec_count = 0
        #Image clarity is reduced by six consecutive frames
        
        if dec_count > 6:
            break
        last_value = val
        
        #Increase the focal distance
        #obniżając ten parametr można zwiększyć dokładność
        #to increase accuracy lower this parameter
        focal_distance += 5
        if focal_distance > 1000:
            break

    #Adjust focus to the best
    focusing(max_index)
    time.sleep(1)
    #set camera resolution to 2592x1944
    camera.resolution = (2592,1944)
    #save image to file.
    camera.capture("test.jpg")
    print("max index = %d,max value = %lf" % (max_index,max_value))

    #oblicz odległość - calculate the distance
    dist = equation(max_index)
    print("distance = %d cm" %(dist)) 
    #while True:
    #   time.sleep(1)
        
    camera.stop_preview()
    camera.close()
        
    
