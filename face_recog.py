import cv2, os, os.path, sqlite3, numpy as np, pickle, keyboard, shutil, prettytable, datetime
from PIL import Image 
import urllib

camAddress = 0
date = datetime.date.today().strftime('%b%d%y')

conn = sqlite3.connect('students.db')
c = conn.cursor()

def generateDataset():
	cam = cv2.VideoCapture(camAddress)
	detector=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
	conn = sqlite3.connect('students.db')
	c = conn.cursor()

	c.execute("CREATE TABLE IF NOT EXISTS students (id INT PRIMARY KEY NOT NULL, name text NOT NULL)")
	def insert_or_update(Id, name):
		c.execute('select * from students where id = ?', (Id,))
		row = c.fetchone()
		if row is None:
			c.execute("insert into students values (?,?)",  (Id, name))
			conn.commit()
		else:
			print('record already exists, updating...')
			c.execute('UPDATE students SET name = ? WHERE id = ?', (name, Id))
			conn.commit()

	i=0
	print ('\nIMPORTANT: Press Backspace before typing ID')
	Id = input('\n\nenter your ID: ')
	name = input('enter your name: ')
	
	insert_or_update(Id, name)

	if not os.path.exists('dataSet'):
		os.makedirs('dataSet')

	while True:
		ret, im = cam.read()
		gray=cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
		faces=detector.detectMultiScale(gray, scaleFactor=1.7, minNeighbors=5, minSize=(100, 100))
		for(x,y,w,h) in faces:
			i=i+1
			cv2.rectangle(im,(x-50,y-50),(x+w+50,y+h+50),(225,0,0),2)
			cv2.imwrite("dataSet/face-" + Id + '.' + str(i) + ".jpg", gray[y:y+h,x:x+w])
			cv2.imshow('im',im[y-50:y+h+50,x-50:x+w+50])
			cv2.waitKey(100)
		if i >= 15:
			cam.release()
			cv2.destroyAllWindows()
			break

def train():
	recognizer = cv2.face.LBPHFaceRecognizer_create()
	cascadePath = 'haarcascade_frontalface_default.xml'

	faceCascade = cv2.CascadeClassifier(cascadePath)

	def get_images_and_ids(path):
		image_paths = [os.path.join(path, f) for f in os.listdir(path)]
		# images will contains face images
		images = []
		# ids will contains the label that is assigned to the image
		ids = []
		for image_path in image_paths:
			# Read the image and convert to grayscale
			image_pil = Image.open(image_path).convert('L')
			# Convert the image format into numpy array
			image = np.array(image_pil, 'uint8')
			# Get the label of the image
			Id = int(os.path.split(image_path)[1].split(".")[0].replace("face-", ""))
			#Id=int(''.join(str(ord(c)) for c in Id))
			# Detect the face in the image
			faces = faceCascade.detectMultiScale(image)
			# If face is detected, append the face to images and the label to ids
			for (x, y, w, h) in faces:
				images.append(image[y: y + h, x: x + w])
				ids.append(Id)
				cv2.imshow("Adding faces to traning set...", image[y: y + h, x: x + w])
				cv2.waitKey(10)
		# return the images list and ids list
		return images, ids


	images, ids = get_images_and_ids('dataSet')
	cv2.imshow('test',images[0])
	cv2.waitKey(1)

	recognizer.train(images, np.array(ids))
	recognizer.save('training.yml')
	cv2.destroyAllWindows()



def detect():
	recognizer = cv2.face.LBPHFaceRecognizer_create()
	recognizer.read('training.yml')
	cascadePath =  'haarcascade_frontalface_default.xml'
	faceCascade = cv2.CascadeClassifier(cascadePath)

	cam = cv2.VideoCapture(camAddress)
	font = cv2.FONT_HERSHEY_SIMPLEX

	b = 255
	g = 255
	r = 0
	while True:
		ret, im = cam.read()
		gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
		faces=faceCascade.detectMultiScale(gray, minNeighbors=5)

		for(x,y,w,h) in faces:
			prediction, confidence = recognizer.predict(gray[y:y+h,x:x+w])
			cv2.rectangle(im, (x-20,y-20), (x+w+20,y+h+20), (b,g,r), 2)

			c.execute('select name from students where id = ' + str(prediction))
			name = c.fetchone()

			if confidence <= 70:
				cv2.putText(im, name[0], (x,y+h), font,1,(255,255,255),2)
				b = 255
				g = 255
				r = 0
				c.execute('select id from ' + date + ' where id = ?', (prediction,))
				row = c.fetchone()
				# print(c.fetchone())
				if row is None:
					c.execute('insert into ' + date + ' values (?,?)', (prediction, name[0]))
					conn.commit()
			else:
				cv2.putText(im, 'unknown', (x,y+h), font,1,(0,0,255),2)
				b = 0
				g = 0
				r = 255
			
		# print(name[0], confidence) # this line cause crash if there is no one in front of camera when recognition is started

		
		cv2.namedWindow('im', cv2.WINDOW_NORMAL)
		cv2.imshow('Press Esc to close this window',im)
		k = cv2.waitKey(10)
		if k == 27:		#close window if press Esc
			cv2.destroyAllWindows()
			cam.release()
			break
		# if cv2.getWindowProperty('im',cv2.WND_PROP_VISIBLE) < 1:        
		# 	break        
	cv2.destroyAllWindows()
	

def deleteDB():
	if os.path.exists('students.db'):
		os.remove('students.db')
	if os.path.exists('training.yml'):
		os.remove('training.yml')
	if os.path.exists('dataSet'):
		shutil.rmtree('dataSet', ignore_errors=True)
	global conn
	conn.close()
	

