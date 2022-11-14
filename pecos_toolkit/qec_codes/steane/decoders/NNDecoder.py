#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NNDecoder.py
@author Luc Kusters
@date 26-09-2022
"""

import numpy
from tensorflow import keras

from pecos_toolkit.qec_codes.steane.decoders import AbstractSequentialDecoder


class RegularIntervalModelSaver(keras.callbacks.Callback):

    def __init__(self, model_name, *args, epoch_interval=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.epoch_interval = epoch_interval

    def on_epoch_end(self, epoch, logs={}):
        if epoch % self.epoch_interval == 0:
            print("saving...")
            self.model.save(f"{self.model_name}_epoch_{epoch}")


class _BaseNeuralNetworkDecoder(
        AbstractSequentialDecoder.AbstractSequentialDecoder):

    def __init__(self):
        self.model = keras.models.Sequential()

    @classmethod
    def from_path(cls, path, *args, **kwargs):
        instance = cls()
        instance.model = instance.load(path, *args, **kwargs)
        return instance

    def decode_sequence_to_parity(self, sequence_data, parity_threshold=0.5):
        """Calculate expected error parity for the model

        Arguments:
            sequence_data, numpy.ndarray containing sequence data used
                for decoding. Can be a numpy array of shape (?,s,12)
                or (s,12).
            parity_threshold: threshold to determine when a bit flip
                occurs. The keras model returns probabilities from 0 to
                1 for whether a bit flip occured. The standard
                threshold is 0.5 (which comes down to mathematical
                rounding)

        Returns:
            numpy.ndarray of bools. True means the network predicted that
            an error occured, False means that the network predicted that
            no error occured.
        """
        sequence_ndim = sequence_data.ndim
        if sequence_ndim == 2:
            numpy.expand_dims(sequence_data, axis=0)
        predictions = self.model.predict(sequence_data)
        parities = predictions >= parity_threshold
        return parities

    def decode_sequence_to_correction(self, sequence_data, **kwargs):
        """Generate a correction based on sequence data

        The Neural Network decoder

        Arguments:
            sequence_data, numpy.ndarray containing sequence data used
                for decoding. Can be a numpy array of shape (?,s,12)
                or (s,12).
            **kwargs passed to decode_sequence_to_parity

        Returns:
            Set of qubits on which a correction is to be applied. The
            correction Pauli type must be derived from context and is
            not implemented here.
        """
        raise NotImplementedError("AAAAAAAAAAA")
        # parities = self.decode_sequence_to_parity(sequence_data, **kwargs)

    def fit(self, *args, **kwargs):
        """Wrapper for self.model.fit"""
        self.model.fit(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Wrapper for self.model.save"""
        self.model.save(*args, **kwargs)

    def load(self, *args, **kwargs):
        """Wrapper for keras.models.load_model"""
        self.model = keras.models.load_model(*args, **kwargs)

class categorical_accuracy_no_mask(keras.callbacks.Callback):

    def on_train_begin(self, logs={}):
        self.val_acc = []

    def on_epoch_end(self, epoch, logs={}):
        val_predict = (numpy.asarray(self.model.predict(
            self.model.validation_data[0]))).round()
        val_targ = self.model.validation_data[1]
        indx = numpy.where(val_targ.any(axis=2) == -1)[0]  # FIXME
        y_true_nomask = numpy.delete(val_targ, indx, axis=0)
        y_pred_nomask = numpy.delete(val_predict, indx, axis=0)

        _val_accuracy = accuracy_score(y_true_nomask, y_pred_nomask)
        self.val_acc.append(_val_accuracy)

        print(" — val_accuracy : %f " % (_val_accuracy))
        return


class DualLSTMDecoder(_BaseNeuralNetworkDecoder):
    """LSTM decoder, can decode either Z or X errors from sequence data

    Defines a tensorflow.keras model with a number of LSTM layers followed by
    a number of dense (post-processing) layers.

    2 LSTM layers followed by DNN.

    Uses keras standard interface to learn, save and load a model
    """

    def __init__(self, input_shape, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_shape = input_shape
        self.loss_function = keras.losses.BinaryCrossentropy()
        self.optimizer = keras.optimizers.Adam(lr=1e-3)  # , decay=1e-5)

        # LSTM Layer + masking
        self.model.add(keras.layers.Masking(
              mask_value=-1, input_shape=input_shape))
        self.model.add(keras.layers.LSTM(units=36,
                                         input_shape=self.input_shape,
                                         activation="relu",
                                         return_sequences=True,
                                         ))
        self.model.add(keras.layers.LSTM(units=36,
                                         input_shape=self.input_shape,
                                         activation="relu",
                                         return_sequences=False,
                                         ))
        # post_processing
        self.model.add(keras.layers.Dense(units=48, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.Dense(units=24, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.Dense(units=12, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        # binary output from 0 to 1
        self.model.add(keras.layers.Dense(units=1, activation="sigmoid"))

        self.model.compile(loss=self.loss_function, optimizer=self.optimizer,
                           metrics=['accuracy'])


class XZDecoder(_BaseNeuralNetworkDecoder):
    """LSTM decoder, can decode both X and Z errors from sequence data

    Defines a tensorflow.keras model with a number of LSTM layers followed by
    a number of dense (post-processing) layers.

    2 LSTM layers followed by DNN.

    Uses keras standard interface to learn, save and load a model
    """

    def __init__(self, input_shape, mask_value=-1, *args, **kwargs):
        self.mask_value = mask_value

        super().__init__(*args, **kwargs)

        self.input_shape = input_shape
        self.loss_function = self.masked_bce
        self.optimizer = keras.optimizers.Adam(lr=1e-3)

        # LSTM Layer + masking
        self.model.add(keras.layers.Masking(
              mask_value=-1, input_shape=input_shape))
        self.model.add(keras.layers.LSTM(units=36,
                                         input_shape=self.input_shape,
                                         activation="relu",
                                         return_sequences=True,
                                         ))
        self.model.add(keras.layers.LSTM(units=36,
                                         input_shape=self.input_shape,
                                         activation="relu",
                                         return_sequences=False,
                                         ))
        # post_processing
        self.model.add(keras.layers.Dense(units=48, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.Dense(units=24, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        self.model.add(keras.layers.Dense(units=12, activation='relu'))
        self.model.add(keras.layers.Dropout(0.2))
        # binary output from 0 to 1 (output 0 for x errors and output 2 for z)
        self.model.add(keras.layers.Dense(units=2, activation="sigmoid"))

        self.model.compile(loss=self.loss_function, optimizer=self.optimizer)

    def masked_bce(self, y_true, y_pred):
        mask = keras.backend.not_equal(y_true, self.mask_value),
        p = keras.backend.cast(y_true * mask, keras.backend.floatx())
        q = y_pred * mask
        return keras.backend.binary_crossentropy(p, q)
