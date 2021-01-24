# Algoritmo baseado em: https://medium.com/analytics-vidhya/retrieval-based-chatbots-using-nltk-keras-e4f86b262b17

import json
import numpy as np
import random
import nltk
from nltk.tokenize.treebank import TreebankWordTokenizer
from nltk.data import load
import src.utils as u
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.optimizers import SGD
import os 

class Model:
  def __init__(self):
    # Criando o procedimento de tokenização
    w, words, documents, classes, self._intents = self.tokenizing(r"src/intents.json")

    # Criando o procedimento de lematização
    w, words, documents, classes, lemmatizer = self.lemmatizing(w, words, documents, classes)

    # Chamando o procedimento de treino
    self._train_x, self._train_y = self.training_data(w, words, documents, classes, lemmatizer)

    # Chamando o procedimento de tokenização
    self._model = self.training(self._train_x, self._train_y)

  def tokenizing(self, url):
    words = []
    classes = []
    documents = []
    intents = json.loads(open(url).read())
    tokenizer = load("file:portuguese.pickle")
    treebank_word_tokenize = TreebankWordTokenizer().tokenize

    for intent in intents["intents"]:
      for pattern in tokenizer.tokenize(str(intent["patterns"])):
        w = [w for w in treebank_word_tokenize(pattern)]
        
        words.extend(w)
        documents.append((w, intent["tag"]))

        if intent["tag"] not in classes:
          classes.append(intent["tag"])

    return w, words, documents, classes, intents

  def lemmatizing(self, w, words, documents, classes):
    ignore_words = ["?", "!"]
    lemmatizer = nltk.stem.WordNetLemmatizer()

    # Lematizando, transformando cada palavra em minúscula e removendo duplicadas
    words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]

    # Organizando classes e palavras
    classes = sorted(list(set(classes)))
    words = sorted(list(set(words)))

    # Criando os arquivos .pkl com as informações necessárias
    u.create_pickle(words, r"pickles/words.pkl")
    u.create_pickle(words, r"pickles/classes.pkl")

    return w, words, documents, classes, lemmatizer

  def training_data(self, w, words, documents, classes, lemmatizer):
    # Criando os dados de treino
    training = []
    train_x = []
    train_y = []

    # Criando um array vazio para o output
    output = [0] * len(classes)

    # Treinando e criando um bag of words para cada sentença
    for doc in documents:
      # Inicializando o bag of words
      bag = []
      # Lista de palavras tokenizadas para o padrão
      pattern_words = doc[0]
      # Lematizando cada palavra, com o propósito de representar palavras relacionadas
      pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]

      # Preenchendo o vetor de bag of words com 1 se a palavra der match com o padrão atual
      for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

      # Output será 0 para cada tag e 1 se a tag for a tag atual
      output_row = list(output)
      output_row[classes.index(doc[1])] = 1
      
      training.append([bag, output_row])

    # Randomizando as features e transformando-as em um array
    random.shuffle(training)

    training = np.array(training, dtype = object)

    # Criando listas de treino e teste (X - padrões e Y - intents)
    train_x = list(training[:, 0])
    train_y = list(training[:, 1])

    return train_x, train_y

  def training(self, train_x, train_y):
    # Modelo sequencial do Keras
    # Modelo com 3 camadas (primeira com 128 neurônios, segunda com 64 e terceira
    # (output) com o número de intents para predição utilizando a função softmax)
    model = Sequential()
    model.add(Dense(128, input_shape = (len(train_x[0]), ), activation = "relu"))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation = "relu"))
    model.add(Dropout(0.5))
    model.add(Dense(len(train_y[0]), activation = "softmax"))

    # Compilando o modelo com a variação de Nesterov do método do gradiente estocástico
    sgd = SGD(lr = 0.01, decay = 1e-6, momentum = 0.9, nesterov = True)
    
    model.compile(loss = "categorical_crossentropy", optimizer = sgd, metrics = ["accuracy"])

    # Fazendo o ajuste do modelo e salvando-o
    hist = model.fit(np.array(train_x), np.array(train_y), epochs = 200, batch_size = 5, verbose = 1)
    
    model.save(r"src/model.h5", hist)

    return model

  def get_train_x(self):
    return self._train_x
    
  def get_train_y(self):
    return self._train_y
    
  def get_model(self):
    return self.model
    
  def get_intents(self):
    return self._intents