from selenium import webdriver
from selenium.webdriver.edge.service import Service
import time

service = Service(executable_path='./msedgedriver.exe')
driver = webdriver.Edge(service=service)
driver.get("https://www.facebook.com/")
# ...
time.sleep(10)
driver.quit()