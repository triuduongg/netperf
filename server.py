import asyncio
import websockets
import json
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 8765

# 1. Yêu cầu nhập địa chỉ IP hợp lệ ngay khi vừa chạy chương trình
print("=== THIẾT LẬP BẢO MẬT TRẠM MẶT ĐẤT ===")
ALLOWED_IP = input("Nhập địa chỉ IP của điện thoại (UAV) được phép kết nối: ").strip()

async def handle_uav(websocket):
    # Lấy địa chỉ IP của thiết bị đang cố gắng kết nối
    client_ip = websocket.remote_address[0]
    
    # 2. BỨC TƯỜNG LỬA: Kiểm tra xem IP có khớp với IP đã nhập không
    if client_ip != ALLOWED_IP:
        print(f"\n[!] CẢNH BÁO: Từ chối kết nối từ thiết bị lạ (IP: {client_ip})!")
        # Đóng ngay cổng kết nối với mã lỗi 1008 (Vi phạm chính sách)
        await websocket.close(code=1008, reason="IP không được cấp phép")
        return  # Kết thúc luồng, không nhận dữ liệu

    # Nếu qua được tường lửa thì chạy code nhận dữ liệu bình thường
    print(f"\n[+] UAV HỢP LỆ đã kết nối từ: {websocket.remote_address}")
    start_time = time.time()
    total_bytes = 0
    
    try:
        async for message in websocket:
            payload_size = len(message.encode('utf-8'))
            total_bytes += payload_size
            data = json.loads(message)
            
            # Chỉ in ra log để thầy cô thấy dữ liệu truyền là Text/JSON
            print(f"[Frame {data['frame']}] Nhận {len(data['detections'])} vật thể | Kích thước gói tin: {payload_size} Bytes")
            for obj in data['detections']:
                print(f"   -> {obj['class']} (Conf: {obj['conf']}) - Tọa độ: {obj['bbox']}")
                
    except websockets.exceptions.ConnectionClosed:
        print("\n[-] UAV đã ngắt kết nối.")
    finally:
        duration = time.time() - start_time
        if duration > 0:
            print(f"\n--- BÁO CÁO HIỆU NĂNG MẠNG (SEMANTIC TRANSMISSION) ---")
            print(f"Tổng băng thông ngữ nghĩa: {total_bytes / 1024:.2f} KB")
            print(f"Tốc độ truyền trung bình: {(total_bytes / duration / 1024):.2f} KB/s")

async def main():
    print(f"\n--- TRẠM MẶT ĐẤT ĐÃ SẴN SÀNG LẮNG NGHE ---")
    print(f"[*] CHÚ Ý: Chỉ chấp nhận duy nhất dữ liệu gửi từ IP: {ALLOWED_IP}")
    async with websockets.serve(handle_uav, SERVER_IP, SERVER_PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())