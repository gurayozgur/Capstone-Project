from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import imutils
import time
import cv2
import os
import serial
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
def detect_and_predict_mask(frame, maskNet):
	xmin=0
	ymin=0
	xmax=1
	ymax=1

	xn_min=0
	yn_min=0
	xn_max=640
	yn_max=480
	
	pred_flag=1
	
	(hei, wid) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	faces = []
	locs = []
	preds = []
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	faces1 = faceCascade.detectMultiScale(
	    gray,
	    scaleFactor=1.2,
	    minNeighbors=2,     
	    minSize=(90,90)#128
	)

	for (x,y,w,h) in faces1:
		xmin=x-20
		ymin=y-20
		xmax=x+w+20
		ymax=y+h+20
		wf=w
		hf=h
		 
		if xmin<0:
			xmin=0    
		if ymin<0:
			ymin=0
		if xmax>640:
			xmax=640
		if ymax>480:
			ymax=480

	if xmin==0 and ymin==0 and xmax==1 and ymax==1:
		pred_flag=0

	face = frame[ymin:ymax, xmin:xmax]
	face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
	face = cv2.resize(face, (224, 224))
	face = img_to_array(face)
	face = preprocess_input(face)
	faces.append(face)
	locs.append((xmin, ymin, xmax, ymax))

	if len(faces) > 0:
		faces = np.array(faces, dtype="float32")
		preds = maskNet.predict(faces, batch_size=32)
	return (locs, preds, pred_flag)
def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False
def showimage(frame,people):
	# show the output frame and if the `q` key was pressed, break from the loop
	cv2.putText(frame, "", (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
	
	#cv2.putText(frame, "People: "+str(people), (10, 20),
		#cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
	#cv2.imshow("Face Mask Detector", frame)

#########################################
print("[INFO] starting the mask detection system...")

if yes_or_no("Do you want to use existing people count?") == True:
	file = open('trace.txt','r+')
	people = file.read()
	file.close()
	print("Number of people inside is", people)
else:
	people = input("Number of people inside:")
	file = open('trace.txt','r+')
	file.truncate(0)
	file.write(str(people))
	file.close()

if yes_or_no("Do you want to use predefined visitor quota?") == True:
	file = open('quota.txt','r+')
	volume = file.read()
	file.close()
	print("Number of allowed people inside is", volume)
else:
	volume = input("Number of allowed people inside:")
	file = open('quota.txt','r+')
	file.truncate(0)
	file.write(str(volume))
	file.close()

while int(volume) < int(people):
	print("Number of people cannot be greater than number of allowed.")
	if yes_or_no("Do you want to use existing people count?") == True:
		file = open('trace.txt','r+')
		people = file.read()
		file.close()
		print("Number of people inside is", people)
	else:
		people = input("Number of people inside:")
		file = open('trace.txt','r+')
		file.truncate(0)
		file.write(str(people))
		file.close()
	if yes_or_no("Do you want to use predefined visitor quota?") == True:
		file = open('quota.txt','r+')
		volume = file.read()
		file.close()
		print("Number of allowed people inside is", volume)
	else:
		volume = input("Number of allowed people inside:")
		file = open('quota.txt','r+')
		file.truncate(0)
		file.write(str(volume))
		file.close()

ser=serial.Serial('/dev/ttyUSB0', 9600, timeout=5)
ser.write((people+"_"+volume+"\n").encode('utf-8'))
ok = ser.read()
while int.from_bytes(ok, byteorder='big') != 1:
	ser.write((people+"_"+volume+"\n").encode('utf-8'))
	ok = ser.read()
people = int(people)

print("[INFO] loading face mask detector model...")
maskNet = load_model("mask_detector_2_3.model")

print("[INFO] starting video stream...")
#vs = VideoStream(src=0).start()
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

maskflag = 0
confidence = 0

while True:
	pe_done = ser.readline().decode('utf-8').rstrip()
	while int(pe_done.split('_')[2]) == 1:
		if pe_done != b'':
			if people != int(pe_done.split('_')[0]):
				people = int(pe_done.split('_')[0])
				file = open('trace.txt','r+')
				file.truncate(0)
				file.write(str(people))
				file.close()
		
		cv2.putText(frame, "CROWDED", (20, 20),
			cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
		pe_done = ser.readline().decode('utf-8').rstrip()
		
		#cv2.putText(frame, "People: "+str(people), (10, 20),
			#cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
		cv2.imshow("Face Mask Detector", frame)
		



	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	# detect faces in the frame and determine if they are wearing a face mask or not
	(locs, preds, pred_flag) = detect_and_predict_mask(frame, maskNet)
	# loop over the detected face locations and their corresponding locations
	if pred_flag>0:
		for (box, pred) in zip(locs, preds):
			# unpack the bounding box and predictions
			(startX, startY, endX, endY) = box
			(mask, withoutMask, wrongMask) = pred
			# determine the class label and color we'll use to draw the bounding box and text
			if (mask > withoutMask) and (mask > wrongMask):
				label = "Mask is okay"
				color = (0, 255, 0)
				maskflag = 1
				confidence = confidence + 1
		
			if (withoutMask > mask) and (withoutMask > wrongMask):
				label = "Wear a face mask"
				color = (0, 0, 255)
				maskflag = 0
				confidence = 0

			if (wrongMask > mask) and (wrongMask > withoutMask):
				label = "Wear your mask properly"
				color = (255, 0, 0)
				maskflag = 0
				confidence = 0

			cv2.putText(frame, label, (startX-50, startY - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
			cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

	while confidence >= 3:
		pe_done = ser.readline().decode('utf-8').rstrip()
		if pe_done != b'':
			if people != int(pe_done.split('_')[0]):
				people = int(pe_done.split('_')[0])
				file = open('trace.txt','r+')
				file.truncate(0)
				file.write(str(people))
				file.close()
			if int(pe_done.split('_')[1]) == 1:
				maskflag = 0
				confidence = 0
				ser.write((str(maskflag)+"_0\n").encode('utf-8'))
				break;
			
			else:
				ser.write((str(maskflag)+"_0\n").encode('utf-8'))	
		cv2.putText(frame, "Let's check your temperature", (10, 350),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
		
		
		
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break

	pe_done = ser.readline().decode('utf-8').rstrip()
	if pe_done != b'':
		if people != int(pe_done.split('_')[0]):
			people = int(pe_done.split('_')[0])
			file = open('trace.txt','r+')
			file.truncate(0)
			file.write(str(people))
			file.close()
	
	#cv2.putText(frame, "People: "+str(people), (10, 20),
	#	cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
	cv2.imshow("Face Mask Detector", frame)
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()



