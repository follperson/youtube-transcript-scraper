import credentials as cred
import pandas as pd
import googleapiclient.discovery
import googleapiclient.errors

version = '20191112_test'
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


def get_youtube_api_connection():
    api_service_name = "youtube"
    api_version = "v3"

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=cred.api_key)
    return youtube


def get_data_from_api(channel_id, youtube=None, get_video=True):
    if youtube is None:
        youtube = get_youtube_api_connection()
    upload_id, channel_data = get_channel_info(channel_id, youtube)
    video_data = {}
    if get_video:
        video_data = get_videos_from_playist_id(upload_id, youtube)
    return channel_data, video_data


def get_channel_info(channel_id, youtube):
    channel_request = youtube.channels().list(
        part='contentDetails,statistics,snippet',
        id=channel_id
    )
    channel_response = channel_request.execute()
    upload_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    channel_info_cols=['title','description','customUrl','publishedAt']
    stats = channel_response['items'][0]['statistics']
    info = channel_response['items'][0]['snippet']
    channel_cols = ['viewCount','commentCount','subscriberCount','videoCount']
    channel_data = {col: stats[col]for col in channel_cols}
    channel_data.update({col:info[col] for col in channel_info_cols if col in info})
    return upload_id, channel_data


def get_videos_from_playist_id(upload_id, youtube=None):
    part = 'snippet'
    max_results = 50
    playlist_request = youtube.playlistItems().list(playlistId=upload_id, part=part, maxResults=max_results)
    playlist_response = playlist_request.execute()
    cols = ['publishedAt','channelId','title','description','channelTitle']
    all_video_data={}
    max_steps = 6
    steps = 0
    while 'nextPageToken' in playlist_response and steps < max_steps:
        for item in playlist_response['items']:
            all_video_data[item['snippet']['resourceId']['videoId']] ={col:item['snippet'][col] for col in cols}
        next_token = playlist_response['nextPageToken']
        playlist_request = youtube.playlistItems().list(playlistId=upload_id,
                                                        part=part,
                                                        maxResults=max_results,
                                                        pageToken=next_token)
        playlist_response = playlist_request.execute()
        steps += 1
    return all_video_data


def main():
    df = pd.read_csv('channels.csv')
    df = df.loc[pd.isnull(df['Completed'])]
    channel_data = {}
    video_data = {}
    youtube = get_youtube_api_connection()
    for i in df.index:
        print(df.loc[i, :])
        channel_id = df.loc[i,'channelId']

        c_data, v_data = get_data_from_api(channel_id, youtube, True)
        channel_data.update({channel_id:c_data})
        video_data.update(v_data)
    df_channel = pd.DataFrame(channel_data).T.reset_index().rename(columns={'index':'channelId'})
    df_video = pd.DataFrame.from_dict(video_data).T.reset_index().rename(columns={'index':'videoId'})
    df_channel.to_csv('data/channel_data_ytapi_{}.csv'.format(version), index=False)
    df_video.to_csv('data/video_data_ytapi_{}.csv'.format(version), index=False)
    df_video.to_csv('data/video_data_ytapi_{}-inflight.csv'.format(version), index=False)


if __name__ == '__main__':
    main()
