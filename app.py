from flask import Flask, render_template, Response
import cv2
from flask_socketio import SocketIO
from utils import init_google_sheets, save_to_google_sheets, get_data_from_google_sheets, all_posisi
from datetime import datetime
import threading

app = Flask(__name__, static_folder='templates/static')
socketio = SocketIO(app, cors_allowed_origins="*")
scanned_data = set()
scanned_data_lock = threading.Lock()
detector = cv2.QRCodeDetector()
sheet = init_google_sheets()
camera_ids = [1, 2, 3, 4] 
camera_threads = {}

def read_qr_codes(frame, detector):
    data, points, _ = detector.detectAndDecode(frame)
    if points is not None and len(points) > 0:
        if cv2.contourArea(points) > 0:
            return data
    else:
        return None 

def generate_frames(camera_id):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Kamera {camera_id} tidak terdeteksi.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            qr_data = read_qr_codes(frame, detector)
            if qr_data:
                try:
                    nama, posisi = qr_data.split('; ')
                except ValueError:
                    print("QR Code data is invalid")
                    continue

                with scanned_data_lock:
                    if qr_data not in scanned_data:
                        scanned_data.add(qr_data)
                        nama, posisi = qr_data.split('; ')
                        tanggal = datetime.now().strftime("%Y-%m-%d")
                        jam = datetime.now().strftime("%H:%M:%S")
                        entry = [nama, posisi, tanggal, jam]
                        save_to_google_sheets(sheet, [entry])
                        print(f"Data Tersimpan: {nama}, {posisi}, {tanggal}, {jam}")
                        handle_request_records()
                        
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@socketio.on('request_records')
def handle_request_records():
    print("Request for records received")
    record = get_data_from_google_sheets(sheet)
    records = sorted(record, key=lambda x: (x['Tanggal'], x['Jam']), reverse=True)[:7]
    socketio.emit('update_records', records)

@app.route('/')
def index():
    records = get_data_from_google_sheets(sheet)
    sorted_data = sorted(records, key=lambda x: (x['Tanggal'], x['Jam']), reverse=True)[:6]
    return render_template('index.html', camera_ids=camera_ids, records=sorted_data)

@app.route('/data')
def data():
    records = get_data_from_google_sheets(sheet)
    position_counts = all_posisi(sheet)
    return render_template('data.html', records=records, position_counts=position_counts)

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    return Response(generate_frames(camera_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/restart_camera/<int:camera_id>', methods=['POST'])
def restart_camera(camera_id):
    global camera_threads
    if camera_id in camera_threads:
        camera_threads[camera_id].stop()
        camera_threads[camera_id] = threading.Thread(target=generate_frames, args=(camera_id,))
        camera_threads[camera_id].start()
        return {'status': 'success', 'message': f'Kamera {camera_id} di-restart.'}, 200
    else:
        return {'status': 'error', 'message': f'Kamera {camera_id} tidak ditemukan.'}, 404


@app.route('/data_count')
def data_count():
    records = get_data_from_google_sheets(sheet)
    # Don't forget to change what any position/job title at your company
    filtered_records = [record for record in records if record['Posisi'] in ['BPMD Non Utusan', 'Anggota MD']]
    total_peserta = 63
    return {'count': len(filtered_records), 'max': total_peserta}

if __name__ == '__main__':
    socketio.run(app, debug=True)
