def fire_on_aos(sat, pk, tle1, tle2, aos, los):
	from selenium import webdriver
	from selenium.webdriver.edge.service import Service
	from screeninfo import get_monitors
	import time
	from datetime import datetime
	import argparse
	# import threading

	# passid, satellite name, tle, aos, los

	# argParser = argparse.ArgumentParser()
	# argParser.add_argument("-s", "--sat", help="satellite name", required=True)
	# argParser.add_argument("-p", "--pid", help="pass id", required=True)
	# argParser.add_argument("-t1", "--tle1", help="TLE line 1", required=True)
	# argParser.add_argument("-t2", "--tle2", help="TLE line 2", required=True)
	# argParser.add_argument("-a", "--aos", help="AOS", required=True)
	# argParser.add_argument("-l", "--los", help="LOS", required=True)
	# args = argParser.parse_args()

	now = datetime.now()
	later = datetime.strptime(los, '%Y-%m-%dT%H:%M:%S')
	seconds = (later-now).total_seconds()

	print(seconds)
	# print("args=%s" % args)

	x1=0
	y1=0
	x2=500
	y2=0
	height1=height2=700
	width1=width2=500

	m = get_monitors()
	if (len(m) > 0):
		height1=height2=m[0].height
		width1=width2=x2=m[0].width/2

	# print(height1)
	# print(width1)

	desired_cap={}
	service = Service(executable_path='./msedgedriver.exe')

	# driver = webdriver.Edge(executable_path='./MicrosoftWebDriver.exe', capabilities=desired_cap)
	driver = webdriver.Edge(service=service)
	# # driver.set_window_position(x1, y1, windowHandle='current')
	driver.set_window_rect(x = x1, y = y1, width = width1, height = height1)
	time.sleep(1)

	# driver1 = webdriver.Edge(executable_path='./MicrosoftWebDriver.exe', capabilities=desired_cap)
	driver1 = webdriver.Edge(service=service)
	# # driver1.set_window_position(0, 0, windowHandle='current')
	driver1.set_window_rect(x = x2, y = y2, width = width2, height = height2)
	driver.get("http://127.0.0.1:5000/spectrum.html")

	params = "?pid="+pk+"&sat="+sat+"&aos="+aos+"&los="+los+"&tle1="+tle1+"&tle2="+tle2
	driver1.get("http://127.0.0.1:5000/passview.html"+params)
	time.sleep(seconds)
	driver.quit()
	time.sleep(80)


def fire_on_los(pk):
	from selenium import webdriver
	from selenium.webdriver.edge.service import Service
	from screeninfo import get_monitors
	import time
	height2=700
	width2=500
	m = get_monitors()
	if (len(m) > 0):
		height2=m[0].height
		width2=m[0].width/2

	service = Service(executable_path='./msedgedriver.exe')
	driver = webdriver.Edge(service=service)
	driver.set_window_rect(x = 0, y = 0, width = width2*2, height = height2)
	driver.get("http://127.0.0.1:5000/mwd.html?passid="+pk)
	time.sleep(180)
	driver.quit()