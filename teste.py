import cv2
import time
import requests
from ultralytics import YOLO

# ================= CONFIGURAÇÕES =================
DJANGO_API = "http://192.168.1.16:8000/api/ambiente/update/"  # endpoint PATCH da API Django
INTERVAL = 2  # segundos entre atualizações

# ================= YOLO =================
model = YOLO("yolov8n.pt")  # modelo leve

# ================= CÂMERA =================
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erro ao abrir a câmera.")
    exit()

# ================= ESTADO =================
last_update = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erro ao capturar frame.")
        break

    # Detecta pessoas
    results = model(frame)[0]
    person_count = 0

    for box in results.boxes.data.cpu().numpy():
        x1, y1, x2, y2, conf, cls = box
        if int(cls) == 0:  # classe "person"
            person_count += 1
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Person {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # ================= ATUALIZAR API DJANGO =================
    current_time = time.time()
    if current_time - last_update > INTERVAL:
        payload = {"total_pessoas": person_count, "pessoas_presentes": []}  # você pode colocar nomes se tiver reconhecimento
        try:
            response = requests.patch(DJANGO_API, json=payload, timeout=3)
            print(f"[API] Pessoas detectadas: {person_count} | Status: {response.status_code}")
        except requests.RequestException as e:
            print("[ERRO] Falha ao enviar dados para a API:", e)
        last_update = current_time

    # ================= EXIBIÇÃO =================
    cv2.imshow("Detecção de Pessoas YOLO", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
