#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NNDecoder.py
@author Luc Kusters
@date 26-09-2022
"""

import datetime
import numpy
import os
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

    def __init__(self, *args, **kwargs):
        print(args, kwargs)
        super().__init__(*args, **kwargs)
        self.model = keras.models.Sequential()

    @classmethod
    def from_path(cls, path, custom_objects=None, *args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.load(path, custom_objects)
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

    def compile(self, *args, **kwargs):
        """Wrapper for self.models.compile"""
        self.model.compile(*args, **kwargs)


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

    def __init__(self, checkpoint_filepath=None, *args, **kwargs):
        if checkpoint_filepath is None:
            if not os.path.exists("models"):
                os.mkdir("models")
            self.checkpoint_filepath = os.path.join(
                "models",
                f"model_{type(self).__name__}_{datetime.datetime.now()}"
                )
            print(f"Saving checkpoints to {self.checkpoint_filepath}...")
        super().__init__(*args, **kwargs)

    def define_model(self, input_shape):
        self.input_shape = input_shape
        self.loss_function = keras.losses.BinaryCrossentropy()
        self.optimizer = keras.optimizers.Adam(learning_rate=1e-3)
        # decay=1e-5)

        # LSTM Layer + masking
        self.model.add(keras.layers.Masking(
              mask_value=self.mask_value, input_shape=input_shape))
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

        # checkpoint callback
        self.callbacks = []
        self.callbacks.append(keras.callbacks.ModelCheckpoint(
                filepath=self.checkpoint_filepath,
                monitor="val_loss",
                verbose=0,
                save_best_only=True,
                save_weights_only=False,
                mode="auto",
                save_freq="epoch",
                options=None,
                initial_value_threshold=None,
                ))

    def compile(self, *args, **kwargs):
        self.define_model(*args, **kwargs)
        self.model.compile(loss=self.loss_function, optimizer=self.optimizer,
                           metrics=['accuracy'])


class DualLSTMDecoderXZ(_BaseNeuralNetworkDecoder):
    """LSTM decoder, can decode both X and Z errors from sequence data

    Defines a tensorflow.keras model with a number of LSTM layers followed by
    a number of dense (post-processing) layers.

    2 LSTM layers followed by DNN.

    Uses keras standard interface to learn, save and load a model
    """

    def __init__(self, input_shape=(21, 12), x_mask_value=-1,
                 y_mask_value=-1, *args, **kwargs):
        self.x_mask_value = x_mask_value
        self.y_mask_value = y_mask_value

        super().__init__(*args, **kwargs)

        self.input_shape = input_shape
        self.loss_function = self.masked_bce
        self.optimizer = keras.optimizers.Adam(learning_rate=1e-3)

        # LSTM Layer + masking
        self.model.add(keras.layers.Masking(
              mask_value=self.x_mask_value, input_shape=input_shape))
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

    @classmethod
    def from_path(cls, path, custom_objects=None, **kwargs):
        if custom_objects is None:
            custom_objects = {"masked_bce": cls.masked_bce}
        return super().from_path(path, custom_objects=custom_objects, **kwargs)

    @staticmethod
    def masked_bce(y_true, y_pred, y_mask_value=0):
        mask = keras.backend.not_equal(y_true, y_mask_value),
        p = keras.backend.cast(y_true * mask, keras.backend.floatx())
        q = y_pred * mask
        return keras.backend.binary_crossentropy(p, q)


class DNNDecoder(_BaseNeuralNetworkDecoder):
    """Deep neural network (DNN) decoder, can decode either Z or X errors

    The DNN Decoder requires fixed input size data.

    Defines a tensorflow.keras model with a number of dense layers.

    Uses keras standard interface to learn, save and load a model
    """

    def __init__(self, checkpoint_filepath=None, *args, **kwargs):
        if checkpoint_filepath is None:
            if not os.path.exists("models"):
                os.mkdir("models")
            self.checkpoint_filepath = os.path.join(
                "models",
                f"model_{type(self).__name__}_{datetime.datetime.now()}"
                )
            print(f"Saving checkpoints to {self.checkpoint_filepath}...")
        super().__init__(*args, **kwargs)

    def define_model(self, input_shape,
                     base_neuron_scale=12,
                     large_block_rscale=4,
                     mid_block_rscale=2,
                     small_block_rscale=1,
                     repeats=1,
                     n_large_blocks=1,
                     n_mid_blocks=1,
                     n_small_blocks=1,
                     learning_rate=1e-4, decay=None,
                     with_dropout=True,
                     dropout_p=0.2,
                     amsgrad=True,
                     save_best_only=True,
                     save_regular_interval=True,
                     save_interval=1,
                     use_regularizer=True,
                     ):
        self.input_shape = input_shape
        self.loss_function = keras.losses.BinaryCrossentropy()
        if decay is None:
            decay = learning_rate
        self.optimizer = keras.optimizers.Adam(learning_rate=learning_rate,
                                               decay=decay,
                                               amsgrad=amsgrad)
        # decay=1e-5)

        # post_processing
        self.model.add(keras.layers.InputLayer(input_shape=self.input_shape))
        # large block (from input)
        # large
        self.add_n_blocks(units=base_neuron_scale*large_block_rscale,
                          repeats=repeats*n_large_blocks,
                          with_dropout=with_dropout,
                          dropout_p=dropout_p,
                          )
        # mid
        self.add_n_blocks(units=base_neuron_scale*mid_block_rscale,
                          repeats=repeats*n_mid_blocks,
                          with_dropout=with_dropout,
                          dropout_p=dropout_p,
                          )
        # small
        self.add_n_blocks(units=base_neuron_scale*small_block_rscale,
                          repeats=repeats*n_small_blocks,
                          with_dropout=with_dropout,
                          dropout_p=dropout_p,
                          )
        # binary output from 0 to 1
        self.model.add(keras.layers.Dense(units=1, activation="sigmoid"))

        # checkpoint callback
        self.callbacks = []
        self.callbacks.append(keras.callbacks.ModelCheckpoint(
                filepath=f"{self.checkpoint_filepath}_cpt",
                monitor="val_accuracy",
                verbose=0,
                save_best_only=save_best_only,
                save_weights_only=False,
                mode="auto",
                save_freq="epoch",
                options=None,
                initial_value_threshold=None,
                ))
        if save_regular_interval:
            self.callbacks.append(RegularIntervalModelSaver(
                self.checkpoint_filepath, epoch_interval=save_interval))
        print(self.callbacks)

    def add_n_blocks(self, units, repeats,
                     with_dropout, dropout_p,
                     activation="relu"):
        if units == 0:
            return
        for _ in range(repeats):
            self.model.add(keras.layers.Dense(
                units=units,
                activation=activation,
                #kernel_regularizer="l1",
                #bias_regularizer="l1",
                ))
            if with_dropout:
                self.model.add(keras.layers.Dropout(dropout_p))

    def compile(self, *args, **kwargs):
        self.define_model(*args, **kwargs)
        self.model.compile(loss=self.loss_function, optimizer=self.optimizer,
                           metrics=['accuracy'])

    def decode_sequence_to_parity(self, sequence_data, parity_threshold=0.5,
                                  batch_process=False):
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
        if not batch_process:
            sequence_data = sequence_data.flatten()[numpy.newaxis]

        predictions = self.model.predict(sequence_data)
        parities = predictions >= parity_threshold
        return parities

