from ultralytics import YOLO
model = YOLO("yolo26n.pt")  
results = model.train(data="VisDrone.yaml", epochs=50, imgsz=640)