# Music sourced from: https://pixabay.com/music/search/theme/background%20music/

from moviepy.editor import *
import os
import random
import shutil
import pandas as pd
from datetime import datetime

def create_video(dir_process, dir_upload, date_folder_name, frames_per_sec):
    image_folder = os.path.normpath(dir_process + '/' + date_folder_name)
    dateday = datetime.strptime(date_folder_name, '%Y-%m-%d').strftime('%A')
    video_name = os.path.normpath(dir_upload + '/' + date_folder_name + ' ' + dateday + '.mp4')
    images = [os.path.join(image_folder, img) for img in sorted(os.listdir(image_folder)) if img.endswith(".jpeg")]
    clip = ImageSequenceClip(images, fps=frames_per_sec)
    return image_folder, int(clip.duration), clip, video_name, dateday

def create_audio(dir_music_library, clip_duration, clip, video_name):
    available_music = [os.path.normpath(dir_music_library + '/' + song) for song in os.listdir(dir_music_library) if song.endswith(".mp3")]
    songs_used = [AudioFileClip(available_music.pop(random.choice(range(0, len(available_music)))))] # initialise with 1 random song
    audio_length = int(songs_used[0].duration)
    while True:
        if audio_length < clip_duration:
            print('Creating audio file')
            #print(f'Audio length {audio_length}/{clip_duration}, adding another track.')
            songs_used.append(AudioFileClip(available_music.pop(random.choice(range(0, len(available_music))))))
            audio_length = int(sum([song.duration for song in songs_used]))
            continue
        else:
            songs_used_titles = [song.filename for song in songs_used]
            print(f'Audio length {audio_length}/{clip_duration}. Songs: {songs_used_titles}')
            break

    # Create single audio file
    audio_clip = concatenate_audioclips(songs_used).set_duration(clip_duration)
    #print('Created audio file')

    #clip = VideoFileClip(clip) # to import another clip
    videoclip = clip.set_audio(audio_clip)
    videoclip.audio_fadeout(5)
    videoclip.write_videofile(video_name)
    return songs_used_titles

def zip_and_delete_pictures(dir_process, dir_upload, date_folder_name, dateday):
    print('Creating zip archive and deleting original folder')
    shutil.make_archive(os.path.normpath(dir_upload + '/' + date_folder_name + ' ' + dateday), 'zip', os.path.normpath(dir_process + '/' + date_folder_name))
    shutil.rmtree(os.path.normpath(dir_process + '/' + date_folder_name)) # delete existing folder

def create_song_list(songs_used_titles):
    print('Creating song list')
    songnames = [title.split("\\")[-1] for title in songs_used_titles]
    #with open(image_folder+'.txt', 'w') as f:
    #    f.write(str(songnames))
    songnames_str = ','.join(songnames)
    return songnames_str

'''
##########
MAIN
##########
'''

'''
1) Ensure that the images folders in dir_process are named as the dates, and that the images are named chronologically
2) Ensure that the music folder is populated
3) The images folder will be zipped and the original folder will be deleted
4)log.csv will be updated with new entries
'''

dir_process = r'directory of files for processing'
dir_upload = r'directory of where to save the processed files'
dir_music_library = r'directory for the music files'
frames_per_sec = 2

dates_scraped = os.listdir(dir_process)
print(f'{len(dates_scraped)} folder(s) to process: {dates_scraped}')
for date_folder_name in dates_scraped:
    print(f'Processing: {date_folder_name}')
    df = pd.read_csv('log.csv')
    df.set_index('Date', inplace=True)

    image_folder, clip_duration, clip, video_name, dateday = create_video(dir_process, dir_upload, date_folder_name, frames_per_sec)
    songs_used_titles = create_audio(dir_music_library, clip_duration, clip, video_name)    
    songnames_str = create_song_list(songs_used_titles)
    zip_and_delete_pictures(dir_process, dir_upload, date_folder_name, dateday) # Gets a static folderlist and iterates through that. ensure that only the folders to be zipped are inside
    df.loc[date_folder_name] = [dateday, int(clip_duration*frames_per_sec), songnames_str, '', ''] # Date | Day ; Images_count ; Songs ; Uploaded ; Remarks
    print('Folder processed\n')
    df.to_csv('log.csv')

print(f'Completed: {dates_scraped}')