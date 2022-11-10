import requests
import json
import csv
import time

def scrape(url, page, error_wait = 1):
    while True:
        t_request_start = time.perf_counter()
        request = requests.post(url, {'page':page})
        t_request_duration = time.perf_counter() - t_request_start
        print(f"waiting for request time: {t_request_duration}")
        if request.status_code == 200:
            break
        print(f"unexpected request status code: '{request.status_code}', sending request again in {error_wait}")
        time.sleep(error_wait)
    
    t_computation_start = time.perf_counter()
    raw_data = request.json()['data']
    data = []
    for i in range(len(raw_data)):
        temp_data = {
        'jmeno': raw_data[i]['name'],
        'adresa': raw_data[i]['address']['print'],
        'email': raw_data[i]['contact']['email1'],
        'tel': raw_data[i]['contact']['phone1'],
        'web': raw_data[i]['contact']['web']
         }
        data.append(temp_data)
    t_computation_duration = time.perf_counter() - t_computation_start
    print(f"time spent on computation: {t_computation_duration}")
    return data
        
def create_json(data, json_file):
    """
    Creates a file with name 'json_file' and saves list 'data' in json format
    """
    with open(json_file, "w") as write_file:
        json.dump(data, write_file, indent=4)
    print(f"{len(data)} entries on page {page} were saved to '{json_file}'")

def append_json(data, json_file):
    """
    Appends 'json_file' file with data in list 'data' in json format
    """
    with open(json_file, "+r") as append_file:
        append_file.seek(0,2)
        position = append_file.tell() - 3
        append_file.seek(position)
        append_file.write(json.dumps(data, indent=4).replace("[",",",1))
    print(f"{len(data)} entries on page {page} were saved to '{json_file}'")

def create_csv(data, csv_file):
    """
    Creates a file with name 'csv_file' and saves data from list 'data' in csv format
    """
    
    with open(csv_file, 'w', newline ='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(data[0].keys())
        for i in range(len(data)):
            csv_writer.writerow(data[i].values())
    
    print(f"data from {page} transfered into csv format and saved to '{csv_file}'")

def append_csv(data, csv_file):
    """
    Appends file 'csv_file' with data from list 'data' in csv format
    """
    
    with open(csv_file, 'a', newline ='') as file:
        csv_writer = csv.writer(file)
        for i in range(len(data)):
            csv_writer.writerow(data[i].values())

    print(f"data from {page} transfered into csv format and saved to '{csv_file}'")
    
if __name__ == "__main__":
    url = "https://is-api.dent.cz/api/v1/web/workplaces"
    page = 1

    json_file = "data.json"
    csv_file = "data.csv"

    data = scrape(url, page)
    t_io_start = time.perf_counter()
    create_json(data, json_file)
    create_csv(data,csv_file)
    t_io_duration = time.perf_counter() - t_io_start
    print(f"IO operation duration: {t_io_duration}")
    page += 1

    while True:
        data = scrape(url, page)
        if data == []:
            break
        append_json(data, json_file)
        append_csv(data,csv_file)
        page += 1