# README: youtube-transcript-scraper 

## about

Youtube offers an API to download the transcripts but they limit how much you can access pretty severely.
This patchwork of functions and programs is designed to facilitate channel data access, video data access and transcript scraping

benchmark fyi - About transcripts 15 per minute 

## requirements
* chromedriver (https://chromedriver.chromium.org/)
* pandas, `pip install pandas`
* python bindings for selenium `pip install selenium`
* google api credentials (https://developers.google.com/youtube/v3/getting-started)
* csv file with video IDs which you want to scrape OR
* csv file with channel IDs which you want to collect videos from 
* csv file with plalyist IDs which you want to collect videos from

## use
* download script
* create a directory called "transcripts" 
* modify `channel_data_ytAPI.py` with channel CSV (and playlist csv)
* First run the channel channel_data_ytAPI.py script if you do not have videoids yet
* if you have video Ids, then update the video csv path  in the `captions.py` file, and run `captions.py`
 