def viewTodaysAttendance():
	os.system('cls' if os.name == 'nt' else 'clear')
	
	c.execute('select * from ' + date)
	output = prettytable.from_db_cursor(c)
	output.set_style(prettytable.PLAIN_COLUMNS)
	print ("Today's attendance\n\n")
	print (output)
	conn.commit()

	print ('\nPress Esc to return to the main menu.')
	while True:
		if keyboard.is_pressed(chr(27)):
			menu()
			break


def viewAnyAttendance():
	os.system('cls' if os.name == 'nt' else 'clear')
	
	print ('\nIMPORTANT: Press Backspace before typing\n')
	date = input('Enter a date in the following format: May1318 \n13 is the day and 18 is the year 2018\n')
	

	c.execute("SELECT name FROM sqlite_master WHERE type='table' and name = ?", (date,))
	if c.fetchone():
		c.execute('select * from ' + date)	
		output = prettytable.from_db_cursor(c)
		output.set_style(prettytable.PLAIN_COLUMNS)
		print ("\nAttendance of " + date + ":\n\n")
		print (output)
		conn.commit()
	else:
		viewAnyAttendance()

	print ('\nPress Esc to return to the main menu.')
	while True:
		if keyboard.is_pressed(chr(27)):
			menu()
			break

def menu():
	os.system('cls' if os.name == 'nt' else 'clear')
	noData = False
	noTrainingFile = False

	c.execute("create table if not exists " + str(date) + " (id int primary key not null, name text not null)")
	conn.commit()
		
	if (not os.path.exists('dataSet') and not os.path.exists('training.yml') and not os.path.exists('students.db')) or os.path.exists('students.db') and not os.path.exists('dataSet'):
		noData = True
	elif not os.path.exists('training.yml') and os.path.exists('dataSet') and os.path.exists('students.db'):
		noTrainingFile = True

	if noData == True:
		print ('\n')
		print ('1. Generate Dataset. (No data has been generated yet.)')
		print ('2. Exit')
		print ('3. Enter Camera/Video Path')
		print ('\n')
		
		while True:
			if keyboard.is_pressed('1'):
				generateDataset()
				menu()
				break

			if keyboard.is_pressed('2'):
				os.system('cls' if os.name == 'nt' else 'clear')
				break

			if keyboard.is_pressed('3'):
				enterCamAddress()
				break
		
	if noTrainingFile == True:
		print('\n')
		print ('1. Generate Dataset')
		print ('2. Train. (No training data has been generated yet)')
		print ('3. View Database')
		print ('4. Exit')
		print ('5. Delete Database and Exit (Exit to Clear Cache)')
		print ('6. Enter Camera/Video Path')
		print ('\n')

		while True:
			if keyboard.is_pressed('1'):
				generateDataset()
				menu()
				break

			if keyboard.is_pressed('2'):
				train()
				menu()
				break

			if keyboard.is_pressed ('3'):
				viewDatabase()
				break

			if keyboard.is_pressed('4'):
				os.system('cls' if os.name == 'nt' else 'clear')
				break

			if keyboard.is_pressed('5'):
				deleteDB()
				break

			if keyboard.is_pressed('6'):
				enterCamAddress()
				break
		
	elif os.path.exists('dataSet') and os.path.exists('training.yml') and os.path.exists('students.db'):
		print('\n')
		print ('1. Generate Dataset')
		print ('2. Train')
		print ('3. Mark Attendance')
		print ('4. View Database')
		print ('5. Exit')
		print ('6. Delete Database and Exit (Exit to Clear Cache)')
		print ('7. Enter Camera/Video Path')
		print ('8. Enter a Date to View Attendance')
		print ("9. View Today's Attendance")
		print ('\n')

		while True:
			if keyboard.is_pressed('1'):
				generateDataset()
				menu()
				break			
			
			if keyboard.is_pressed('2'):
				train()
				menu()
				break

			if keyboard.is_pressed('3'):
				detect()
				menu()
				break

			if keyboard.is_pressed ('4'):
				viewDatabase()
				break
				
			if keyboard.is_pressed('5'):
				os.system('cls' if os.name == 'nt' else 'clear')
				break

			if keyboard.is_pressed('6'):
				deleteDB()
				break

			if keyboard.is_pressed('7'):
				enterCamAddress()
				break

			if keyboard.is_pressed('8'):
				viewAnyAttendance()
				break

			if keyboard.is_pressed('9'):
				viewTodaysAttendance()
				break

def viewDatabase():
	os.system('cls' if os.name == 'nt' else 'clear')

	c.execute('select * from students')
	output = prettytable.from_db_cursor(c)
	output.set_style(prettytable.PLAIN_COLUMNS)
	print (output)
	conn.commit()

	print ('\nPress Esc to return to the main menu.')
	while True:
		if keyboard.is_pressed(chr(27)):
			menu()
			break


def enterCamAddress():
	os.system('cls' if os.name == 'nt' else 'clear')
	print('Enter Camera IP. Example: http://192.168.10.39:8080/video')
	print('Or')
	print('Enter Camera Index. Example: 0')
	print ('Or')
	print('Path to Video File')
	print ('\nIMPORTANT: Press Backspace before typing')
	print ('\nPress Esc to return to the main menu.')
	global camAddress
	# camTemp = input('\nCamera IP: ')
	camAddress = input('\nCamera IP/Index: ')
	if camAddress.isdigit():
		camAddress = int(camAddress)
	menu()

menu()