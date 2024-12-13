import os
import numpy as np
import tensorflow as tf
from keras.preprocessing import image

class BoneFracturePredictor:
    def __init__(self, project_folder):
         self.weights_path = os.path.join(project_folder, 'weights')
          # load the models
         self.model_elbow_frac = tf.keras.models.load_model(os.path.join(self.weights_path, "ResNet50_Elbow_frac.h5"))
         self.model_hand_frac = tf.keras.models.load_model(os.path.join(self.weights_path, "ResNet50_Hand_frac.h5"))
         self.model_shoulder_frac = tf.keras.models.load_model(os.path.join(self.weights_path, "ResNet50_Shoulder_frac.h5"))
         self.model_parts = tf.keras.models.load_model(os.path.join(self.weights_path, "ResNet50_BodyParts.h5"))

          # categories
         self.categories_parts = ["Elbow", "Hand", "Shoulder"]
         self.categories_fracture = ['fractured', 'normal']
         self.size = 224

    def predict(self, img, model="Parts"):
         try :
            if model == 'Parts':
               chosen_model = self.model_parts
            else:
               if model == 'Elbow':
                   chosen_model = self.model_elbow_frac
               elif model == 'Hand':
                 chosen_model = self.model_hand_frac
               elif model == 'Shoulder':
                   chosen_model = self.model_shoulder_frac

          # load image with 224px224p
            temp_img = image.load_img(img, target_size=(self.size, self.size))
            print("loaded:", temp_img)  #<--add here for load checking
            x = image.img_to_array(temp_img)
            print("img to array:", x.shape)  # <--add for shape
            x = np.expand_dims(x, axis=0)
            print("dimension increased:", x.shape)  #<--add for dimension
            images = np.vstack([x])
            print("stacked shape:", images.shape) # <--- check this part of shapes, if image has problem can identify by wrong shapes in each level and data
            prediction = np.argmax(chosen_model.predict(images), axis=1)
            print("prediction vector:", prediction) # predicted tensor/vector to string before string creation , also check if models are loaded in right conditions
         except Exception as e :

           print(" Exception Model processing at parts " , e)


         # chose category string
         try:

           if model == 'Parts':
               prediction_str = self.categories_parts[prediction.item()]
           else:
               prediction_str = self.categories_fracture[prediction.item()]
         except Exception as e :

          print(" Error category part while generating results " , e )

         return prediction_str