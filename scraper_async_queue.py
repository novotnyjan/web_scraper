import asyncio
import aiohttp
import aiofiles
import json
import platform
from colorama import Fore

async def fetch_response(url : str, session : aiohttp.ClientSession, queue : asyncio.Queue, producer_id : int, error_wait = 0.5) -> None:
    """
    Coroutine that sends POST request with increasing page number with each call. Puts (request.json(), _page) into queue.
    Coroutine terminates when the response 'data' item is empty list. 
    """
    global page
    while True:
        page += 1
        _page = page

        #send post request and continue only if the response status is 200, otherwise try again after 'errow_wait' time
        while True:
            resp = await session.post(url, data = {"page": _page}, ssl=False)
            if resp.status == 200:
                print(Fore.BLUE+f"producer {producer_id} response status for page {_page} is {resp.status}")
                break
            print(Fore.BLUE+f"unexpected request status code for page {_page}: '{resp.status}', sending request again in {error_wait}")
            await asyncio.sleep(error_wait)

        resp = await resp.json()
        
        #if there are no data on current page, terminate task
        if resp['data'] == []:
            print(Fore.BLUE+f"no data on page {_page}, closing task {producer_id}")
            break
        
        print(Fore.BLUE+f"producer {producer_id} put data into queue")
        await queue.put((resp, _page))

async def process_response(queue : aiohttp.ClientSession, json_file : str, consumer_id: int) -> None:
    """
    Coroutine that parses data from queue and saves them into 'json_file' as [page, data] list in unordered manner.
    """
    while True:    
        resp, _page = await queue.get()
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

        async with aiofiles.open(json_file, 'a') as file:
            data_json = json.dumps(data)
            await file.write(data_json + "," + "\n")
            print(Fore.RED+f"consumer number {consumer_id} saved data from page {_page} to {json_file}")
        queue.task_done()

async def main(nprod: int, ncons: int) -> None:
    """
    Main coroutine that handles initialization of queue and tasks and their proper termination.
    Needs to be run as 'asyncio.run()' argument.
    """
    #initialize queue
    queue = asyncio.Queue()
    
    #open aiohttp ClientSession for sending requests
    async with aiohttp.ClientSession() as session:
        
        #initialize consumer and producer tasks
        producers = [asyncio.create_task(fetch_response(url, session, queue, producer_id)) for producer_id in range(nprod)]
        consumers = [asyncio.create_task(process_response(queue,json_file, consumer_id)) for consumer_id in range (ncons)]

        #wait for producers to terminate
        await asyncio.gather(*producers)
        print("all producer tasks closed")

        #wait for all pending tasks in queue to complete
        await queue.join()
        print("all tasks in queue processed")

        #close all consumer tasks
        for c in consumers:
            c.cancel()

if __name__ == '__main__':
    #url of api from site ("https://www.dent.cz/zubni-lekari") inspection using devtools
    url = "https://is-api.dent.cz/api/v1/web/workplaces"
    
    json_file = 'queue_data.json'
    nprod = 10
    ncons = 10
    
    page = 0

    #start file with "[" to make it proper json file
    with open(json_file,'w') as file:
        file.write("[\n")

    #get rid of "RuntimeError: Event loop is closed" on Windows
    if platform.system()=='Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    #create and start even loop with ntasks number of tasks
    asyncio.run(main(nprod,ncons))

    #get rid of "," at the end of file and append "]" to make it proper json file
    with open(json_file, "rb+") as file:
        file.seek(-10,2)
        last_line = file.readline()
        
        offset_last_line = 0
        while True:
            offset_last_line += 1
            end_line = last_line[-offset_last_line:]
            if b"," in end_line:
                break
        
        if b"\r" in end_line:
            end_line = b"\r\n]"
        else:
            end_line = b"\n]"

        file.seek(- offset_last_line,2)
        file.write(end_line)
        file.truncate()