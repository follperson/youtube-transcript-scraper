import shutil
import psutil
import os
import re
import random
import pandas as pd
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

filename = 'meta_input.csv'			# filname with video ids
colname = 'video_id'					# column storing video id
headless = True
OUTDIR = './transcripts/'
filepattern = 'tanscript_{}.txt'
OPTIONS = webdriver.ChromeOptions()
#OPTIONS.headless=True
YOUTUBE_BASE = "https://www.youtube.com/watch?v="
OUTER_FRAME_XPATH = '//body[@dir="ltr"]'



def random_wait(smin=5, smax=15):
    sleep(random.uniform(smin, smax))


def get_driver():
    return webdriver.Chrome(chrome_options=OPTIONS)


def check_process(driver_process):
    chrome_proc = driver_process.children()
    if chrome_proc:
        chrome_proc = chrome_proc[0].is_running()
        if chrome_proc:
            return True
        else:
            chrome_proc.kill()
            return False
    return False

class TranscriptDriver:
    MENU_TRIGGER = '//div[@id="container"]//yt-icon-button[@class="dropdown-trigger style-scope ytd-menu-renderer"]'
    TRANSCRIPT_BUTTON = '(//ytd-menu-popup-renderer//*/yt-formatted-string)[2]'
    FULL_TRANSCRIPT_XPATH = '//ytd-transcript-body-renderer'
    CUE_XPATH = '//ytd-transcript-body-renderer//div[@class="cues style-scope ytd-transcript-body-renderer"]'
    CUE_TIME_XPATH = '//ytd-transcript-body-renderer//div[@class="cue-group-start-offset style-scope ytd-transcript-body-renderer"]'
    TITLE_XPATH = '//h1[@class="title style-scope ytd-video-primary-info-renderer"]'
    DESCRIPTION_XPATH = '//div[@id="description"]'
    RATINGS_XPATH = '//yt-formatted-string[@id="text" and @class="style-scope ytd-toggle-button-renderer style-text"]'

    def __init__(self, video_id,driver=None):
        self.video_id = video_id
        self.csv_path = 'transcripts/timed/{}.csv'.format(self.video_id)
        self.txt_path = 'transcripts/untimed/{}.txt'.format(self.video_id)
        self.transcript = ''
        self.transcript_timed = ''
        self.description = ''
        self.title = ''
        self.likes = ''
        self.dislikes = ''
        print("Begin", video_id)
        self.driver = driver
        self.default_waittime = 3
        self.n_tries = 5

    def wait_for_element(self, until, waittime=None):
        if waittime is None:
            waittime = self.default_waittime
        return WebDriverWait(self.driver, waittime).until(until)

    def start_driver(self):
        self.driver = get_driver()

    def get_video_info(self):
        if self.driver is None:
            self.start_driver()
        self.navigate_to_page()
        self.log_get(self.get_transcript, self.transcript_timed, self.transcript)
        self.log_get(self.get_title,self.title)
        self.log_get(self.get_description,self.description)
        self.log_get(self.get_rating,self.likes,self.dislikes)
        f = open('complete/{}'.format(self.video_id),'w')
        f.close()

    def navigate_to_page(self):
        self.driver.get(YOUTUBE_BASE + self.video_id)
        random_wait(2, 5)

    def get_title(self):
        title_element = self.wait_for_element(EC.presence_of_element_located((By.XPATH,self.TITLE_XPATH)))
        self.title = title_element.text

    def get_rating(self):
        ratings = self.wait_for_element(EC.presence_of_all_elements_located((By.XPATH,self.RATINGS_XPATH)))
        self.likes = ratings[0].get_attribute('aria-label')
        self.dislikes = ratings[1].get_attribute('aria-label')

    def get_description(self):
        description_element = self.wait_for_element(EC.presence_of_element_located((By.XPATH,self.DESCRIPTION_XPATH)))
        self.description = description_element.text

    def get_comments(self):
        pass

    def log_get(self, func, *args):
        if not all([check == '' for check in args]):
            return
        for i in range(self.n_tries):
            try:
                func()
                return
            except Exception:
                print('Unable to complete', func.__name__)
                pass
            random_wait(5,6)

    def get_transcript(self):
        menu_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH,self.MENU_TRIGGER)))
        menu_button.click()

        transcript_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH,self.TRANSCRIPT_BUTTON)))
        if 'transcript' not in transcript_button.text:
            print("No Transcript Available")
            return
        transcript_button.click()

        transcript_element = self.wait_for_element(EC.presence_of_element_located((By.XPATH, self.FULL_TRANSCRIPT_XPATH)), 10)
        transcript_raw = transcript_element.text
        text = re.split('\d*:\d{2}\n', transcript_raw)[1:]
        times = re.findall('\d*:\d{2}\n', transcript_raw)
        df = pd.DataFrame(zip(times,text),columns=['time','text']).replace('\n', '')
        df['text'] = df['text'].str.replace('\n', '')
        df['time'] = df['time'].str.replace('\n', '')
        self.transcript = ' '.join(df['text'])
        self.transcript_timed = df
        df.to_csv(self.csv_path,encoding='utf_8')
        with open(self.txt_path, 'w',encoding='utf_8',errors='ignore') as txt:
            txt.write(' '.join(df['text']))






def main():
    driver =get_driver()
    driver_proc = psutil.Process(driver.service.process.pid)

    for csv in os.listdir('channels'):
        print('--'*20,'Begin',csv,'--'*20)
        inflight = 'channels-mod/' + csv
        if not os.path.exists(inflight):
            shutil.copy('channels/' + csv, inflight)
        df = pd.read_csv(inflight)
        cols = ['description','title','likes','dislikes']
        for i in df.index:
            video_id = df.loc[i,colname]
            td = TranscriptDriver(video_id, driver=driver)
            if os.path.exists('complete/' + video_id):
                continue
            td.get_video_info()

            try:
                df.loc[i, cols] = td.description, td.title, td.likes, td.dislikes
            except KeyError:
                df = df.assign(**{col:'' for col in cols})
                df.loc[i, cols] = td.description, td.title, td.likes, td.dislikes

            if not check_process(driver_proc):
                driver = get_driver()
                driver_proc = psutil.Process(driver.service.process.pid)
            df.to_csv(inflight, encoding='utf_8')

    if check_process(driver_proc):
        driver.quit()


if __name__ == '__main__':
    main()
