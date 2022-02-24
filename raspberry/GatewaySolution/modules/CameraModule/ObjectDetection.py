import cv2 as cv
import requests

cap = cv.VideoCapture(0)

if not cap.isOpened():
    print("Erro ao tentar abrir a camera")
    exit()


def processFrame(frameBytes):

    multipart_form_data = {'frame': ("frame.jpg", frameBytes)}

    response = requests.post('http://10.10.2.101:8080/analyze',files=multipart_form_data)

    return response.json()


while True:
    # Captura um frame de cada vez
    ret, frame = cap.read()

    # se frame foi lido
    if not ret:
        print("Erro ao tentar ler o frame. Terminando!")
        break

    frameBytes = cv.imencode( '.jpg', frame)[1].tobytes()
    result = processFrame(frameBytes)

    #carrega colecao de objetos detectados
    d = result["detections"]
    fps = result["fps"]

    for i in d:
        #print(i["name"])
        x1 = i["bbox"]["x1"]
        y1 = i["bbox"]["y1"]
        x2 = i["bbox"]["x2"]
        y2 = i["bbox"]["y2"]

        cv.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

        text = "{}: {:.2f}%".format(i["label"], i["score"]*100)
        cv.putText(frame, text, (x1, y1 - 5), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    
    cv.putText(frame, "FPS: {:.2f}".format(fps), (5, 20), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    # display do resultado
    cv.imshow('frame', frame)

    #monitora o teclado para detectar se foi pressionado o q
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()


