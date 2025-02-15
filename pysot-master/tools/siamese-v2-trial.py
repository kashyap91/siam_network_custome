from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
os.environ["PYTHONPATH"] = "kashyap/pysot-master/pysot:$PYTHONPATH"


import argparse
import csv
import pandas as pd
import collections
import cv2
import sys
import torch
import datetime
from itertools import count
import numpy as np
from glob import glob1
import json
import time
from pysot.core.config import cfg
from pysot.models.model_builder import ModelBuilder
from pysot.tracker.tracker_builder import build_tracker
import re

torch.set_num_threads(1)
# parser = argparse.ArgumentParser(description='tracking demo')
# parser.add_argument('--video_name', default='', type=str, help='videos or image files')
# args = parser.parse_args()
def get_frames(video_name):

    if video_name.endswith('avi') or \
        video_name.endswith('mp4'):
        vid_name = "/home/developer/kashyap/pysot-master/demo/vids/{}".format(video_name)
        cap = cv2.VideoCapture(vid_name)#(args.video_name)
        while True:
            ret, frame = cap.read()
            if ret:
                yield frame
            else:
                break
    else:
        images = glob(os.path.join(video_name, '*.jp*'))
        images = sorted(images,
                        key=lambda x: int(x.split('/')[-1].split('.')[0]))
        for img in images:
            frame = cv2.imread(img)
            yield frame

def main():
    #try:
        #os.remove("/home/developer/kashyap/pysot-master/*.csv")
    #except:
     #   pass
    # with open('./demo/groundtruth.csv', 'r') as f:
    #     reader = csv.reader(f)
    #     cords = list(reader)

    # load config

    cfg.merge_from_file('./experiments/siamrpn_alex_dwxcorr/config.yaml')
    cfg.CUDA = torch.cuda.is_available()
    device = torch.device('cuda' if cfg.CUDA else 'cpu')
    print(device)
    # create model
    model = ModelBuilder()

    # load model
    model.load_state_dict(torch.load('./experiments/siamrpn_alex_dwxcorr/model.pth', map_location=lambda storage, loc: storage.cpu()))
    model.eval().to(device)

    # build tracker
    tracker = build_tracker(model)


    video_list = glob1("/home/developer/kashyap/pysot-master/demo/vids/", "*.mp4")
    for video_name in video_list:
        video_name_str = os.path.splitext(video_name)[0]
        df = pd.read_csv('./demo/vids/'+video_name_str+'.csv', delimiter=',', header=None)
        cords = [list(x) for x in df.values]
        object_counter = 0
        for cord in cords:
            object_counter = object_counter + 1
            first_frame = True
            # if video_name:#args.video_name:
            #     #video_name = args.video_name.split('/')[-1].split('.')[0]
            #     video_name = video_name.split('/')[-1].split('.')[0]
            # else:
            #     exit()
            frame_count = 1
            mylist = [[frame_count,object_counter,cord,video_name]]
            for frame in get_frames(video_name):#(args.video_name):
                if first_frame:
                    try:
                        init_rect = cord
                    except:
                        exit()
                    tracker.init(frame, init_rect)
                    first_frame = False
                else:
                    outputs = tracker.track(frame)

                    if 'polygon' in outputs:
                        exit()
                    else:
                        #crds = map(int,outputs['bbox'])
                        bbox = list(map(int,outputs['bbox']))
                        #cv2.rectangle(frame,(bbox[0],bbox[1]),(bbox[0]+bbox[2],bbox[1]+bbox[3]),(0,255,0),3)    
                        #for frame in get_frames(video_name):#(args.video_name):
                        frame_count = frame_count + 1   
                        mylist.append([frame_count,object_counter,bbox,video_name])

            with open('vid-'+str(video_name)+'-tracking-'+str(object_counter)+'-object-'+str(cord)+'.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, quoting=0, '\n')#,quotechar='',escapechar='')
                writer.writerow(mylist)

            # with open('coordinates'+str(counter)+'object-'+str(cord)+'.csv') as inp, open('vid-'+str(video_name)+'-tracking-'+str(counter)+'-object.csv', 'w') as out:
            #     reader = csv.reader(inp)
            #     writer = csv.writer(out, delimiter=',')
            #     writer.writerow(['0'] + next(reader))
            #     writer.writerows([i] + row for i, row in enumerate(reader, 1))


# # import subprocess
# # import os
# # os.environ["PYTHONPATH"] = "/path/to/pysot:$PYTHONPATH"
# # subprocess.call('python ./tools/demo.py --video ./demo/bag.avi', shell = True)
if __name__ == '__main__':
    main()