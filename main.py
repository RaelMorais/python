# import cv2
# import numpy as np
# from ultralytics import YOLO

# # Reconhecedor LBPH
# recognizer = cv2.face.LBPHFaceRecognizer_create()
# recognizer.read("trainer.yml")
# person_name = "Israel"

# # Haar Cascade
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# # YOLOv8 - versão leve para performance
# model = YOLO("yolov8n.pt")  # nano, mais rápido que yolov8m

# # Captura de vídeo
# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Reduz resolução
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# frame_count = 0  # Para processar a cada N frames
# process_every_n_frames = 2  # Processar rostos a cada 2 frames

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame_count += 1

#     # Detectar pessoas com YOLO
#     results = model(frame, verbose=False)

#     for result in results:
#         for box in result.boxes:
#             cls = int(box.cls[0])
#             conf = float(box.conf[0])
#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

#             if model.names[cls] == "person" and conf > 0.5:
#                 # Recortar pessoa
#                 person_crop = frame[y1:y2, x1:x2]

#                 # Só processar faces a cada N frames
#                 if frame_count % process_every_n_frames == 0:
#                     # Converter para cinza e reduzir tamanho para Haar
#                     gray_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
#                     small_gray = cv2.resize(gray_crop, (0, 0), fx=0.5, fy=0.5)

#                     faces = face_cascade.detectMultiScale(
#                         small_gray,
#                         scaleFactor=1.1,
#                         minNeighbors=5
#                     )

#                     for (fx, fy, fw, fh) in faces:
#                         # Ajustar coordenadas para escala original
#                         fx, fy, fw, fh = fx*2, fy*2, fw*2, fh*2
#                         face_roi = gray_crop[fy:fy+fh, fx:fx+fw]

#                         label, confidence = recognizer.predict(face_roi)

#                         if confidence < 80:
#                             name = person_name
#                             color = (0, 255, 0)
#                         else:
#                             name = "unknow"
#                             color = (0, 0, 255)

#                         # Desenhar rosto e nome
#                         cv2.rectangle(person_crop, (fx, fy), (fx+fw, fy+fh), color, 2)
#                         cv2.putText(person_crop, f"{name} ({int(confidence)})",
#                                     (fx, fy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

#                 # Colocar crop de volta na imagem original
#                 frame[y1:y2, x1:x2] = person_crop

#     # Reduzir resolução para exibição (mais rápido)
#     display_frame = cv2.resize(frame, (640, 480))
#     cv2.imshow("Detecção + Reconhecimento", display_frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# cap.release()
# cv2.destroyAllWindows()

import requests
import cv2
from ultralytics import YOLO

# Endereços
ESP32_URL = "http://192.168.4.1"       # IP do ESP32
DJANGO_API = "http://192.168.0.100:8000"  # IP/porta da sua API Django

# Credenciais
AUTHORIZED_RFID = "6C3ACB33"
AUTHORIZED_NAME = "Israel"

# Modelo YOLO
model = YOLO("yolov8n.pt")

def controlar_led(cor, acao):
    try:
        r = requests.get(f"{ESP32_URL}/led_control?led={cor}&action={acao}", timeout=2)
        print("LED:", r.json())
    except Exception as e:
        print("Erro LED:", e)

def atualizar_django(total_pessoas, nomes, evento):
    try:
        # Atualizar ambiente
        payload = {"total_pessoas": total_pessoas, "pessoas_presentes": nomes}
        r = requests.patch(f"{DJANGO_API}/ambiente/update/", json=payload, timeout=5)
        print("API Django ambiente:", r.status_code, r.json())

        # Registrar log
        requests.post(f"{DJANGO_API}/logs/", json={"evento": evento}, timeout=5)

    except Exception as e:
        print("Erro API Django:", e)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)

    nome_reconhecido = None
    total_pessoas = 0
    nomes_presentes = []

    for result in results:
        for box in result.boxes:
            if model.names[int(box.cls[0])] == "person":
                total_pessoas += 1
                # aqui entraria seu LBPHRecognizer
                nome_reconhecido = AUTHORIZED_NAME
                nomes_presentes.append(nome_reconhecido)

    # Consultar ESP32 (último RFID lido)
    try:
        status = requests.get(f"{ESP32_URL}/status", timeout=2).json()
        last_rfid = status["last_rfid"]
        print("Último RFID:", last_rfid, "| Nome reconhecido:", nome_reconhecido)

        if last_rfid == AUTHORIZED_RFID and nome_reconhecido == AUTHORIZED_NAME:
            controlar_led("green", "on")
            atualizar_django(total_pessoas, nomes_presentes, f"Acesso autorizado: {AUTHORIZED_NAME}")
        else:
            controlar_led("red", "on")
            atualizar_django(total_pessoas, nomes_presentes, "Acesso negado")

    except Exception as e:
        print("Erro ao falar com ESP32:", e)

    cv2.imshow("YOLO + Django", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
