import cv2
from ultralytics import YOLO
import requests
import time

# ================= CONFIGURAÇÕES =================
ESP32_IP = "192.168.4.1"
DJANGO_API_UPDATE = "http://192.168.4.2:8000/api/ambiente/update/"
DJANGO_API_LUZ = "http://192.168.4.2:8000/api/luz/"
AUTHORIZED_NAME = "Israel"
AUTHORIZED_RFID = "6C3ACB33"
CONFIDENCE_THRESHOLD = 80

# URLs para controlar o ESP32
LED_PRESENCA_ON = f"http://{ESP32_IP}/led_presenca?status=on&mensagem=Pessoa"
LED_PRESENCA_OFF = f"http://{ESP32_IP}/led_presenca?status=off"

def led_acesso_libera(nome):
    return f"http://{ESP32_IP}/led_acesso?status=liberado&mensagem={nome}"

def led_acesso_negada(nome):
    return f"http://{ESP32_IP}/led_acesso?status=negado&mensagem={nome}"

# YOLO
yolo_model = YOLO("yolov8n.pt")  # pode rodar em GPU ou CPU dependendo do sistema

# LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ================= FUNÇÕES =================
def atualizar_esp32(url):
    try:
        requests.get(url, timeout=1)
    except Exception as e:
        print("[ERRO ESP32]", e)

def atualizar_django(total, nomes, luz, status_led):
    """Atualiza o ambiente completo no Django."""
    # Garantir que luz nunca seja None ou vazio
    if luz not in ["ON", "OFF"]:
        luz = "OFF"

    payload = {
        "total_pessoas": total,
        "pessoas_presentes": nomes,
        "luz": luz,
        "status_led": status_led
    }
    try:
        requests.patch(DJANGO_API_UPDATE, json=payload, timeout=2)
        print(f"[DJANGO] Ambiente atualizado: {payload}")
    except Exception as e:
        print("[ERRO Django]", e)

def atualizar_luz_django(estado):
    """Atualiza apenas a luz no Django, sempre com valor válido."""
    global ultimo_estado_luz
    if estado not in ["ON", "OFF"]:
        print("[ERRO] Estado da luz inválido:", estado)
        return
    if estado != ultimo_estado_luz:
        payload = {"luz": estado}
        try:
            requests.patch(DJANGO_API_LUZ, json=payload, timeout=2)
            print(f"[DJANGO] Luz atualizada para: {estado}")
            ultimo_estado_luz = estado
        except Exception as e:
            print("[ERRO Django Luz]", e)

def consultar_rfid():
    try:
        r = requests.get(f"http://{ESP32_IP}/status_rfid", timeout=2)
        return r.json().get("last_rfid", "")
    except:
        return ""

# ================= LOOP PRINCIPAL =================
led_presenca_status = None  # on/off
ultimo_total = None
ultimo_nomes = []
ultimo_status_led = None
ultimo_estado_luz = None  # estado da luz para não enviar repetido

while True:
    ret, frame = cap.read()
    if not ret:
        break

    total_pessoas = 0
    nomes_presentes = []
    israel_presente = False

    # ================= DETECÇÃO YOLO =================
    results = yolo_model(frame, verbose=False)
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if cls == 0 and conf > 0.5:  # pessoa detectada
                total_pessoas += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                person_crop = frame[y1:y2, x1:x2]

                gray_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray_crop, 1.1, 5)
                for (fx, fy, fw, fh) in faces:
                    face_roi = gray_crop[fy:fy+fh, fx:fx+fw]
                    label, confidence = recognizer.predict(face_roi)
                    if confidence < CONFIDENCE_THRESHOLD:
                        nomes_presentes.append(AUTHORIZED_NAME)
                        israel_presente = True
                        cv2.rectangle(person_crop, (fx, fy), (fx+fw, fy+fh), (0,255,0), 2)
                        cv2.putText(person_crop, AUTHORIZED_NAME, (fx, fy-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                    else:
                        nomes_presentes.append("Desconhecido")
                        cv2.rectangle(person_crop, (fx, fy), (fx+fw, fy+fh), (0,0,255), 2)
                        cv2.putText(person_crop, "Desconhecido", (fx, fy-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
                frame[y1:y2, x1:x2] = person_crop

    # ================= LED PRESENÇA & DJANGO =================
    if total_pessoas > 0:
        luz = "ON"
        status_led = "verde"
        if led_presenca_status != "on":
            atualizar_esp32(LED_PRESENCA_ON)
            led_presenca_status = "on"
    else:
        luz = "OFF"
        status_led = "vermelho"
        if led_presenca_status != "off":
            atualizar_esp32(LED_PRESENCA_OFF)
            led_presenca_status = "off"

    # Atualiza Django apenas se mudou
    if (total_pessoas != ultimo_total or nomes_presentes != ultimo_nomes or status_led != ultimo_status_led):
        atualizar_django(total_pessoas, nomes_presentes, luz, status_led)
        atualizar_luz_django(luz)
        ultimo_total = total_pessoas
        ultimo_nomes = nomes_presentes.copy()
        ultimo_status_led = status_led

    # ================= VERIFICAR RFID =================
    last_rfid = consultar_rfid().replace(" ", "").upper()
    if last_rfid != "":
        if israel_presente and last_rfid == AUTHORIZED_RFID:
            atualizar_esp32(led_acesso_libera(AUTHORIZED_NAME))
            print("[ACESSO] Liberado para Israel")
        else:
            atualizar_esp32(led_acesso_negada("Desconhecido"))
            print("[ACESSO] Negado")
        # resetar RFID no ESP32 para ler novamente
        requests.get(f"http://{ESP32_IP}/led_acesso?status=off")
        time.sleep(1)

    # ================= MOSTRAR FRAME =================
    cv2.imshow("YOLO + RFID", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
