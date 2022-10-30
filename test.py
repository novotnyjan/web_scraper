from urllib import request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
import requests
import json
import csv
import re
import time

req = requests.get("https://www.dent.cz/zubni-lekari")
with open('adresa.txt', 'w') as file:
    file.write(req.text)