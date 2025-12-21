import tensorflow as tf
import numpy as np
import pydub
import music21
from music21 import *
import fitz

us = environment.UserSettings()
us['lilypondPath'] = 'lilypond-2.24.4/bin/lilypond.exe'

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import tensorflow.keras.backend as K
from tensorflow.keras.optimizers import Adamax

import os, sys, getopt, glob, random, re, subprocess
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


def load_model(path):
    if not os.path.exists(path):
        print(f"Файл {path} не найден.")
        return
    else:
        model = tf.keras.models.load_model(path)
        return model

def note_sheet(Snippet, offset_increment=1):
    Melody = []
    offset = 0 #Incremental
    for i in Snippet:
        #If it is chord
        if ("." in i or i.isdigit()):
            chord_notes = i.split(".") #Seperating the notes in chord
            notes = []
            for j in chord_notes:
                inst_note=int(j)
                note_snip = note.Note(inst_note)
                notes.append(note_snip)
                chord_snip = chord.Chord(notes)
                chord_snip.offset = offset
                Melody.append(chord_snip)
        # pattern is a note
        else:
            note_snip = note.Note(i)
            note_snip.offset = offset
            Melody.append(note_snip)
        # increase offset each iteration so that notes do not stack
        offset += offset_increment
    Melody_midi = stream.Stream(Melody)
    return Melody_midi

def Melody_Generator(model_path, tempo, duration):
    model = tf.keras.models.load_model(model_path+'model.keras')
    X_seed = np.loadtxt(model_path+'X_seed.txt', delimiter=',')
    X_seed = X_seed.reshape((*X_seed.shape, 1))
    symb = np.loadtxt(model_path+'symb.txt', delimiter=',', dtype=str)
    L_symb = len(symb)
    reverse_mapping = dict((i, c) for i, c in enumerate(symb))
    seed = X_seed[np.random.randint(0, X_seed.shape[0]-1)]
    
    Music = ""
    Notes_Generated=[]
    duration *= 2 # for some reason it works in half-second intervals
    Note_Count = int(tempo * duration / 60.0)
    for i in range(Note_Count):
        seed = seed.reshape(1,X_seed.shape[1],1)
        prediction = model.predict(seed, verbose=0)[0]
        prediction = np.log(prediction) / 1.0 #diversity
        exp_preds = np.exp(prediction)
        prediction = exp_preds / np.sum(exp_preds)
        index = np.argmax(prediction)
        index_N = index / float(L_symb)
        Notes_Generated.append(index)
        Music = [reverse_mapping[char] for char in Notes_Generated]
        seed = np.insert(seed[0],len(seed[0]),index_N) 
        seed = seed[1:]
    offset_increment = 60.0 / tempo ####?
    Melody = note_sheet(Music, offset_increment)
    Melody_midi = stream.Stream(Melody)
    return Music, Melody_midi

#Music_notes, Melody = Melody_Generator('models/Chopin/', tempo=128, duration=15)
#Melody.write('midi', 'Melody_Generated_test.mid')
#Melody.write('lily.pdf', fp='Melody_Generated_test')
  
def pdf_to_png(midi_name):
    doc = fitz.open(f'{midi_name}.pdf')
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        pix.save(f'{midi_name}.png')
        break
    doc.close()

def midi_to_mp3(midi_name, sf2='FluidR3_GM.sf2', out_type='wav', conv_type='mp3'):
    midi_file = f"{midi_name}.mid"
    out_file = f"{midi_name}.{out_type}"
    subprocess.run(['fluidsynth', '-T', out_type, '-F', out_file, '-ni', sf2, midi_file])
    conv_file = f"{midi_name}.{conv_type}"
    sound = pydub.AudioSegment.from_wav(out_file)
    sound.export(conv_file, format=conv_type)
#midi_to_mp3('Melody_Generated_test')
