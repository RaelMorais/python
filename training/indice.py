import cv2

print("Verificando câmeras disponíveis...")

for i in range(1):  # testa os índices 0 a 4
    cap = cv2.VideoCapture(i)
    ret, frame = cap.read()
    if ret:
        print(f"Câmera {i} detectada!")
    cap.release()
