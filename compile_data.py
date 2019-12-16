# This a bit of a convenience program. Assuming we have scraped and downloaded the channel and YouTube data several
# times, with multiple output files we need to compile our data into a clean and singular video and channel data files
import pandas as pd
import re
import os

version = '20191212'
root = r'data'
video_filepaths = reversed([os.path.join(root, f) for f in os.listdir(root) if re.match('video_data.*-inflight\.csv',f)])
channel_filepaths = reversed([os.path.join(root, f) for f in os.listdir(root) if re.match('channel_data_ytapi.*\.csv',f)])
channel_gb = ['channelId']
video_gb = ['videoId', 'channelId', 'playlistId']
video_fillna = ['playlistId']


def compile_data(list_of_filepaths, groupby_cols, fillna_cols=()):
    df_master = pd.DataFrame()
    for f in list_of_filepaths:
        df = pd.read_csv(f)
        for col in fillna_cols:
            if col not in df:
                df[col] ='Unprovided'
            else:
                df[col] = df[col].fillna('Unprovided')
        df_master = df_master.append(df)
    return df_master.groupby(groupby_cols).first().reset_index()


def video_data():
    df_video = compile_data(video_filepaths, video_gb, video_fillna)
    df_playlist = pd.read_csv('playlist.csv')
    df_playlist_videos = pd.merge(df_video[['videoId', 'playlistId']],
                                  df_playlist[['playlistId', 'playlistName', 'Political Leaning','Type']],
                                  how='inner', on='playlistId')
    df_video = pd.merge(df_video, df_playlist_videos, how='outer', on=['videoId', 'playlistId'])
    df_video = df_video[~df_video.videoId.isin(df_playlist_videos.videoId) |
                        (df_video.videoId.isin(df_playlist_videos.videoId) & pd.notnull(df_video['playlistName']))]
    df_video['playlistName'] = df_video['playlistName'].fillna(df_video['channelTitle'])
    return df_video.groupby(['playlistName','videoId','channelId']).first().reset_index()


def channel_data():
    df_channel = compile_data(channel_filepaths, channel_gb)
    df_orig = pd.read_csv('channels.csv')[['channelId','Political Leaning','Type']]
    return pd.merge(df_channel, df_orig, how='outer', on='channelId')


def main():
    df_channel = channel_data()
    df_channel.to_csv('data/COMPILED channel_data_{}.csv'.format(version))

    df_video = video_data()
    df_video.to_csv('data/COMPILED video_data_{}.csv'.format(version))

if __name__ == '__main__':
    main()
