# This program is used to read your channelId list, and then access the YouTube API
# to get links for the most recent videos uploaded by that channel.
# an also use prespecified PlaylistID instead of channelId, in case you need to only review one playlist instead of
# all content from a given channel.

import credentials as cred
import pandas as pd
import googleapiclient.discovery
import googleapiclient.errors
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

version = '20191202' # filename for you output file
channels_csv = 'channels.csv'
channel_id_col = 'channelId'
video_id_col = 'videoId'
playlist_id_col = 'playlistId'
playlist_csv = 'playlist.csv'
max_videos_per_playlist_channel = 300

def get_youtube_api_connection():
    api_service_name = "youtube"
    api_version = "v3"

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=cred.api_key)
    return youtube


def get_data_from_api(channel_id, youtube=None, get_video=True):
    if youtube is None:
        # create a new YouTube API connection
        youtube = get_youtube_api_connection()

    # get our channel data an the playlist id for the channel uploads
    upload_id, channel_data = get_channel_info(channel_id, youtube)

    video_data = {}
    if get_video:  # we want to download videos as well as the channel data
        video_data = get_videos_from_playist_id(upload_id, youtube)
    return channel_data, video_data


def get_channel_info(channel_id, youtube):
    channel_request = youtube.channels().list(
        part='contentDetails,statistics,snippet',
        id=channel_id
    )
    channel_response = channel_request.execute()

    # Only way to get the videos uploaded by the channel is via the uploads playlist
    upload_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # get some channel level statistics
    stats = channel_response['items'][0]['statistics']
    channel_cols = ['viewCount','commentCount','subscriberCount','videoCount']
    channel_data = {col: stats[col] for col in channel_cols}
    info = channel_response['items'][0]['snippet']
    channel_info_cols = ['title', 'description', 'customUrl', 'publishedAt']
    channel_data.update({col: info[col] for col in channel_info_cols if col in info})

    return upload_id, channel_data


def get_videos_from_playist_id(playlist_id, youtube):
    """
        take in the 
    :param playlist_id:
    :param youtube:
    :return:
    """
    # youtube api parameters
    part = 'snippet'
    max_results = 50
    playlist_request = youtube.playlistItems().list(playlistId=playlist_id, part=part, maxResults=max_results)
    playlist_response = playlist_request.execute()

    # video data points to collect
    video_info_cols = ['publishedAt','channelId','title','description','channelTitle']
    all_video_data = {}
    max_steps = max_videos_per_playlist_channel // 50
    steps = 0

    # iterate thru the current response and collect the video data
    for item in playlist_response['items']:
        video_id = item['snippet']['resourceId']['videoId']
        all_video_data[video_id] = {col: item['snippet'][col] for col in video_info_cols}

    # get the next chunk of videos
    while 'nextPageToken' in playlist_response and steps < max_steps:
        next_token = playlist_response['nextPageToken']
        playlist_request = youtube.playlistItems().list(playlistId=playlist_id, part=part, maxResults=max_results,
                                                        pageToken=next_token)
        playlist_response = playlist_request.execute()
        for item in playlist_response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            all_video_data[video_id] = {col: item['snippet'][col] for col in video_info_cols}
        steps += 1

    # tag on the playlist source so we can merge later on!
    for video in all_video_data:
        all_video_data[video].update({'playlistId': playlist_id})
    return all_video_data


def download_channel_data_and_videos():
    # load our channel ids
    df = pd.read_csv(channels_csv, encoding='utf-8')
    channel_data = {}
    video_data = {}

    # start the youtube api connection
    youtube = get_youtube_api_connection()
    for i in df.index:
        print(df.loc[i, :])
        channel_id = df.loc[i, channel_id_col]
        c_data, v_data = get_data_from_api(channel_id, youtube, True)
        channel_data.update({channel_id: c_data})
        video_data.update(v_data)

    # save and write our data
    df_channel = pd.DataFrame(channel_data).T.reset_index().rename(columns={'index':channel_id_col})
    df_video = pd.DataFrame.from_dict(video_data).T.reset_index().rename(columns={'index':video_id_col})
    df_channel.to_csv('data/channel_data_ytapi_{}.csv'.format(version), index=False)
    df_video.to_csv('data/video_data_ytapi_{}.csv'.format(version), index=False)
    df_video.to_csv('data/video_data_ytapi_{}-inflight.csv'.format(version), index=False)


def download_playlist_videos():
    df = pd.read_csv(playlist_csv, encoding='utf-8')
    video_data = {}
    youtube = get_youtube_api_connection()
    for i in df.index:
        print(df.loc[i, :])
        playlist_id = df.loc[i, playlist_id_col]
        v_data = get_videos_from_playist_id(playlist_id, youtube)
        video_data.update(v_data)
    df_video = pd.DataFrame.from_dict(video_data).T.reset_index().rename(columns={'index': video_id_col})
    df_video.to_csv('data/video_data_ytapi_{}_playlist.csv'.format(version), index=False)
    df_video.to_csv('data/video_data_ytapi_{}_playlist-inflight.csv'.format(version), index=False)


def main():
    # download_channel_data_and_videos()
    # download_playlist_videos()
    pass

if __name__ == '__main__':
    main()
