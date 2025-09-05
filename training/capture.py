import cv2
import os

# Nome da pessoa (vai ser o nome da pasta)
person_name = "Israel"
dataset_path = "dataset"  # pasta onde vai salvar
num_samples = 120      # número de fotos que você quer capturar

# Criar pasta da pessoa se não existir
person_folder = os.path.join(dataset_path, person_name)
os.makedirs(person_folder, exist_ok=True)

# Abrir webcam
cap = cv2.VideoCapture(0)  # 0 = câmera interna, mude se quiser usar outra

count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Mostrar a imagem
    cv2.imshow("Captura de Fotos", frame)

    # Salvar foto ao pressionar 'c'
    key = cv2.waitKey(1) & 0xFF
    if key == ord('c'):
        img_path = os.path.join(person_folder, f"{count+1}.jpg")
        cv2.imwrite(img_path, frame)
        print(f"[INFO] Foto {count+1} salva em {img_path}")
        count += 1

    # Sair com 'q'
    elif key == ord('q'):
        break

    # Quando atingir o número de fotos
    if count >= num_samples:
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Captura concluída!")
