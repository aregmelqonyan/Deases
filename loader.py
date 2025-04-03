# import torch
# from torch.utils.data import DataLoader, Dataset
# import os
# import math
# import numpy as np
# from keras.preprocessing.image import load_img, img_to_array 
# from tensorflow.keras.utils import Sequence
# import cv2

# def list_folders(base_path):
#         folders_path = []
#         for root, dirs, files in os.walk(base_path):
#             for dir_name in dirs:
#                 folders_path.append(os.path.join(root, dir_name))
#         return folders_path

# train_folders = list_folders("data/train")
# dease = [row.split('/')[2] for row in train_folders]
# mapping_folders_name = {folder_name: i for i, folder_name in enumerate(dease)}


# class DataLoader(Sequence):
#     def __init__(self, dir_path, img_size=(256, 256), batch_size=10, shuffle=False):
#         self.image_dirs = list_folders(dir_path)
#         self.image_paths = self.list_all_jpg_images(dir_path)
#         self.batch_size = batch_size
#         self.shuffle = shuffle
#         self.labels = self.get_labels()
#         self.img_size = img_size
#         self.indices = np.arange(len(self.labels))
#         self.on_epoch_end()

#     def __len__(self):
#         return int(math.ceil(len(self.image_paths) / self.batch_size))

#     def __getitem__(self, index):
#         indices = self.indices[index * self.batch_size:(index + 1) * self.batch_size]

#         batch_image_paths = [self.image_paths[i] for i in indices]
#         batch_labels = np.array([self.labels[i] for i in indices])

#         images = self.__load_images(batch_image_paths)
#         return images, batch_labels
#         # return indices
    
#     def on_epoch_end(self):
#         if self.shuffle:
#             np.random.shuffle(self.indices)

    
#     def get_labels(self):
#         labels = [mapping_folders_name[image_path.split("/")[2]] for image_path in self.image_paths]
#         return labels
    
#     @staticmethod
#     def list_all_jpg_images(base_path):
#         jpg_files = []

#         for root, dirs, files in os.walk(base_path):
#             for file in files:
#                 if file.lower().endswith('.jpg'):
#                     jpg_files.append(os.path.join(root, file))

#         return jpg_files
    
#     def __load_images(self, batch_image_paths):
#         images = []
#         for image_path in batch_image_paths:
#             image = cv2.imread(image_path)
#             image = cv2.resize(image, self.img_size)
#             image = image / 255.0
#             images.append(image)
    
#         return np.stack(images, axis=0)


    
import torch
from torch.utils.data import DataLoader, Dataset
import os
import math
import numpy as np
from keras.preprocessing.image import load_img, img_to_array 
from tensorflow.keras.utils import Sequence
import cv2
import random

def list_folders(base_path):
    folders_path = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            folders_path.append(os.path.join(root, dir_name))
    return folders_path

train_folders = list_folders("data/train")
dease = [row.split('/')[2] for row in train_folders]
mapping_folders_name = {folder_name: i for i, folder_name in enumerate(dease)}


class DataLoader(Sequence):
    def __init__(self, dir_path, img_size=(256, 256), batch_size=10, shuffle=False):
        self.image_dirs = list_folders(dir_path)
        self.image_paths = self.list_all_jpg_images(dir_path)
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.labels = self.get_labels()
        self.img_size = img_size
        self.indices = np.arange(len(self.labels))
        self.on_epoch_end()

    def __len__(self):
        return int(math.ceil(len(self.image_paths) / self.batch_size))

    def __getitem__(self, index):
        indices = self.indices[index * self.batch_size:(index + 1) * self.batch_size]

        batch_image_paths = [self.image_paths[i] for i in indices]
        batch_labels = np.array([self.labels[i] for i in indices])

        images = self.__load_images(batch_image_paths)
        return images, batch_labels

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)

    def get_labels(self):
        labels = [mapping_folders_name[image_path.split("/")[2]] for image_path in self.image_paths]
        return labels
    
    @staticmethod
    def list_all_jpg_images(base_path):
        jpg_files = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.jpg'):
                    jpg_files.append(os.path.join(root, file))
        return jpg_files
    
    def __add_salt_pepper_noise(self, image, salt_prob=0.05, pepper_prob=0.05):
        noisy = np.copy(image)
        salt = np.random.rand(*image.shape[:2])
        noisy[salt < salt_prob] = 1.0
        pepper = np.random.rand(*image.shape[:2])
        noisy[pepper < pepper_prob] = 0.0
        return noisy
    
    def __add_gaussian_blur(self, image, kernel_size=(5,5)):
        return cv2.GaussianBlur(image, kernel_size, 0)
    
    def __zoom_sequence(self, image, zoom_out_factor=0.8, zoom_in_factor=1.2):
        h, w = image.shape[:2]
        
        new_h, new_w = int(h * zoom_out_factor), int(w * zoom_out_factor)
        zoomed_out = cv2.resize(image, (new_w, new_h))
        image = cv2.resize(zoomed_out, (w, h))
        # pad_top = (h - new_h) // 2
        # pad_bottom = h - new_h - pad_top
        # pad_left = (w - new_w) // 2
        # pad_right = w - new_w - pad_left
        # zoomed_out = cv2.copyMakeBorder(zoomed_out, pad_top, pad_bottom, 
        #                              pad_left, pad_right, 
        #                              cv2.BORDER_REPLICATE)
        
        # new_h, new_w = int(h * zoom_in_factor), int(w * zoom_in_factor)
        # zoomed_in = cv2.resize(zoomed_out, (new_w, new_h))
        # start_x = (new_w - w) // 2
        # start_y = (new_h - h) // 2
        # zoomed_in = zoomed_in[start_y:start_y+h, start_x:start_x+w]
        
        return image
    
    def __load_images(self, batch_image_paths):
        images = []
        augmentations = ['salt_pepper'] * 2 + ['gaussian_blur'] * 2 + ['zoom'] * 2 + ['normal'] * 4
        random.shuffle(augmentations)

        for i, image_path in enumerate(batch_image_paths):
            image_path
            image = cv2.imread(image_path)
            image = cv2.resize(image, self.img_size)
            image = image / 255.0
            
            aug_type = augmentations[i] if i < len(augmentations) else 'normal'
            
            if aug_type == 'salt_pepper':
                image = self.__add_salt_pepper_noise(image)

            elif aug_type == 'gaussian_blur':
                image = self.__add_gaussian_blur(image)
            elif aug_type == 'zoom':
                image = self.__zoom_sequence(image)
            images.append(image)

            if i < 2: 
                output_dir = "augmentation_checks"
                os.makedirs(output_dir, exist_ok=True)
                filename = f"{output_dir}/sample_{i}_{aug_type}.jpg"
                cv2.imwrite(filename, (image * 255).astype(np.uint8))
    
        return np.stack(images, axis=0)


