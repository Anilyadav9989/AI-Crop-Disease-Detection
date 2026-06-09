from tensorflow.keras.preprocessing.image import ImageDataGenerator

datagen = ImageDataGenerator(validation_split=0.2)

generator = datagen.flow_from_directory(
    "dataset",
    target_size=(224,224),
    subset="training"
)

print(generator.class_indices)