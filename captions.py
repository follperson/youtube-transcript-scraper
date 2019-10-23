# modify these values
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

import os
import re
import random
import pandas as pd
from time import sleep
filename = 'meta_input.csv'			# filname with video ids
colname = 'video_id'					# column storing video ids
waittime = 10						# seconds browser waits before giving up
# random seconds range before loading next video id
sleeptime = [5, 15]

headless = True


OUTDIR = './transcripts/'
filepattern = 'tanscript_{}.txt'
OPTIONS = webdriver.ChromeOptions()
#OPTIONS.headless=True


def random_wait(smin=5, smax=15):
    sleep(random.uniform(smin, smax))



YOUTUBE_BASE = "https://www.youtube.com/watch?v="
OUTER_FRAME_XPATH = '//body[@dir="ltr"]'

class TranscriptDriver:
    MENU_TRIGGER = '//div[@id="container"]//yt-icon-button[@class="dropdown-trigger style-scope ytd-menu-renderer"]'
    TRANSCRIPT_BUTTON = '(//ytd-menu-popup-renderer//*/yt-formatted-string)[2]'
    FULL_TRANSCRIPT_XPATH = '//ytd-transcript-body-renderer'
    CUE_XPATH = '//ytd-transcript-body-renderer//div[@class="cues style-scope ytd-transcript-body-renderer"]'
    CUE_TIME_XPATH = '//ytd-transcript-body-renderer//div[@class="cue-group-start-offset style-scope ytd-transcript-body-renderer"]'

    def __init__(self, video_id):
        self.video_id = video_id
        self.csv_path = 'transcripts/timed/{}.csv'.format(self.video_id)
        self.txt_path = 'transcripts/untimed/{}.txt'.format(self.video_id)
        print("Begin", video_id)
        self.driver = None
        self.default_waittime = 3
        self.n_tries = 5

    def wait_for_element(self, until, message='', waittime=None):
        if waittime is None:
            waittime = self.default_waittime
        return WebDriverWait(self.driver, waittime).until(until)
        # except TimeoutException:
            #self.driver.find_element_by_xpath(OUTER_FRAME_XPATH).send_keys(Keys.ESCAPE)
            # return WebDriverWait(self.driver, waittime).until(until)

    def get_transcript(self):
        self.driver = webdriver.Chrome(chrome_options=OPTIONS)
        for i in range(self.n_tries):
            try:
                self._get_transcript()
                return 'Success'
            except (ElementClickInterceptedException, TimeoutException):
                print('Failed %s times' % (i + 1))
                continue
        return 'Fail'

    def _get_transcript(self):
        self.driver.get(YOUTUBE_BASE + self.video_id)
        random_wait(2,5)

        menu_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH,self.MENU_TRIGGER)),'Menu Button')
        menu_button.click()

        transcript_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH,self.TRANSCRIPT_BUTTON)),'Transcript Button')
        transcript_button.click()

        transcript_element = self.wait_for_element(EC.presence_of_element_located((By.XPATH, self.FULL_TRANSCRIPT_XPATH)),
                                                   'Transcript', 10)
        transcript_raw = transcript_element.text
        text = re.split('\d*:\d{2}\n', transcript_raw)[1:]
        times = re.findall('\d*:\d{2}\n', transcript_raw)
        df = pd.DataFrame(zip(times,text),columns=['time','text']).replace('\n', '')
        df['text'] = df['text'].str.replace('\n', '')
        df['time'] = df['time'].str.replace('\n', '')
        df.to_csv(self.csv_path,encoding='utf_8')
        with open(self.txt_path, 'w',encoding='utf_8',errors='ignore') as txt:
            txt.write(' '.join(df['text']))



def get_transcript(video_id):
    td = TranscriptDriver(video_id)
    if os.path.exists(td.csv_path) and os.path.exists(td.txt_path):
        return
    td.get_transcript()
    td.driver.quit()


df = pd.read_csv('channels/video links UC2PA-AKmVpU6NKCGtZq_rKQ.csv')
df[colname].apply(lambda x: get_transcript(x))
