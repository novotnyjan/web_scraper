import asyncio
import aiohttp
import json
import csv
import time
import platform

async def scrape(url : str, session : aiohttp.ClientSession, task_id : int, error_wait = 0.5) -> None:
    """ 
    Coroutine that sends POST request with increasing page number with each call. Saves data to 'result_unsorted' global variable.
    Coroutine terminates when the response 'data' item is empty list.
    """ 
    global page
    global result_unsorted

    while True:
        page += 1
        _page = page

        #send post request and continue only if the response status is 200, otherwise try again after 'errow_wait' time
        while True:
            resp = await session.post(url, data = {"page": _page}, ssl=False)
            if resp.status == 200:
                print(f"response status for page {_page} is {resp.status}")
                break
            print(f"unexpected request status code for page {_page}: '{resp.status}', sending request again in {error_wait}")
            await asyncio.sleep(error_wait)

        #if there are no data on current page, terminate task
        resp = await resp.json()
        if resp['data'] == []:
            print(f"no data on page {_page}, closing task {task_id}")
            break
        
        #parse original json request and save it to global 'result_unsorted' variable with page number information
        raw_data = resp['data']
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
        data = [_page, data]
        result_unsorted.append(data)
        print(f"data from page {_page} in memory")

def save_json(json_file : str, result : list) -> None:
    with open(json_file, 'w') as file:
        json.dump(result, file, indent=4)
        print(f"data saved to {json_file}")

def save_csv(csv_file : str, result : list) -> None:
    with open(csv_file, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(result[0].keys())
        for i in range(len(result)):
            csv_writer.writerow(result[i].values())
        print(f"data saved to {csv_file}")

def sort_data(result_unsorted : list) -> list:
    """
    Takes list of lists containing page and list of dicts and returns list of dicts ordered by page number.

    [[page, dicts_page],...] -> [dicts_1[0], ..., dicts_1[-1], dicts_2[0], ...]
    """
    result = []
    print("sorting data")
    for i in range(len(result_unsorted)):
        for j in range(len(result_unsorted)):
            if result_unsorted[j][0] == i+1:
                result.extend(result_unsorted[j][1])
                del result_unsorted[j]
                break
    return result

async def main(ntasks: int) -> None:
    """
    Main coroutine that handles initialization tasks and their proper termination.
    Needs to be run as 'asyncio.run()' argument.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(scrape(url, session, task_id)) for task_id in range(ntasks)]
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    t_start = time.perf_counter()

    #url of api from site ("https://www.dent.cz/zubni-lekari") inspection using devtools
    url = "https://is-api.dent.cz/api/v1/web/workplaces"

    json_file = 'data.json'
    csv_file = 'data.csv'
    ntasks = 10

    page = 0
    result_unsorted = []

    #get rid of "RuntimeError: Event loop is closed" on Windows
    if platform.system()=='Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    #create and start even loop with ntasks number of tasks
    asyncio.run(main(ntasks))

    result = sort_data(result_unsorted)
    
    save_json(json_file, result)
    save_csv(csv_file, result)
    
    print(f"finished in {time.perf_counter() - t_start} sec")