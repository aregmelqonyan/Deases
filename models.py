import os
import tensorflow as tf
from tensorflow.keras import layers, models
from abc import ABC, abstractmethod
from loader import DataLoader
from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint
import datetime

class BatchTensorBoard(TensorBoard):
    def __init__(self, log_dir='./logs', **kwargs):
        super().__init__(log_dir=log_dir, **kwargs)
        self.batch_count = 0
    
    def on_train_batch_end(self, batch, logs=None):
        self.batch_count += 1
        if logs is not None:
            for name, value in logs.items():
                tf.summary.scalar('batch_' + name, value, step=self.batch_count)
            if self._train_writer is not None:
                self._train_writer.flush()
        
        if self._train_writer is not None:
            self._train_writer.flush()

class AbstractModel(ABC):
    def __init__(self, train_dir, val_dir):
        self.train_dir = train_dir
        self.val_dir = val_dir
        self.labels_count = self.get_train_folders_count()
        self.train_data_loader = DataLoader(train_dir)
        self.val_data_loader = DataLoader(val_dir)
    
    def get_train_folders_count(self):
        train_folder_path = 'data/train' 
        folders = [f for f in os.listdir(train_folder_path) if os.path.isdir(os.path.join(train_folder_path, f))]
        return len(folders)
    
    def compile(self, optimizer, loss, metrics=None):
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    
    @abstractmethod
    def add_custom_layers(self):
        pass

    @abstractmethod
    def fit(self):
        pass
    
    def get_checkpoint_path(self, model_name):
        """Helper method to get checkpoint directory path"""
        checkpoint_dir = f"checkpoints/{model_name}/"
        os.makedirs(checkpoint_dir, exist_ok=True)
        return os.path.join(checkpoint_dir, "weights-{epoch:02d}.weights.h5")

class VGGModel(AbstractModel, models.Model):
    def __init__(self, train_dir, val_dir):
        super().__init__(train_dir, val_dir)
        self.model = models.Sequential()
        self.add_custom_layers()
    
    def add_custom_layers(self):
        base_model = tf.keras.applications.VGG16(
            weights='pretrained_weights/vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5',
            include_top=False,
            input_shape=(256, 256, 3))
        base_model.trainable = False
        
        self.model.add(base_model)
        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(4096, activation='relu'))
        self.model.add(layers.Dense(4096, activation='relu'))
        self.model.add(layers.Dense(self.labels_count, activation='softmax'))
    
    def fit(self):
        log_dir = "logs/VGG/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        tensorboard_callback = BatchTensorBoard(log_dir=log_dir, histogram_freq=1, update_freq='batch')
        
        checkpoint_path = self.get_checkpoint_path("VGG")
        checkpoint_callback = ModelCheckpoint(
            filepath=checkpoint_path,
            save_weights_only=True,
            save_freq='epoch', 
            verbose=1
        )
        
        self.model.fit(
            self.train_data_loader,
            validation_data=self.val_data_loader,
            epochs=10,
            callbacks=[tensorboard_callback, checkpoint_callback]
        )

class InceptionModel(AbstractModel, models.Model):
    def __init__(self, train_dir, val_dir):
        super().__init__(train_dir, val_dir)
        self.model = models.Sequential()
        self.add_custom_layers()

    def add_custom_layers(self):
        base_model = tf.keras.applications.InceptionV3(
            weights='pretrained_weights/inception_v3_weights_tf_dim_ordering_tf_kernels_notop.h5',
            include_top=False,
            input_shape=(256, 256, 3))
        base_model.trainable = False
        self.model.add(base_model)

        self.model.add(layers.GlobalAveragePooling2D())  
        self.model.add(layers.Dense(4096, activation='relu'))
        self.model.add(layers.Dense(4096, activation='relu')) 
        self.model.add(layers.Dense(self.labels_count, activation='softmax'))
        return self.model
    
    def fit(self):
        log_dir = "logs/inception/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        tensorboard_callback = BatchTensorBoard(log_dir=log_dir, histogram_freq=1, update_freq='batch')

        checkpoint_path = self.get_checkpoint_path("Inception")
        checkpoint_callback = ModelCheckpoint(
            filepath=checkpoint_path,
            save_weights_only=True,
            save_freq='epoch', 
            verbose=1
        )

        self.model.fit(
            self.train_data_loader,
            validation_data=self.val_data_loader,
            epochs=10,
            callbacks=[tensorboard_callback, checkpoint_callback]
        )

class ResNet(AbstractModel, models.Model):
    def __init__(self, train_dir, val_dir):
        super().__init__(train_dir, val_dir)
        self.model = models.Sequential()
        self.add_custom_layers()
    
    def add_custom_layers(self):
        base_model = tf.keras.applications.ResNet50(
            weights='pretrained_weights/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5',
            include_top=False,
            input_shape=(256, 256, 3))
        base_model.trainable = False
        self.model.add(base_model)

        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(4096, activation='relu'))
        self.model.add(layers.Dense(4096, activation='relu')) 
        self.model.add(layers.Dense(self.labels_count, activation='softmax'))
        return self.model
    
    def fit(self):
        log_dir = "logs/resnet/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        tensorboard_callback = BatchTensorBoard(log_dir=log_dir, histogram_freq=1, update_freq='batch')

        # Create ModelCheckpoint callback
        checkpoint_path = self.get_checkpoint_path("ResNet")
        checkpoint_callback = ModelCheckpoint(
            filepath=checkpoint_path,
            save_weights_only=True,
            save_freq='epoch',
            verbose=1
        )

        self.model.fit(
            self.train_data_loader,
            validation_data=self.val_data_loader,
            epochs=10,
            callbacks=[tensorboard_callback, checkpoint_callback]
        )
  
model1 = VGGModel("data/train", "data/valid")
model1.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
model1.fit()
print("VGG finshed!!!!!!!!!!!!")
model2 = ResNet("data/train", "data/valid")
model2.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
model2.fit()
print("Resnet finshed!!!!!!!!!!!!")
model3 = InceptionModel("data/train", "data/valid")
model3.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
model3.fit()
print("Inception finshed!!!!!!!!!!!!")
