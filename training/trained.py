import cv2
import numpy as np

# 1) Carregar reconhecedor treinado
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")  # seu arquivo treinado

person_name = "israel"  # nome da pessoa treinada

# 2) Detector de rosto Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# 3) Abrir webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]

        # Reconhecimento
        label, confidence = recognizer.predict(face_roi)

        if confidence < 80:  # quanto menor, mais confiante
            name = person_name
            color = (0, 255, 0)
        else:
            name = "Desconhecido"
            color = (0, 0, 255)

        # Desenhar retângulo e nome
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, f"{name} ({int(confidence)})", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Reconhecimento Facial LBPH", frame)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
