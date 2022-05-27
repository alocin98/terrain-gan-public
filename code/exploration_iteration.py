# -*- coding: utf-8 -*-
"""exploration_iteration.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ldro7EAgOFXDb54kxdVJhEUvcbtgN8Lj

#Prepare data
"""

!git config --global user.Username "nicolas.mueller@students.ffhs.ch"
!git config --global user.password "Thunersee1*"
!git clone https://git.ffhs.ch/nicolas.mueller/terrain-gan.git

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import matplotlib.pyplot as plt
import numpy
from google.colab import drive
import os
import math
import numpy as np

drive.mount('/content/drive')

DATA_PATH = '/content/drive/MyDrive/Terrain GAN/data/alps_hgt/'
os.listdir(DATA_PATH)

def getHeightModelsFromDirectory(path=DATA_PATH):
  filenames = [DATA_PATH + file for file in os.listdir(DATA_PATH)]
  data = []
  for file in filenames:
    siz = os.path.getsize(file)
    dim = int(math.sqrt(siz/2))
    data.append(np.fromfile(file, numpy.dtype('>i2'), dim*dim).reshape((dim, dim)))

  return data

def createWindows(heightmodel, win_size, resolution=1, step=0.1):
  windows = []
  for i in range(0,len(heightmodel) - win_size, int(win_size * step)):
    window = heightmodel[i:i+win_size*resolution:resolution,i:i+win_size*resolution:resolution];
    windows.append(window)
  return windows

def isEnoughHilly(heightmodel, minDifference = 0, midHeight = 0):
  flattened = np.array(heightmodel).flatten()
  sorted = np.sort(flattened)
  length = len(sorted)
  dif = abs(sorted[0] - sorted[length - 1])
  median = sorted[int(length / 2)]
  return dif > minDifference and median > midHeight and length == 16384



data = getHeightModelsFromDirectory(DATA_PATH)
windows = []
for heightmodel in data:
  windows.extend(createWindows(heightmodel, 128, 2))

filtered = list(filter(lambda model: isEnoughHilly(model, 1000, 500), windows))
filtered = [x / 5000 for x in filtered]
filtered = numpy.expand_dims(filtered, axis=3)


plt.figure()
print("before filtering: ")
print(len(windows[0]))
print(len(windows))
print("after filtering: ")
print(len(filtered[0]))
print(len(filtered))
print("samples:")

"""#Define Properties

Define all parameters that need to be tested out
"""



