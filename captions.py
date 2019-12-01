import shutil
import psutil
import os
import re
import random
import pandas as pd
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium import webdriver

n = 5
version = '20191201_{}-{}'.format(str(7000*(n-1)),str(7000*(n)))
print(version)
video_info_fp = 'data/video_data_ytapi_{}-inflight.csv'.format(version)
video_id_col = 'videoId'			# column storing video id
channel_col = 'channelId'
headless = True
OUTDIR = './transcripts/'
filepattern = 'tanscript_{}.txt'
OPTIONS = webdriver.ChromeOptions()
OPTIONS.headless=True
OPTIONS.add_argument('--mute-audio')
YOUTUBE_BASE = "https://www.youtube.com/watch?v="
OUTER_FRAME_XPATH = '//body[@dir="ltr"]'
TRANSCRIPT_BLOCKED = "No Transcript Available"
TRANSCRIPT_FAILED = 'FAILED'

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
    DATE_XPATH = '//div[@id="date"]//yt-formatted-string'
    VIEWS_XPATH = '//div[@id="count"]//span[@class="view-count style-scope yt-view-count-renderer"]'
    DURATION_XPATH = '//div[@class="ytp-bound-time-right"]'

    def __init__(self, video_id, source_channel, driver=None):
        self.video_id = video_id
        self.txt_path = 'transcripts/untimed/{}/{}.txt'.format(source_channel, self.video_id)
        self.transcript = ''
        self.transcript_timed = ''
        self.description = ''
        self.title = ''
        self.likes = ''
        self.dislikes = ''
        self.views = ''
        self.date = ''
        self.duration = ''
        self.driver = driver
        self.default_waittime = 3
        self.n_tries = 3
        self.limited_scope = False

    def wait_for_element(self, until, waittime=None):
        if waittime is None:
            waittime = self.default_waittime
        return WebDriverWait(self.driver, waittime).until(until)

    def start_driver(self):
        self.driver = get_driver()

    def get_video_info(self):
        print("Begin", self.video_id)
        if self.driver is None:
            self.start_driver()
        self.navigate_to_page()
        self.log_get(self.get_transcript, self.transcript_timed, self.transcript)
        self.log_get(self.get_title, self.title)
        self.log_get(self.get_description, self.description)
        self.log_get(self.get_date, self.date)
        self.log_get(self.get_duration, self.duration)
        if not self.limited_scope:
            self.log_get(self.get_rating, self.likes, self.dislikes)
            self.log_get(self.get_views, self.views)

    def close(self):
        f = open('complete/{}'.format(self.video_id), 'w')
        f.close()

    def navigate_to_page(self):
        self.driver.get(YOUTUBE_BASE + self.video_id)
        random_wait(2, 5)
        try:
            path = self.driver.find_element_by_xpath('//paper-button[@aria-label="I understand and wish to proceed"]')
            path.click()
            random_wait(5,10)
            self.limited_scope = True
        except NoSuchElementException:
            pass


    def get_views(self):
        element = self.wait_for_element(EC.presence_of_element_located((By.XPATH, self.VIEWS_XPATH)))
        self.views = element.text

    def get_date(self):
        element = self.wait_for_element(EC.presence_of_element_located((By.XPATH,self.DATE_XPATH)))
        self.date = element.text

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

    def get_duration(self):
        element = self.wait_for_element(EC.presence_of_element_located((By.XPATH, self.DURATION_XPATH)))
        self.duration = element.text

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
        menu_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH, self.MENU_TRIGGER)))
        menu_button.click()

        transcript_button = self.wait_for_element(EC.element_to_be_clickable((By.XPATH, self.TRANSCRIPT_BUTTON)))
        if 'transcript' not in transcript_button.text:
            self.transcript = TRANSCRIPT_BLOCKED
            return
        transcript_button.click()

        transcript_element = self.wait_for_element(EC.presence_of_element_located(
            (By.XPATH, self.FULL_TRANSCRIPT_XPATH)), 10)
        transcript_raw = transcript_element.text
        text = re.split('\d*:\d{2}\n', transcript_raw)[1:]
        times = re.findall('\d*:\d{2}\n', transcript_raw)
        df = pd.DataFrame(zip(times,text),columns=['time','text']).replace('\n', '')
        df['text'] = df['text'].str.replace('\n', '')
        df['time'] = df['time'].str.replace('\n', '')
        self.transcript = ' '.join(df['text'])
        self.transcript_timed = df
        self.write_transcript_to_file()

    def write_transcript_to_file(self):
        if not os.path.exists(os.path.dirname(self.txt_path)):
            os.makedirs(os.path.dirname(self.txt_path))
        with open(self.txt_path, 'w',encoding='utf_8',errors='ignore') as txt:
            txt.write(self.transcript)

def check_completed(path):
    if os.path.exists(path):
        try:
            with open(path) as fopen:
                content = fopen.read()
        except UnicodeDecodeError:
            return True
        if len(content) > 10:
            return True
    return False


def main():
    driver = get_driver()

    driver_proc = psutil.Process(driver.service.process.pid)
    df_video_meta = pd.read_csv(video_info_fp)
    df_video_meta = df_video_meta.drop_duplicates(video_id_col).set_index(video_id_col)
    cols = ['description-scraped', 'title-scraped', 'likes-scraped', 'dislikes-scraped', 'views-scraped',
            'date-scraped', 'duration-scraped', 'transcript-scraped']
    for col in cols:
        if col not in df_video_meta.columns:
            df_video_meta[col] = pd.np.nan

    for video_id in df_video_meta.index:
        ts = df_video_meta.loc[video_id, 'transcript-scraped']
        if not (pd.isnull(ts) | (ts == TRANSCRIPT_FAILED)):
            continue
        source_channel = df_video_meta.loc[video_id, channel_col]
        td = TranscriptDriver(video_id, driver=driver, source_channel=source_channel)
        if check_completed(td.txt_path):
            df_video_meta.loc[video_id, 'transcript-scraped'] = True
            continue

        td.get_video_info()

        if td.transcript == '': transcript_found = TRANSCRIPT_FAILED
        elif td.transcript == TRANSCRIPT_BLOCKED: transcript_found = TRANSCRIPT_BLOCKED
        else: transcript_found = True
        df_video_meta.loc[
            video_id, cols] = td.description, td.title, td.likes, td.dislikes, td.views, td.date, td.duration, transcript_found
        if not check_process(driver_proc):
            driver = get_driver()
            driver_proc = psutil.Process(driver.service.process.pid)
        td.close()
        df_video_meta.to_csv(video_info_fp, encoding='utf_8', index=True)
    if check_process(driver_proc):
        driver.quit()


if __name__ == '__main__':
    main()
