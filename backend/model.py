import tensorflow as tf
import numpy as np
import music21
from music21 import *

us = environment.UserSettings()
us['lilypondPath'] = 'lilypond-2.24.4/bin/lilypond.exe'

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import tensorflow.keras.backend as K
from tensorflow.keras.optimizers import Adamax

import os
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


def load_model(path, shape):
    model = Sequential()
    model.add(LSTM(512, input_shape=(shape[1], shape[2]), return_sequences=True))
    model.add(Dropout(0.1))
    model.add(LSTM(256))
    model.add(Dense(256))
    model.add(Dropout(0.1))
    model.add(Dense(shape[1], activation='softmax'))
    opt = Adamax(learning_rate=0.01)
    model.compile(loss='categorical_crossentropy', optimizer=opt)
        
    if not os.path.exists(path):
        print(f"Файл {path} не найден.")
    
    else:
        model = model.load_weights(path)
        
    return model

def Melody_Generator(model, Note_Count):
    seed = X_seed[np.random.randint(0,len(X_seed)-1)]
    Music = ""
    Notes_Generated=[]
    for i in range(Note_Count):
        seed = seed.reshape(1,length,1)
        prediction = model.predict(seed, verbose=0)[0]
        prediction = np.log(prediction) / 1.0 #diversity
        exp_preds = np.exp(prediction)
        prediction = exp_preds / np.sum(exp_preds)
        index = np.argmax(prediction)
        index_N = index/ float(L_symb)
        Notes_Generated.append(index)
        Music = [reverse_mapping[char] for char in Notes_Generated]
        seed = np.insert(seed[0],len(seed[0]),index_N)
        seed = seed[1:]
    #Now, we have music in form or a list of chords and notes and we want to be a midi file.
    Melody = note_sheet(Music)
    Melody_midi = stream.Stream(Melody)
    return Music,Melody_midi

model = tf.keras.models.load_model(r'models/midigen_Chopin.keras')
Music_notes, Melody = Melody_Generator(model, 100)
Melody.write('midi','Melody_Generated.mid')
