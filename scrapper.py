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

def scrape(driver, error_wait = 1):
    """
    Scrapes the current page and returns list of dictionaries 'dict'

    dict = {
            'jmeno': name,
            'lekari': list of names of doctors,
            'adresa': full adress,
            'email': email,
            'tel': phone number,
            'web': web page adress
        }
    
    *error_wait : int, (default 1)
        - Time to try again after a failed get request
    """
    global hrefs_old

    elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//a[@class='btn btn--light btn--dentists']")))
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    
    # After going to the next page, in the case that all the page elements weren't properly updated,
    # try loading them into 'elements' variable again after 1 second
    if not page == re.sub(".*/","1 /", page):
        while True:
            broken = False    
            for i in range(len(elements)):
                if elements[i].get_attribute('href') == hrefs_old[i]:
                    time.sleep(1)
                    elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//a[@class='btn btn--light btn--dentists']")))
                    broken = True
                    break
            if broken == False:
                break

    data=[]
    req=[]
    for i in range(len(elements)):
        req.append(elements[i].get_attribute('href'))
        req[i]=req[i].replace("https://www.dent.cz/zubar/","https://is-api.dent.cz/api/v1/web/workplaces/")
        
        # In the case the get request fails, try again after 'error_wait' seconds
        while True:
            resp = requests.get(req[i])
            if resp.ok:
                break
            print(f"status code of request for data number {i+1} on page {page} is {resp.status_code}, trying again in {error_wait} second(s)")
            time.sleep(error_wait)

        fdata = resp.json()
        fdict = {
            'jmeno': fdata['name'],
            'lekari': [fdata['membes'][i]['full_name_with_title'] for i in range(len(fdata['membes']))],
            'adresa': fdata['address']['print'],
            'email': fdata['contact']['email1'],
            'tel': fdata['contact']['phone1'],
            'web': fdata['contact']['web']
        }
        data.append(fdict)
    
        print(f"data number {i+1} on page {page} in memorry")
    hrefs_old = [elements[j].get_attribute('href') for j in range(len(elements))]
    return data

def create_json(json_file, data):
    """
    Creates a file with name 'json_file' and saves list 'data' in json format
    """
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    with open(json_file, "w") as write_file:
        json.dump(data, write_file, indent=4)
    print(f"data on page {page} was saved to '{json_file}'")

def append_json(json_file, data):
    """
    Appends 'json_file' file with data in list 'data' in json format
    """
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    with open(json_file, "+r") as append_file:
        append_file.seek(0,2)
        position = append_file.tell() - 3
        append_file.seek(position)
        append_file.write(json.dumps(data, indent=4).replace("[",",",1))
    print(f"data on page {page} was saved to '{json_file}'")

def create_csv(csv_file, data):
    """
    Creates a file with name 'csv_file' and saves data from list 'data' in csv format
    
    Excludes keyword 'lekari' from each dictionary in 'data'
    """
    for i in range(len(data)):
        del data[i]['lekari']
    
    with open(csv_file, 'w', newline ='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(data[0].keys())
        for i in range(len(data)):
            csv_writer.writerow(data[i].values())
    
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    print(f"data from {page} transfered into csv format and saved to '{csv_file}'")

def append_csv(csv_file, data):
    """
    Appends file 'csv_file' with data from list 'data' in csv format
    
    Excludes keyword 'lekari' from each dictionary in 'data'
    """
    for i in range(len(data)):
        del data[i]['lekari']
    
    with open(csv_file, 'a', newline ='') as file:
        csv_writer = csv.writer(file)
        for i in range(len(data)):
            csv_writer.writerow(data[i].values())
    
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    print(f"data from {page} transfered into csv format and saved to '{csv_file}'")

def scrape_create(driver, json_file, csv_file = None):
    """
    Scrapes current page, creates file 'json_file' and saves the data in there in json format
    
    If argument 'csv_file' is specified, it also creates the file and saves the data (with keyword 'lekari' excluded) in there in csv format
    """
    data = scrape(driver)
    create_json(json_file, data)
    if csv_file:
        create_csv(csv_file, data)

def scrape_append(driver, json_file, csv_file = None):
    """
    Scrapes current page, appends file 'json_file' with data in json format
    
    If argument 'csv_file' is specified, it also appends the file with data (with keyword 'lekari' excluded) in csv format
    """
    data = scrape(driver)
    append_json(json_file, data)
    if csv_file:
        append_csv(csv_file, data)

def next_page(driver):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,"//button[@class='box-pager__item box-pager__btn box-pager__btn--next']"))).click()
    page = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@class='box-pager__item']"))).text
    print(f"going to page {page}")


if __name__ == "__main__":
    """ 
    Scrapes the database at "https://www.dent.cz/zubni-lekari" and saves the data
    in json and csv format into files 'json_file' and 'csv_file' respectively
    """
    json_file = "data.json"
    csv_file = 'data.csv'

    options = Options()
    #options.add_argument("headless")

    driver = webdriver.Edge(options = options)
    print("browser opened")
    driver.get("https://www.dent.cz/zubni-lekari")
    print("going to 'https://www.dent.cz/zubni-lekari'")

    scrape_create(driver, json_file, csv_file)
    next_page(driver)

    while True:
        scrape_append(driver, json_file, csv_file)
        if not WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,"//button[@class='box-pager__item box-pager__btn box-pager__btn--next']"))).is_enabled():
            break
        next_page(driver)

    driver.close()
    print("browser closed")