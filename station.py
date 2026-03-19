import os
import subprocess
import sys
import time
import json
import cv2
import asyncio
import websockets
from datetime import datetime 
from pathlib import Path
from ultralytics import YOLO

# ==============================================================================
# CÁC HÀM TIỆN ÍCH CHUNG
# ==============================================================================
def convert_avi_to_mp4(input_path, real_fps=None):
    output_path = os.path.splitext(input_path)[0] + ".mp4"
    print(f"\n>> Converting: {input_path} -> {output_path}")
    cmd = ['ffmpeg', '-y']
    if real_fps and real_fps > 0:
        print(f">> Video has been sped up. Adjusting to real speed: {real_fps:.2f} FPS")
        cmd.extend(['-r', str(real_fps)])
    cmd.extend(['-i', input_path])
    cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac', output_path])
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(">> Converted to MP4 successfully!")
        if os.path.exists(input_path):
            os.remove(input_path)
            print(">> Original AVI file removed.")
    except subprocess.CalledProcessError:
        print(">> Error: Cannot convert file. Please check FFmpeg installation!")
    except Exception as e:
        print(f">> Unknown Error: {e}")

def get_next_save_dir(base_dir="runs/detect", name="predict"):
    """Tự động tạo thư mục lưu trữ giống hệt cơ chế của Ultralytics YOLO"""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    if not (base / name).exists():
        return str(base / name)
    i = 2
    while (base / f"{name}{i}").exists():
        i += 1
    return str(base / f"{name}{i}")


