import credentials as cred
import pandas as pd
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]



def get_videos_from_channel_id(channel_id):
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = cred.api_key

    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

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
    channel_data = {col:stats[col]for col in channel_cols}
    channel_data.update({col:info[col] for col in channel_info_cols if col in info})
    playlist_request = youtube.playlistItems().list(playlistId=upload_id, part='snippet', maxResults=50)
    playlist_response = playlist_request.execute()
    cols = ['publishedAt','channelId','title','description','channelTitle']
    all_video_data={}
    max_steps = 6
    steps = 0
    while 'nextPageToken' in playlist_response and steps < max_steps:
        for item in playlist_response['items']:
            all_video_data[item['snippet']['resourceId']['videoId']] ={col:item['snippet'][col] for col in cols}
        next_token = playlist_response['nextPageToken']
        playlist_request = youtube.playlistItems().list(playlistId=upload_id, part='snippet', maxResults=50,
                                                        pageToken=next_token)
        playlist_response = playlist_request.execute()
        steps += 1
    return channel_data, all_video_data



def main():
    df = pd.read_csv('channels.csv')
    channel_data = {}
    video_data = {}
    for i in df.index:
        print(df.loc[i, :])
        channel_id =df.loc[i,'channel_id']
        c_data, v_data = get_videos_from_channel_id(channel_id)
        channel_data.update({channel_id:c_data})
        video_data.update(v_data)
    df_channel = pd.DataFrame(channel_data)
    df_video = pd.DataFrame.from_dict(video_data).T
    df_channel.to_csv('channel_data_ytapi.csv')
    df_video.to_csv('video_data_ytapi.csv')


if __name__ == '__main__':
    main()