"""#Models"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt
import os
import gdown
from zipfile import ZipFile
import io

## DCGAN
discriminator = keras.Sequential(
    [
        keras.Input(shape=(128, 128,1)),
        layers.Conv2D(64, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2D(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2D(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Flatten(),
        layers.Dropout(0.2),
        layers.Dense(1, activation="sigmoid"),
    ],
    name="discriminator",
)
discriminator.summary()

latent_dim = 128

generator = keras.Sequential(
    [
        keras.Input(shape=(latent_dim,)),
        layers.Dense(8 * 8 * 128),
        layers.Reshape((8, 8, 128)),
        layers.Conv2DTranspose(128, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2DTranspose(256, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2DTranspose(512, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2DTranspose(1024, kernel_size=4, strides=2, padding="same"),
        layers.LeakyReLU(alpha=0.2),
        layers.Conv2D(1, kernel_size=5, padding="same", activation="sigmoid"),
    ],
    name="generator",
)
generator.summary()

class GANMonitor(keras.callbacks.Callback):
    def __init__(self, logname='', num_img=3, latent_dim=128):
        self.num_img = num_img
        self.latent_dim = latent_dim
        self.logname = logname
        self.generated = []
        self.d_loss = []
        self.g_loss = []
        self.x_axis = []

    def on_epoch_end(self, epoch, logs=None):
      random_latent_vectors = tf.random.normal(shape=(self.num_img, self.latent_dim))
      generated_images = self.model.generator(random_latent_vectors)
      generated_images.numpy()
      generated_images = numpy.expand_dims(generated_images, axis=3)
      images = np.reshape(generated_images, (-1, 128, 128, 1))
      self.generated.append(images)
      temp_generated.append(images)

      # Save the losses
      self.d_loss.append(logs["d_loss"])
      self.g_loss.append(logs["g_loss"])
      self.x_axis.append(epoch)

      with file_writer.as_default():
        tf.summary.image(self.logname, images[0:10], step=epoch)
        tf.summary.scalar('g_loss', logs["g_loss"], step=epoch)
        tf.summary.scalar('d_loss', logs["d_loss"], step=epoch)
      #tf.summary.scalar('loss', log, step=epoch)
    def on_train_end(self, logs=None):
      plot = plt.figure()
      f, axarr = plt.subplots(3,3, figsize=(16,16))
      f.suptitle(self.logname + '-OVERVIEW', fontsize=20, fontweight='bold')
      f.tight_layout(rect=[0, 0.05, 1, 0.95])
      i = 0
      for x in range(3):
        for y in range(3):
          axarr[x][y].imshow(numpy.squeeze(self.generated[i][0], axis=(2)))
          axarr[x][y].set_title('Epoch: ' + str(i))
          i = i + 1
      with file_writer.as_default():
        tf.summary.image(self.logname + "-OVERVIEW", self.plot_to_image(plot), step=0)
      losses = plt.figure()
      plt.plot(self.x_axis, self.d_loss)
      plt.plot(self.x_axis, self.g_loss)
      with file_writer.as_default():
        tf.summary.image(self.logname + "-LOSSES", self.plot_to_image(losses), step=0)
      
    def plot_to_image(self, figure):    
      buf = io.BytesIO()
      plt.savefig(buf, format='png')
      plt.close(figure)
      buf.seek(0)

      digit = tf.image.decode_png(buf.getvalue(), channels=4)
      digit = tf.expand_dims(digit, 0)

      return digit


class DCGAN(keras.Model):
    def __init__(self, discriminator, generator, latent_dim):
        super(DCGAN, self).__init__()
        self.discriminator = discriminator
        self.generator = generator
        self.latent_dim = latent_dim

    def compile(self, d_optimizer, g_optimizer, loss_fn):
        super(DCGAN, self).compile()
        self.d_optimizer = d_optimizer
        self.g_optimizer = g_optimizer
        self.loss_fn = loss_fn
        self.d_loss_metric = keras.metrics.Mean(name="d_loss")
        self.g_loss_metric = keras.metrics.Mean(name="g_loss")

    @property
    def metrics(self):
        return [self.d_loss_metric, self.g_loss_metric]

    def train_step(self, real_images):
        # Sample random points in the latent space
        batch_size = tf.shape(real_images)[0]
        random_latent_vectors = tf.random.normal(shape=(batch_size, self.latent_dim))

        # Decode them to fake images
        generated_images = self.generator(random_latent_vectors)

        # Combine them with real images
        combined_images = tf.concat([generated_images, real_images], axis=0)

        # Assemble labels discriminating real from fake images
        labels = tf.concat(
            [tf.ones((batch_size, 1)), tf.zeros((batch_size, 1))], axis=0
        )
        # Add random noise to the labels - important trick!
        labels += 0.05 * tf.random.uniform(tf.shape(labels))

        # Train the discriminator
        with tf.GradientTape() as tape:
            predictions = self.discriminator(combined_images)
            d_loss = self.loss_fn(labels, predictions)
        grads = tape.gradient(d_loss, self.discriminator.trainable_weights)
        self.d_optimizer.apply_gradients(
            zip(grads, self.discriminator.trainable_weights)
        )

        # Sample random points in the latent space
        random_latent_vectors = tf.random.normal(shape=(batch_size, self.latent_dim))

        # Assemble labels that say "all real images"
        misleading_labels = tf.zeros((batch_size, 1))

        # Train the generator (note that we should *not* update the weights
        # of the discriminator)!
        with tf.GradientTape() as tape:
            predictions = self.discriminator(self.generator(random_latent_vectors))
            g_loss = self.loss_fn(misleading_labels, predictions)
        grads = tape.gradient(g_loss, self.generator.trainable_weights)
        self.g_optimizer.apply_gradients(zip(grads, self.generator.trainable_weights))

        # Update metrics
        self.d_loss_metric.update_state(d_loss)
        self.g_loss_metric.update_state(g_loss)
        return {
            "d_loss": self.d_loss_metric.result(),
            "g_loss": self.g_loss_metric.result(),
        }

def train_DCGAN(name, data, epochs, optimizer, batch_size, activation_function, loss_function):
  gan = DCGAN(discriminator=discriminator, generator=generator, latent_dim=latent_dim)
  gan.compile(
      d_optimizer=keras.optimizers.Adam(learning_rate=0.0001),
      g_optimizer=keras.optimizers.Adam(learning_rate=0.0001),
      loss_fn=keras.losses.BinaryCrossentropy()
  )

  gan.fit(
      data, epochs=epochs, callbacks=[GANMonitor(logname=name, num_img=10, latent_dim=latent_dim)]
  )

"""#Train and store performance"""

# Commented out IPython magic to ensure Python compatibility.
from datetime import datetime
# %load_ext tensorboard

# Start tensorboard to explore results
# %tensorboard --logdir logs/train_data

# Parameters we give in
optimizers = []             # Keras optimizers
batch_size = 4
activation_functions = []   
loss_functions = []

# Run title
run = "DCGAN-"# + activation_function + "-" + optimizer + "-" + loss_function
logdir = "logs/train_data/" + run
file_writer = tf.summary.create_file_writer(logdir)

train_DCGAN(run, filtered[0:100], 9, '', 4, '', '')

plot = plt.figure()
f, axarr = plt.subplots(3,3, figsize=(16,16))
i = 0
f.suptitle('test' + '-OVERVIEW', fontsize=20, fontweight='bold')
f.tight_layout(rect=[0, 0.05, 1, 0.95])

for x in range(3):
  for y in range(3):
    axarr[x][y].imshow(numpy.squeeze(temp_generated[i][0], axis=(2)))
    axarr[x][y].set_title('Epoch: ' + str(i))
    i = i + 1

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt

x =  [1,2,3,4,5,6,7,8,9]
y1 = [2,2,3,4,3,4,4,3,2]
y2 = [3,3,4,5,6,5,4,5,4]

plt.plot(x,y1)
plt.plot(x,y2)