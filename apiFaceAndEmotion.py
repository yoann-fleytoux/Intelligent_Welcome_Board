import cv2.face
from freenect import sync_get_video as get_video
import face_recognition
import cv2
import glob
import pickle
import os
from kivy.app import App
import configparser

#from warpTranslate import *

class apiFaceDetectAndClassifier:

    #Yoann will call the function when he needs so he has more control over performance

    def __init__(self):
        self.parent = App.get_running_app()
        self.emotion_list = ["neutral", "happy", "sadness", "surprise", "anger", "fear"]
        self.divPix = 3
        #self.cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        #self.emotionClassifier = cv2.face.createFisherFaceRecognizer()
        #self.emotionClassifier.load("classifier.yml")
        self.personsDB = apiFaceDetectAndClassifier.loadAllDataBase(self)
        with open('data/profile.txt', 'rb') as handleProfiles:
            self.numProfile = pickle.loads(handleProfiles.read())
        self.video_capture = cv2.VideoCapture(0)

    def getPerson(self, frame, personsDB):

        face_locations = []
        face_encodings = []

        # Resize frame of video to 1/divPix si size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=1/self.divPix, fy=1/self.divPix)

        # Find all the faces and face encodings in the current frame of video
        # Try with other cascade classifier
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        #print(face_locations)
        face_names = []
        for i in range(0, len(face_encodings)):
            name = "Unknown"
            for people in personsDB.items():
                match = face_recognition.compare_faces([people[1]], face_encodings[i])

                if match[0]:
                    name = people[0]
                    break
            if name == "Unknown":
                name = apiFaceDetectAndClassifier.cutAndAddToDataBase(self, face_locations[i], face_encodings[i], frame, personsDB, self.numProfile)

            face_names.append(name)

        return face_names

    def loadAllDataBase(self):
        allPersons = {}
        with open('data/encodings.txt', 'rb') as handle:
            allPersons = pickle.loads(handle.read())

        personsDB = apiFaceDetectAndClassifier.removeDeletedProfiles(self, allPersons, "pics/*.jpg")
        return personsDB

    def removeDeletedProfiles(self, personsDB, folderPath):
        # Check if pictures corresponding to names in allPersons are still here

        images = glob.glob(folderPath)
        imageNames = []

        for image in images:
            image = image.replace("pics/", "")
            image = image.replace(".jpg", "")
            imageNames.append(image)

        #print(allPersons.keys())

        toDelete = []

        for person in personsDB.keys():
            if person not in imageNames:
                toDelete.append(person)

        for person in toDelete:
            del personsDB[person]

        #print(allPersons.keys())
        return personsDB

    def cutAndAddToDataBase(self, location, encoding, img, personsDB, numProfile):

        img = img[location[0] * self.divPix:location[2] * self.divPix, location[3] * self.divPix:location[1] * self.divPix].copy()

        numProfile += 1
        imagePath = "pics/" + str(numProfile) + ".jpg"

        cv2.imwrite(imagePath, img)
        """
        #todo create user profile
        config = configparser.ConfigParser()
        config["WATCHING_HABITS"]={}
        with open("pics/" + str(numProfile) +".ini", 'w+') as configfile:
            config.write(configfile)
        """
        fo = open("pics/" + str(numProfile) +".ini",  "wb")
        fo.close()

        imagePath = imagePath.replace("pics/", "")
        imagePath = imagePath.replace(".jpg", "")

        personsDB[imagePath] = encoding

        return str(numProfile)

    def quitAndSave(self):
        with open('data/encodings.txt','wb') as handle:
            pickle.dump(self.personsDB, handle)

        with open('data/profile.txt','wb') as handleProfiles:
            pickle.dump(self.numProfile, handleProfiles)
        #exit(0)

    def changeName(self, old, new, personsDB):
        #print(personsDB[old])
        if old in personsDB.keys():
            #todo modify user file name
            personsDB[new] = personsDB.pop(old)
            oldNamePic = "pics/" + str(old)
            newNamePic = "pics/" + new
            os.rename(oldNamePic+".jpg",newNamePic+".jpg")
            os.rename(oldNamePic + ".ini", newNamePic + ".ini")
            return 0
        else:
            return -1

    def check_who_it_is(self):
        (video, _) = get_video()
        res = apiFaceDetectAndClassifier.getPerson(self, video, self.personsDB)
        for name in res:
            print(name, "is here")
        del video
        return res

if __name__ == '__main__':
    obj = apiFaceDetectAndClassifier()

    while True:
        # Grab a single frame of video
        (video, _) = get_video()
        res = apiFaceDetectAndClassifier.getPerson(obj, video, obj.personsDB)
        print(res)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            apiFaceDetectAndClassifier.quitAndSave(obj)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            print(apiFaceDetectAndClassifier.changeName(obj, res[0],"coquin",obj.personsDB))
