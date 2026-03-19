// --- ĐIỀN ĐỊA CHỈ IP LAPTOP CỦA BẠN VÀO ĐÂY ---
const SERVER_IP = "192.168.1.48"; 
const SERVER_PORT = 8765;
const MODEL_URL = './yolo26n_web_model/model.json';

// TỪ ĐIỂN 80 VẬT THỂ CỦA YOLO (COCO DATASET)
const YOLO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
];

const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const statusText = document.getElementById('status');
const logDiv = document.getElementById('log');

let model, socket;
let frameCount = 0;

function addLog(msg) {
    logDiv.innerHTML += `> ${msg}<br>`;
    logDiv.scrollTop = logDiv.scrollHeight;
}

async function startSystem() {
    addLog("Bật Camera...");
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
    video.srcObject = stream;
    
    addLog(`Đang kết nối Server ${SERVER_IP}...`);
    socket = new WebSocket(`ws://${SERVER_IP}:${SERVER_PORT}`);
    socket.onopen = () => addLog("Đã kết nối Ground Station!");
    
    addLog("Đang tải YOLO Model...");
    model = await tf.loadGraphModel(MODEL_URL);
    addLog("Model tải xong!");
    statusText.innerText = "ĐANG TRUYỀN DỮ LIỆU NGỮ NGHĨA";
    statusText.style.color = "lime";

    processFrames();
}

async function processFrames() {
    if (socket.readyState === WebSocket.OPEN && video.readyState === 4) {
        frameCount++;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const input = tf.browser.fromPixels(canvas).resizeBilinear([640, 640]).expandDims(0).toFloat().div(255.0);
        const predictions = await model.predict(input);
        
        const tensorData = predictions.dataSync(); 
        let realDetections = [];
        
        for (let i = 0; i < 300 * 6; i += 6) {
            let conf = tensorData[i + 4]; 
            
            if (conf > 0.4) { 
                let classId = Math.round(tensorData[i + 5]);
                
                // TRA TỪ ĐIỂN TẠI ĐÂY: Dịch ClassID thành tên tiếng Anh
                let objectName = YOLO_CLASSES[classId] || ("Unknown_ID_" + classId);

                realDetections.push({
                    class: objectName, // Gán tên thật vào đây
                    conf: Math.round(conf * 100) / 100,
                    bbox: [
                        Math.round(tensorData[i]),     
                        Math.round(tensorData[i+1]),   
                        Math.round(tensorData[i+2]),   
                        Math.round(tensorData[i+3])    
                    ]
                });
            }
        }

        const semanticPayload = {
            frame: frameCount,
            detections: realDetections
        };

        socket.send(JSON.stringify(semanticPayload));
        tf.dispose([input, predictions]); 
    }
    requestAnimationFrame(processFrames);
}

startSystem();