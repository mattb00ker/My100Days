import tensorflow as tf
import numpy as np
import os

path_to_file = ('trumpTweets.txt')

# Read, then decode for py2 compat.
text = open(path_to_file, 'rb').read()
text = text.decode(encoding='utf-8')
print ('Total number of characters in the corpus is:', len(text))
print('The first 100 characters of the corpus are as follows:\n', text[:100])

# The unique characters in the corpus
vocab = sorted(set(text))
print ('The number of unique characters in the corpus is', len(vocab))
print('A slice of the unique characters set:\n', vocab[:10])

# Create a mapping from unique characters to indices
char2idx = {u:i for i, u in enumerate(vocab)}
# Make a copy of the unique set elements in NumPy array format for later use in the decoding the predictions
idx2char = np.array(vocab)
# Vectorize the text with a for loop
text_as_int = np.array([char2idx[c] for c in text])

# Create training examples / targets
char_dataset = tf.data.Dataset.from_tensor_slices(text_as_int) 
# for i in char_dataset.take(5): 
#   print(i.numpy())
seq_length = 100 # The max. length for single input
# examples_per_epoch = len(text)//(seq_length+1) # double-slash for “floor” division
sequences = char_dataset.batch(seq_length+1, drop_remainder=True) 
# for item in sequences.take(5): 
#   print(repr(''.join(idx2char[item.numpy()])))

def split_input_target(chunk):
  input_text = chunk[:-1]
  target_text = chunk[1:]
  return input_text, target_text

dataset = sequences.map(split_input_target)

BUFFER_SIZE = 10000 # TF shuffles the data only within buffers

BATCH_SIZE = 64 # Batch size

dataset = dataset.shuffle(BUFFER_SIZE).batch(BATCH_SIZE, drop_remainder=True)

print(dataset)

# Length of the vocabulary in chars
vocab_size = len(vocab)
# The embedding dimension
embedding_dim = 256
# Number of RNN units
rnn_units = 1024

def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
  model = tf.keras.Sequential([
    tf.keras.layers.Embedding(vocab_size, embedding_dim,
                              batch_input_shape=[batch_size, None]),
    tf.keras.layers.GRU(rnn_units,
                        return_sequences=True,
                        stateful=True,
                        recurrent_initializer='glorot_uniform'),
    tf.keras.layers.Dense(vocab_size)
  ])
  return model

model = build_model(
    vocab_size = len(vocab), # no. of unique characters
    embedding_dim=embedding_dim, # 256
    rnn_units=rnn_units, # 1024
    batch_size=BATCH_SIZE)  # 64 for the traning

model.summary()

def loss(labels, logits):
  return tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)

# example_batch_loss  = loss(target_example_batch, example_batch_predictions)
# print("Prediction shape: ", example_batch_predictions.shape, " (batch_size, sequence_length, vocab_size)")
# print("scalar_loss:      ", example_batch_loss.numpy().mean())

model.compile(optimizer='adam', loss=loss)

# Directory where the checkpoints will be saved
checkpoint_dir = './training_checkpoints'
# Name of the checkpoint files
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

checkpoint_callback=tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_prefix,
    save_weights_only=True)

EPOCHS = 12
history = model.fit(dataset, 
                    epochs=EPOCHS, 
                    callbacks=[checkpoint_callback])