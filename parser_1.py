from bs4 import BeautifulSoup as bs
import time
import asyncio
import aiohttp
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

#получение ссылок на активности
async def gather_data(url):
    browser = webdriver.Edge()
    browser.get(url)
    for i in range(22):
        time.sleep(5)
        button = browser.find_element(By.ID, 'btn-load-more-activities')
        WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'btn-load-more-activities')))
        ActionChains(browser)\
            .scroll_to_element(button)\
            .perform()
        button.click()
    
    activities = []
    image = []
    for i in range(1,23):
        activities.append(browser.find_element(By.ID, f'activities-group-{i}'))
    for activity in activities:
        image.append(activity.find_elements(By.CLASS_NAME, 'image'))
    a = []
    link = []
    for img in image:
        for img1 in img:
            a.append(img1.find_element(By.TAG_NAME, 'a'))
    for a1 in a:
        link.append(a1.get_attribute('href'))
    st_accept = "text/html" #Для получения Html

    #Имитируем подключение через браузер Mozilla на macOS
    st_useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"

    #Формируем хеш заголовки
    headers = {
    "Accept": st_accept,
    "User-Agent": st_useragent
    }
    async with aiohttp.ClientSession() as session:
        tasks = []
        for a1 in link:
            task = asyncio.create_task(pars_activ(session, a1))
            tasks.append(task)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print('xui')
        #print(a)
#парс активности
async def pars_activ(session, url):
    #Имитируем подключение через браузер Mozilla на macOS
    st_useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"
    st_accept = "text/html" #Для получения Html
#Формируем хеш заголовки
    headers = {
    "Accept": st_accept,
    "User-Agent": st_useragent
    }
    async with session.get(url = url, headers=headers) as responce:

        insrt = []
        tags = []
        test = []
        responce_text = await responce.text()
        soup = bs(responce_text, "lxml")
        name = soup.find('div', class_='inner').find('h1').text
        if(soup.find('div', class_='tags').find('ul').findAll('li')!=None):
            tags = soup.find('div', class_='tags').find('ul').findAll('li')
        print(tags)
        for tag in tags:
            test.append(tag.find('span').text)
        type_ = test[0]
        time_ = test[1]
        col_vo = test[2]
        dinamic = test[3]
        test1 = []
        instruction = ''
        if(soup.find('div', class_='draw')!=None):
            if(soup.find('ol')!=None):
                test1 = soup.find('ol').findAll('li')
        for tes in test1:
            insrt.append(tes.text)
        for ins in insrt:
            instruction += ins 
        instruction = instruction.replace(',', '')
        dat = {'title': name,
               'type': type_,
               'time': time_,
               'quantity': col_vo,
               'activity': dinamic,
               'instruction': instruction}
        write_csv(dat)

def write_csv(data):
    with open('result.csv', 'a', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([data['title'],
                         data['type'],
                         data['quantity'],
                         data['activity'],
                         data['instruction']])
