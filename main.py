from parser_1 import *
import asyncio
import time

if __name__=='__main__':
    start_time = time.time()
    url = 'https://www.playmeo.com/activities/'
    asyncio.run(gather_data(url))
    print(f'Распарсило за {time.time()-start_time}')