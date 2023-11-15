import sys

import h5py
import numpy as np

import os
import numpy as np
from scipy import signal
from keras.utils import Sequence

from keras.utils import to_categorical


def load_ches_hd5(database_file,
                  profiling_traces_file, profiling_metadata_file,
                  attack_traces_file, attack_metadata_file):
    try:
        in_file = h5py.File(database_file, "r")
    except ValueError:
        print(f"Error: can't open HDF5 file '{database_file}' for reading (it might be malformed) ...")
        sys.exit(-1)
    # Load profiling traces
    x_profiling = np.array(in_file[profiling_traces_file], dtype=np.float64)
    # Load profiling labels
    metadata_profiling = np.array(in_file[profiling_metadata_file])
    # Load attacking traces
    x_attack = np.array(in_file[attack_traces_file], dtype=np.float64)
    # Load attacking labels
    metadata_attack = np.array(in_file[attack_metadata_file])
    return (x_profiling, metadata_profiling), (x_attack, metadata_attack)


def load_hd5(database_file,
             profiling_traces_file, profiling_labels_file,
             attack_traces_file, attack_labels_file,
             attack_metadata_file=None):
    try:
        in_file = h5py.File(database_file, "r")
    except ValueError:
        print(f"Error: can't open HDF5 file '{database_file}' for reading (it might be malformed) ...")
        sys.exit(-1)
    # Load profiling traces
    x_profiling = np.array(in_file[profiling_traces_file], dtype=np.float32) #dtype=np.float64)
    # Load profiling labels
    y_profiling = np.array(in_file[profiling_labels_file])
    # Load attacking traces
    x_attack = np.array(in_file[attack_traces_file], dtype=np.float32) #dtype=np.float64)
    # Load attacking labels
    y_attack = np.array(in_file[attack_labels_file])
    if attack_metadata_file is None:
        return (x_profiling, y_profiling), (x_attack, y_attack)
    else:
        return (x_profiling, y_profiling), (x_attack, y_attack), in_file[attack_metadata_file]['plaintext']

def load_npy(database_file, train_traces_file, train_labels_file,
             valid_traces_file, valid_labels_file,
             attack_traces_file, attack_labels_file,
             attack_metadata_file=None):

    # Load attacking traces
    test_windows = np.load(database_file + attack_traces_file, mmap_mode="r") 
    # Load attacking labels
    test_targets = np.load(database_file + attack_labels_file, mmap_mode="r")
    
    return (None, None), (test_windows , test_targets)


def load_hd5_hw_model(database_file,
                      profiling_traces_file, profiling_labels_file,
                      attack_traces_file, attack_labels_file,
                      attack_metadata_file=None):
    result = load_hd5(
        database_file, profiling_traces_file, profiling_labels_file,
        attack_traces_file, attack_labels_file, attack_metadata_file
    )
    y_profiling = np.array([bin(x).count("1") for x in result[0][1]])
    y_attack = np.array([bin(x).count("1") for x in result[1][1]])
    if attack_metadata_file is None:
        return (result[0][0], y_profiling), (result[1][0], y_attack)
    else:
        return (result[0][0], y_profiling), (result[1][0], y_attack), result[2]


class ClassifierDataset(Sequence):
    def __init__(self, data_dir, which_subset='train', bacth_size=256, shuffle=True):

        self.windows = np.load(
            os.path.join(data_dir, '{}_windows.npy'.format(which_subset)), mmap_mode='r')

        self.target = np.load(
            os.path.join(data_dir, '{}_targets.npy'.format(which_subset)), mmap_mode='r')
        
        self.shuffle = shuffle

        self.which_subset = which_subset
        self.batch_size = bacth_size
        self.on_epoch_end()
        
    
    def __len__(self):
        return self.target.shape[0] // self.batch_size
    
    def __getitem__(self, index):
        low = index* self.batch_size
        high = min(low + self.batch_size, self.target.shape[0])
        idx = self.indexes[low:high]
        
        x = self.windows[idx]

        # Normalize x (mean 0, std 1)
        x = (x - np.mean(x)) / np.std(x)
        
        y = self.target[idx]
        
        y = to_categorical(y, num_classes=256)
        
        return x, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(self.target.shape[0])
        if self.shuffle == True:
            np.random.shuffle(self.indexes)