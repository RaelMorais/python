import cv2
import os
import numpy as np

# Caminho para o dataset
dataset_path = "../dataset/israel"
images = []
labels = []

label = 0  # só uma pessoa, então 0

for filename in os.listdir(dataset_path):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        img_path = os.path.join(dataset_path, filename)
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        images.append(gray)
        labels.append(label)

images = np.array(images)
labels = np.array(labels)

# Criar reconhecedor LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(images, labels)

recognizer.write("trainer.yml")  # <--- aqui você cria o arquivo
print("[INFO] Treinamento concluído!")