# ==============================================================================
# CHẾ ĐỘ 1: XỬ LÝ VIDEO/ẢNH THÔ (LOCAL / STREAM)
# ==============================================================================
def run_raw_mode():
    print("\n--- [MODE 1] YOLO RAW DETECTION SYSTEM ---")
    print("(Press Enter to use default values)")
    source_input = input("1. Source (file path, URL, or '0' for webcam): ").strip()
    source_file = source_input if source_input else "test1.mp4"
    model_input = input("2. Model (default 'yolo26n.pt'): ").strip() 
    model_file = model_input if model_input else "yolo26n.pt"
    img_input = input("3. Image size (Press Enter for default 640): ").strip() 
    try:
        imgsz = int(img_input) if img_input else 640
    except ValueError:
        print(">> Invalid input, reverting to default 640.")
        imgsz = 640
    conf_input = input("4. Confidence threshold (default 0.25): ").strip()
    try:
        conf = float(conf_input) if conf_input else 0.25
    except ValueError:
        conf = 0.25
    stride_input = input("5. Video stride (skip frames, default 1): ").strip()
    try:
        vid_stride = int(stride_input) if stride_input else 1
    except ValueError:
        vid_stride = 1
        
    is_url = source_file.lower().startswith(('http://', 'https://', 'rtsp://', 'rtmp://', 'tcp://'))
    if source_file != '0' and not is_url and not os.path.exists(source_file):
        print(f"Error: Source file '{source_file}' not found.")
        sys.exit()
        
    print("-" * 30)
    print(f"Running with: Source={source_file}, Model={model_file}, Imgsz={imgsz}, Conf={conf}, Stride={vid_stride}")
    print(">> Press 'q' on the video window or Ctrl+C in terminal to stop.")
    print("-" * 30)
    
    try:
        model = YOLO(model_file)
    except Exception as e:
        print(f">> Error loading model: {e}")
        sys.exit()
        
    save_dir = None 
    total_frames = 0 
    start_time = 0 
    end_time = 0 
    json_data = [] 
    try:
        start_time = time.time()
        results = model.predict(
            source=source_file, 
            imgsz=imgsz, 
            save=True, 
            stream=True, 
            show=False, 
            conf=conf,
            vid_stride=vid_stride 
        )
        for i, result in enumerate(results):
            if i == 0:
                save_dir = result.save_dir 
            total_frames += 1
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            frame_info = {
                "frame_id": i,
                "timestamp": current_time_str, 
                "detections": []
            }
            boxes = result.boxes
            if len(boxes) > 0:
                clss = boxes.cls.int().cpu().tolist()
                confs = boxes.conf.cpu().tolist()
                xyxys = boxes.xyxy.cpu().tolist()
                names = [result.names[c] for c in clss]
                for cls_id, confidence, box, name in zip(clss, confs, xyxys, names):
                    frame_info["detections"].append({
                        "class_id": cls_id,
                        "class_name": name,
                        "confidence": round(confidence, 3),
                        "bbox": [round(b, 1) for b in box] 
                    })
                print(f"Frame {i}: Found {len(names)} object(s). Detail: {names}")
            else:
                if i % 10 == 0:
                    print(f"Frame {i}: Scanning...", end='\r')
            json_data.append(frame_info)
            annotated_frame = result.plot()
            cv2.imshow(source_file, annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n>> I received the exit command from the window.")
                break
    except KeyboardInterrupt:
        print("\n\n>> Stopping detection (User interrupted)...")
    finally:
        cv2.destroyAllWindows() 
        
    end_time = time.time()
    duration = end_time - start_time
    actual_fps = 0
    if duration > 0 and total_frames > 0:
        actual_fps = total_frames / duration
        print(f"\n\n--- Statistics ---")
        print(f"Total run time:         {duration:.2f}s")
        print(f"Total number of frames: {total_frames}")
        print(f"Actual speed:           {actual_fps:.2f} FPS")
    else:
        print("\n>> No frames have been run yet, or the time is too short.")

    if save_dir:
        json_path = os.path.join(save_dir, 'predictions.json')
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            print(f">> Saved JSON detections to: {json_path}")
        except Exception as e:
            print(f">> Error saving JSON file: {e}")

    print("\n--- Detection Phase Completed ---")
    is_video_source = is_url or source_file == '0' or source_file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.flv'))
    if save_dir and is_video_source:
        print(f">> Checking for output in: {save_dir}")
        try:
            avi_files = [f for f in os.listdir(save_dir) if f.endswith('.avi')]
            if avi_files:
                latest_avi = max([os.path.join(save_dir, f) for f in avi_files], key=os.path.getctime)
                print(f">> Found output file: {latest_avi}")
                convert_avi_to_mp4(latest_avi, real_fps=actual_fps)
            else:
                print(">> No AVI file found in save directory.")
        except Exception as e:
            print(f">> Error finding output file: {e}")
    elif not is_video_source:
        print(">> Input was an image. No video conversion needed.")


# ==============================================================================
# CHẾ ĐỘ 2: NHẬN DỮ LIỆU NGỮ NGHĨA (SEMANTIC WEBSOCKETS)
# ==============================================================================
async def run_semantic_mode():
    print("\n--- [MODE 2] SEMANTIC TRANSMISSION RECEIVER ---")
    ALLOWED_IP = input("Nhập địa chỉ IP của điện thoại (UAV) được phép kết nối: ").strip()
    clean_allowed_ip = ALLOWED_IP.replace("::ffff:", "")
    
    # Tạo thư mục save_dir giống hệt Ultralytics
    save_dir = get_next_save_dir()
    os.makedirs(save_dir, exist_ok=True)
    print(f">> Dữ liệu Semantic sẽ được lưu tại: {save_dir}")
    
    stop_event = asyncio.Event() # Biến cờ để báo hiệu dừng Server khi xong 1 client

    async def handle_uav(websocket):
        raw_ip = websocket.remote_address[0]
        clean_client_ip = raw_ip.replace("::ffff:", "")
        
        # BỨC TƯỜNG LỬA
        if clean_client_ip != clean_allowed_ip:
            print(f"\n[!] CẢNH BÁO: Từ chối kết nối từ thiết bị lạ (IP: {clean_client_ip})!")
            await websocket.close(code=1008, reason="IP không được cấp phép")
            return

        print(f"\n[+] UAV HỢP LỆ đã kết nối từ: {websocket.remote_address}")
        start_time = time.time()
        total_bytes = 0
        total_frames = 0
        json_data = []
        
        try:
            async for message in websocket:
                payload_size = len(message.encode('utf-8'))
                total_bytes += payload_size
                data = json.loads(message)
                
                frame_id = data.get('frame', total_frames)
                detections = data.get('detections', [])
                total_frames += 1
                
                # Trích xuất danh sách tên vật thể để in ra log cho giống detect.py
                names = [obj['class'] for obj in detections]
                
                # In ra format hệt như detect.py (kèm thêm dung lượng mạng)
                if len(names) > 0:
                    print(f"Frame {frame_id}: Found {len(names)} object(s). Detail: {names} | Size: {payload_size} Bytes")
                else:
                    if frame_id % 10 == 0:
                        print(f"Frame {frame_id}: Scanning... | Size: {payload_size} Bytes", end='\r')
                
                # Đóng gói dữ liệu chuẩn bị lưu JSON
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                frame_info = {
                    "frame_id": frame_id,
                    "timestamp": current_time_str, 
                    "detections": []
                }
                
                for obj in detections:
                    frame_info["detections"].append({
                        "class_id": -1, # Web app truyền tên trực tiếp nên ID để -1
                        "class_name": obj['class'],
                        "confidence": obj['conf'],
                        "bbox": obj['bbox']
                    })
                json_data.append(frame_info)
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n[-] UAV đã ngắt kết nối.")
        except KeyboardInterrupt:
            print("\n>> Dừng nhận dữ liệu (User interrupted)...")
        finally:
            # 1. TÍNH TOÁN BÁO CÁO THỐNG KÊ
            duration = time.time() - start_time
            actual_fps = total_frames / duration if duration > 0 else 0
            
            print(f"\n\n--- Statistics ---")
            print(f"Total run time:         {duration:.2f}s")
            print(f"Total number of frames: {total_frames}")
            print(f"Actual speed:           {actual_fps:.2f} FPS")
            print(f"Total bandwidth usage:  {total_bytes / 1024:.2f} KB")
            print(f"Average network speed:  {(total_bytes / duration / 1024):.2f} KB/s" if duration > 0 else "0 KB/s")
            
            # 2. LƯU FILE JSON NHƯ DETECT.PY
            if json_data:
                json_path = os.path.join(save_dir, 'predictions.json')
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=4, ensure_ascii=False)
                    print(f">> Saved JSON detections to: {json_path}")
                except Exception as e:
                    print(f">> Error saving JSON file: {e}")
            else:
                print(">> No data received to save.")
                
            print("\n--- Semantic Phase Completed ---")
            
            # 3. KÍCH HOẠT CỜ DỪNG SERVER (Chỉ nhận 1 thiết bị rồi nghỉ)
            stop_event.set()

    print(f"\n--- TRẠM MẶT ĐẤT ĐÃ SẴN SÀNG LẮNG NGHE ---")
    print(f"[*] CHÚ Ý: Chỉ chấp nhận duy nhất dữ liệu gửi từ IP: {clean_allowed_ip}")
    async with websockets.serve(handle_uav, "0.0.0.0", 8765):
        await stop_event.wait() # Server sẽ chạy cho đến khi stop_event được gọi ở hàm finally


# ==============================================================================
# MAIN MENU
# ==============================================================================
if __name__ == "__main__":
    print("="*50)
    print("   HỆ THỐNG TRẠM MẶT ĐẤT LAI (HYBRID GROUND STATION)")
    print("="*50)
    print("1. Chế độ 1: Phân tích thô (Video/Camera/RTSP)")
    print("2. Chế độ 2: Nhận Ngữ nghĩa (Semantic WebSockets)")
    print("="*50)
    
    choice = input(">> Chọn chế độ hoạt động (1 hoặc 2): ").strip()
    
    if choice == '1':
        run_raw_mode()
    elif choice == '2':
        # Chạy Event Loop của Asyncio cho WebSocket
        asyncio.run(run_semantic_mode())
    else:
        print("Lựa chọn không hợp lệ. Đang thoát chương trình...")