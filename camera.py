import random
import cv2
import torch
from ultralytics import YOLO
from datetime import datetime
from PIL import Image

# opening the file in read mode
with open("utils/5class.txt", "r") as my_file:
    class_list = my_file.read().split("\n")
    my_file.close()

# Generate random colors for class list
detection_colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(len(class_list))]

# load a pretrained YOLOv8n model
model = YOLO("weights/5classv2.pt", "v8")
model.to("cuda" if torch.cuda.is_available() else "cpu")  # Move model to GPU if available

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_test(self, frame):
        # ลดความละเอียดของภาพเพื่อเพิ่มความเร็วในการประมวลผล
        frame_resized = cv2.resize(frame, (800, 600))

        # ทำประมวลผลภาพ
        num = [0] * len(class_list)
        detect_params = model.predict(source=[frame_resized], conf=0.35, save=False)
        DP = detect_params[0].cpu().numpy()
        
        if len(DP) != 0:
            boxes = detect_params[0].boxes
            for i in range(len(boxes)):
                box = boxes[i]  # returns one box
                clsID = box.cls.cpu().numpy()[0]
                conf = box.conf.cpu().numpy()[0]
                bb = box.xyxy.cpu().numpy()[0]

                # วาดกรอบและข้อความบนภาพ
                cv2.rectangle(
                    frame_resized,
                    (int(bb[0]), int(bb[1])),
                    (int(bb[2]), int(bb[3])),
                    detection_colors[int(clsID)],
                    2,
                )

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(
                    frame_resized,
                    class_list[int(clsID)] + " " + str(round(conf, 2)) + "%",
                    (int(bb[0]), int(bb[1]) - 10),
                    font,
                    0.5,
                    (255, 255, 255),
                    1,
                )
                num[int(clsID)] += 1
        
        # แปลงภาพเป็น JPEG
        ret, jpeg = cv2.imencode('.jpg', frame_resized)
        if ret:
            return jpeg.tobytes(), num
        else:
            return None, num

        
    def get_pic(self,frame):
        # ลดความละเอียดของภาพเพื่อเพิ่มความเร็วในการประมวลผล
        frame_resized = cv2.resize(frame, (800, 600))

        # ทำประมวลผลภาพ
        num = [0] * len(class_list)
        detect_params = model.predict(source=[frame_resized], conf=0.50, save=False)
        DP = detect_params[0].cpu().numpy()
        
        if len(DP) != 0:
            boxes = detect_params[0].boxes
            for i in range(len(boxes)):
                box = boxes[i]  # returns one box
                clsID = box.cls.cpu().numpy()[0]
                conf = box.conf.cpu().numpy()[0]
                bb = box.xyxy.cpu().numpy()[0]

                # วาดกรอบและข้อความบนภาพ
                cv2.rectangle(
                    frame_resized,
                    (int(bb[0]), int(bb[1])),
                    (int(bb[2]), int(bb[3])),
                    detection_colors[int(clsID)],
                    2,
                )

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(
                    frame_resized,
                    class_list[int(clsID)] + " " + str(round(conf, 2)) + "%",
                    (int(bb[0]), int(bb[1]) - 10),
                    font,
                    0.5,
                    (255, 255, 255),
                    1,
                )
                num[int(clsID)] += 1
        
        # แปลงภาพเป็น JPEG
        ret, jpeg = cv2.imencode('.jpg', frame_resized)
        if ret:  # ตรวจสอบว่าการแปลงภาพเป็น JPEG สำเร็จหรือไม่
            time_now = datetime.now()
            filename = f"pic/frame_{time_now.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            cv2.imwrite(filename, frame_resized)
            return jpeg.tobytes(),num,filename
        else:
            return None,None