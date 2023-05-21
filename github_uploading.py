import os
import pandas as pd
from datetime import datetime

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.auth.transport.requests
import requests
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

def get_credentials():
  credentials = None #initialise
  if os.path.exists('token.pickle'):
      print('Loading Credentials From File...')
      with open('token.pickle', 'rb') as token:
          credentials = pickle.load(token)

  # If there are no valid credentials available, then either refresh the token or log in.
  if not credentials or not credentials.valid:
      if credentials and credentials.expired and credentials.refresh_token:
          print('Refreshing Access Token...')
          credentials.refresh(Request())
      else:
          print('Fetching New Tokens...')
          flow = InstalledAppFlow.from_client_secrets_file(
              'client_secrets.json',
              scopes=[
                  'https://www.googleapis.com/auth/youtube',
                  'https://www.googleapis.com/auth/youtube.upload',
                  'https://www.googleapis.com/auth/youtube.force-ssl'
              ]
          )

          flow.run_local_server(port='choose a port to use', prompt='consent')
          credentials = flow.credentials

          # Save the credentials for the next run
          with open('token.pickle', 'wb') as f:
              print('Saving Credentials for Future Use...')
              pickle.dump(credentials, f)
  return credentials

def generate_video_details(dir_upload, video_name, video_songs):
    video_to_upload = os.path.join(dir_upload, f"{video_name}.mp4")
    video_title = video_name
    video_description = f"Royalty-free music from: https://pixabay.com/music/\nSongs used:\n{video_songs}"
    video_category = 2
    video_tags = "checkpoint,camera,jb,sg,woodlands,tuas,causeway,traffic".split(",")
    video_privacy = 'public' # ("public", "private", "unlisted")

    body=dict(
        snippet=dict(
        title=video_title,
        description=video_description,
        tags=video_tags,
        categoryId=video_category
        ),
        status=dict(
        privacyStatus=video_privacy,
        selfDeclaredMadeForKids=False
        )
    )
    return video_to_upload, body

def add_video_to_playlist(youtube,videoID,playlistID):
  add_video_request=youtube.playlistItems().insert(
  part="snippet",
  body={
    'snippet': {
      'playlistId': playlistID, 
      'resourceId': {
              'kind': 'youtube#video',
          'videoId': videoID
        }
    #'position': 0
    }
  }
  ).execute()
  return add_video_request


'''
##########
MAIN
##########
'''

no_of_vids_to_process_hardlimit = 6 # uploads cost 1600 tokens, 10 000 a day --> 6 videos a day
dir_upload = r'directory of videos to be uploaded'
dir_archive = r'directory to archive the files after uploading'
playlistID = 'playlist ID'

videos_list = [vid for vid in os.listdir(dir_upload) if vid.endswith(".mp4")]
print(f'Uploading up to {no_of_vids_to_process_hardlimit} of {len(videos_list)} available videos:\n{videos_list}')
no_of_vids = min(no_of_vids_to_process_hardlimit, len(videos_list)) # lower of either the stated hardlimit or number of videos in the upload folder
date_today = datetime.today().strftime('%Y-%m-%d')
videos_processed = {}

for i in range(0, no_of_vids):
    df = pd.read_csv('log.csv',index_col='Date')
    video_name = videos_list[i].replace('.mp4','')
    video_songs = df.at[video_name.split(" ")[0], "Songs"]
    print(f"PROCESSING {i+1}/{no_of_vids}: {video_name}\nSongs: {video_songs}")

    # Move to the archive folder
    print('Moving video and zip file to archive folder')
    os.replace(os.path.join(dir_upload, f"{video_name}.mp4"),os.path.join(dir_archive, f"{video_name}.mp4"))
    os.replace(os.path.join(dir_upload, f"{video_name}.zip"),os.path.join(dir_archive, f"{video_name}.zip"))

    credentials = get_credentials()
    video_to_upload, body = generate_video_details(dir_archive, video_name, video_songs)
    youtube = build("youtube", "v3", credentials=credentials)
    insert_request = youtube.videos().insert(part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_to_upload, chunksize=-1, resumable=True)
    )
    print(f'Uploading now: {video_name}')

    try:
        response = insert_request.execute()
        #print(response)
        video_id = response['id']
        print(f'Upload successful. Adding video id: {video_id} to playlist id: {playlistID}.')
        add_video_request = add_video_to_playlist(youtube, video_id, playlistID)
        #print(add_video_request)
    except Exception as e:
        print(e)
        videos_processed[video_name] = 'Failure'
        df.loc[video_name.split(" ")[0], 'Uploaded'] = f'Failed on {date_today}.'
        df.to_csv('log.csv') # At the end, export the log 
        print(f'Issue, video ID: {video_id}.\nMove the videos back to upload folder\n')
        continue
    else:
        videos_processed[video_name] = 'Success'
        df.loc[video_name.split(" ")[0], 'ID'] = video_id
        df.loc[video_name.split(" ")[0], 'Uploaded'] = date_today       
        df.to_csv('log.csv') # At the end, export the log 
        print(f'Success, video ID: {video_id}\n')

print(f'Report:\n{videos_processed}')          