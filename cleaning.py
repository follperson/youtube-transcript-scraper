#!/usr/bin/env python3
import re


f = 'transcripts/untimed/UCaeO5vkdj5xOQHp4UmIN6dw/kOtq5bkEOSg.txt'

class TranscriptCleaner:
    suite = {'\[.*\]': '',
             '[Tt]he following contains strong language and adult themes? and is intended for [a|an] mature audiences?': '',
             "video is brought to you by":'',
             '>>':'',
             '\(\s*cheers and applause\s*\)':''}
