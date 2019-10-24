# modify these values
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver

import os.path
import random
import csv
import pandas as pd
from time import sleep
filename = 'channels.csv'			# filname with video ids
colname = 'channel_id'					# column storing video ids
waittime = 10						# seconds browser waits before giving up
# random seconds range before loading next video id
sleeptime = [5, 15]

headless = True


OUTDIR = './transcripts/'
filepattern = 'tanscript_{}.txt'
OPTIONS = webdriver.ChromeOptions()
# OPTIONS.headless = True

YOUTUBE_BASE = "https://www.youtube.com/channel/{}/videos"
OUTER_FRAME_XPATH = '//body[@dir="ltr"]'

def random_wait(smin=5, smax=15):
    sleep(random.uniform(smin, smax))


def get_driver():
    return webdriver.Chrome(chrome_options=OPTIONS)


class ChannelDriver:
    THUMBNAIL_LINK = '//a[@class="yt-simple-endpoint inline-block style-scope ytd-thumbnail"]'

    def __init__(self, channel_id, driver=None):
        print("Begin",channel_id)
        self.channel_id = channel_id
        self.write_file = 'channels/video links {}.csv'.format(self.channel_id)
        if os.path.exists('complete/complete-channels/{}'.format(self.channel_id)):
            return
        self.driver = driver
        self.default_waittime = 3

    def start_driver(self):
        self.driver = get_driver()

    def wait_for_element(self, until, message=''):
        try:
            return WebDriverWait(self.driver, self.default_waittime).until(until)
        except TimeoutException:
            self.driver.find_element_by_xpath(OUTER_FRAME_XPATH).send_keys(Keys.ESCAPE)
            return WebDriverWait(self.driver, self.default_waittime).until(until)

    def go_to_channel(self):
        self.driver.get(YOUTUBE_BASE.format(self.channel_id))
        random_wait(5, 6)

    def main(self):
        if self.driver is None:
            self.driver = get_driver()
        self.go_to_channel()
        self.get_videos()


    def get_videos(self, n=10):
        video_ids = []
        main_page = self.wait_for_element(EC.element_to_be_clickable((By.XPATH, OUTER_FRAME_XPATH)))
        for i in range(n):
            main_page.send_keys(Keys.PAGE_DOWN, Keys.PAGE_DOWN)
            sleep(.5)
        link_elements = self.wait_for_element(EC.presence_of_all_elements_located((By.XPATH, self.THUMBNAIL_LINK)))
        links = [link.get_attribute('href') for link in link_elements]
        video_ids += [link.split('=')[-1] for link in links if link is not None]
        df = pd.DataFrame(data=video_ids, columns=['video_id'])
        df['channel_id'] = self.channel_id
        df.to_csv(self.write_file)

def get_videos(channel_id,driver):
    td = ChannelDriver(channel_id, driver)
    if os.path.exists('complete/complete-channels/{}'.format(channel_id)):
        return
    td.main()
    f = open('complete/complete-channels/{}'.format(channel_id),'w')
    f.close()


if __name__ == '__main__':
    df = pd.read_csv(filename)
    df = df[pd.notnull(df['valid channel id'])]
    driver = get_driver()
    df[colname].apply(lambda x: get_videos(x, driver))
