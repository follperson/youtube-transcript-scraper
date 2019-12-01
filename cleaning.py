#!/usr/bin/env python3
import re
import os

tf = 'transcripts/untimed/UCaeO5vkdj5xOQHp4UmIN6dw/kOtq5bkEOSg.txt'

text_to_remove = {'\[.*\]',  # applause, music
          '[Tt]he following contains strong language and adult themes? and is intended for [a|an] mature audiences?',
          "video is brought to you by",
          '>>',
          '\(\s*cheers and applause\s*\)'}


def clean_dir(inroot):
    outroot = r'C:\Users\follm\Documents\CMU\Text Analysis\final-project\youtube-transcript-scraper\transcripts\cleaned'
    flog = open('transcript errors.txt', 'a+')
    ignore_files = flog.read()
    for root, dirs, files in os.walk(inroot):
        cur_out = root.replace(inroot, outroot)
        print(cur_out)
        if not os.path.exists(cur_out):
            os.makedirs(cur_out)
        for f in files:
            if os.path.exists(os.path.join(cur_out, f)):
                continue
            if f in ignore_files:
                continue
            print(f)
            if f.endswith('.txt'):
                with open(os.path.join(root, f)) as in_file:
                    try:
                        content = in_file.read()
                    except UnicodeDecodeError as ok:
                        flog.write(os.path.join(root, f))
                        print('Failed with ', f)
                        continue
                for ignore in text_to_remove:
                    # print(ignore)
                    content, n = re.subn(ignore, '', content)
                with open(os.path.join(cur_out, f), 'w') as out_file:
                    out_file.write(content)


if __name__ == '__main__':
    clean_dir(r'C:\Users\follm\Documents\CMU\Text Analysis\final-project\youtube-transcript-scraper\transcripts\untimed')
