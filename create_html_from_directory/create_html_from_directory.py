#!/usr/bin/python
import os
import subprocess
from datetime import datetime
import pytz
from pymediainfo import MediaInfo
import time
import jinja2
import jj2_templates



def stopwatch(func):
    def wrapper (*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print (f'Время выполнения {end-start:.2f} сек.')
        return result
    return wrapper


class VideoFile:
    total_duration = 0
    total_count = 0
    instance = ()
    error_instance =()
    
    def __init__(self, root, filename, path):
        self.filename = filename
        self.root = root
        self.full_path = os.path.join(self.root, self.filename)
        self.relpath = os.path.relpath(self.full_path, path)
        self.duration = self.get_duration()
        VideoFile.instance += (self,)
        VideoFile.total_duration += self.duration
        VideoFile.total_count += 1


    def get_duration(self):
        result = 0
       
        # MediaInfo ver.
        media_info = MediaInfo.parse(self.full_path)
        for track in media_info.tracks:
            if track.track_type == "Video":
                result = int(track.duration*0.001)

        # opencv ver.
        # need import cv2 (pip install opencv-python)
        # video = cv2.VideoCapture(self.full_path)
        # frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        # video.set(cv2.CAP_PROP_POS_FRAMES , frame_count)
        # result = int(video.get(cv2.CAP_PROP_POS_MSEC)*0.001)


        return result



    def __repr__(self):
        return ('File "{}" - Duration: {}'.format(self.filename, sec_to_hms(self.duration)))

    def __str__(self):
        return ('File "{}\n{}" - Duration: {} \n\n'.format(self.root, self.filename, sec_to_hms(self.duration)))

    def __len__(self):
        return self.duration


def sec_to_hms(seconds):
    h = seconds//3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


def create_directory(path,name):
    directory_path = os.path.join(path,name)
    try:
        os.mkdir(directory_path)
    except FileExistsError:
        print(f'Директория {directory_path} уже существует.\nПродолжаю выполнять задачу...')
    return directory_path

def write_to_file(path,filename,text='', flag='w'):
    full_path = os.path.join(path, filename)
    with open(full_path, flag) as file:
        file.write(text)

def create_videos_dict(path, root, directory_key, files):
    video_format = list(('mp4', 'avi', 'mpg'))
    video_files = []
    video_files_dict = dict()

    for file in sorted(files):
        if file.split('.')[-1] in video_format:
            video = VideoFile(root, file, path)
            print(f'{video.filename} [{root}]')
            video_files.append(video)
        if video_files:
            video_files_dict.update({directory_key: video_files})
    return video_files_dict       


def get_video_files_to_dict(path):
    
    root, directories, files = next(os.walk(path)) #for get root_lvl directories and root_lvl files
    video_files_dict = dict()


    if files: # in root
        video_files_dict.update(create_videos_dict(path=path,
                                              files=files,
                                              directory_key=root,
                                              root=root))
    if directories: # in root
        for directory in sorted(directories):
            for root, dirs, files in os.walk(directory):
                video_files_dict.update(create_videos_dict(path=path,
                                                           files=files,
                                                           directory_key=directory,
                                                           root=root))
    return video_files_dict



@stopwatch
def main():
    current_directory = os.getcwd()
    video_files_dict = get_video_files_to_dict(path=current_directory)
    print(f'Total duration: {sec_to_hms(VideoFile.total_duration)}')
    
    env = jinja2.Environment(loader=jinja2.PackageLoader('jj2_templates'), autoescape=True)
    template = env.get_template('category.html')
    html = template.render(os=os,
                           video_files_dict=video_files_dict,
                           path=os.path.basename(current_directory),
                           total_duration=sec_to_hms(VideoFile.total_duration),
                           hms=sec_to_hms)     

    write_to_file(current_directory, 'video_index.html', html, 'w')

    if VideoFile.error_instance:
        current_time = pytz.utc.localize(datetime.utcnow()).astimezone().isoformat()
        write_to_file(current_directory, 'error.txt', current_time+'\n','w')
        for file in VideoFile.error_instance:
            write_to_file(current_directory, 'error.txt', str(file)+'\n', 'a')

   


if __name__ == '__main__':
    main()