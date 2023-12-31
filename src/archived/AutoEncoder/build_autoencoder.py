# Usage: python build_autoencoder.py

# This file builds an autoencoder on summarized feature statistics for each bag.
# **Note: Ensure that you are in the project's `src/archived/AutoEncoder` directory and the data files are in the project's `data` directory. Otherwise, the code will 
# fail due to inconsistent file paths**

# Setting things up
import keras
import os
from keras import layers
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler

pd.set_option('display.float_format', lambda x: '%.3f' % x)

DATA_PATH = "../../../data/raw/dataset.csv"

if __name__ == "__main__":
    
    # Reading and processing data
    print("Reading data from", DATA_PATH + "...")
    data = pd.read_csv(DATA_PATH).iloc[:,1:]
    print("Data read completed!\n")

    print("Processing data...")
    selected_columns = [
        'transcript_id', 'transcript_position','left_dwell', 'left_std', 'left_mean',
        'mid_dwell', 'mid_std', 'mid_mean',
        'right_dwell', 'right_std', 'right_mean', 'label'
    ]
    processed_data = data[selected_columns]

    # Filter data to keep non-anomalous data (i.e. label==0)
    x_data_label_0 = processed_data[processed_data['label'] == 0].drop(columns=['label'])

    # For test set, both labels 0 and 1 are needed
    x_data = processed_data.copy()

    # Preparing data for train/val/test split
    unique_bags = processed_data['transcript_id'].unique()
    np.random.seed(1)
    np.random.shuffle(unique_bags)

    train_size = int(0.6 * len(unique_bags))
    val_size = int(0.2 * len(unique_bags))
    train_genes = unique_bags[:train_size]
    val_genes = unique_bags[train_size:train_size + val_size]
    test_genes = unique_bags[train_size + val_size:]

    train_df = x_data_label_0[x_data_label_0['transcript_id'].isin(train_genes)]
    val_df = x_data_label_0[x_data_label_0['transcript_id'].isin(val_genes)]
    test_df = x_data[x_data['transcript_id'].isin(test_genes)] # we want label 1 as well

    directory = "../../../data/curated"
    file_path = os.path.join(directory, "test_data.csv")
    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the DataFrame to CSV
    test_df.to_csv(file_path, index=False)
    print("Data processed and split to training/validating/testing sets!\n")
    print("Test set saved to data/curated/test_data.csv.\n")

    # Scale data based on training set
    print("Scaling data...")
    scaler = MinMaxScaler()
    features_to_scale = train_df.drop(columns=['transcript_id', 'transcript_position'])
    train_df_scaled = scaler.fit_transform(features_to_scale)
    val_features_to_scale = val_df.drop(columns=['transcript_id', 'transcript_position'])
    val_df_scaled = scaler.transform(val_features_to_scale)
    joblib.dump(scaler, "../../../model/autoencoder_scaler")
    print("Data scaled and scaler saved!\n")

    # Initialising autoencoder model with parameters
    print("Initialising autoencoder model...")
    
    # Number of desired features/dimensions in encoded data
    encoding_dim = 3  # Hyperparameter: number of layers

    # Number of features/dimensions in original data
    input_shape = (train_df_scaled.shape[1],)  
    
    # Create the input layer
    input_img = keras.Input(shape=input_shape)

    # Defining the architecture of the autoencoder - this model has 3 hidden layers (encoding_dim = 3)
    # First hidden layer
    hidden1_size = 64  # Hyperparameter: number of neurons in the first hidden layer
    hidden1 = layers.Dense(hidden1_size, activation='relu')(input_img)

    # Second hidden layer (encoded layer)
    encoded = layers.Dense(encoding_dim, activation='relu')(hidden1)

    # Third hidden layer (decoder starts here)
    hidden2_size = hidden1_size
    hidden2 = layers.Dense(hidden2_size, activation='relu')(encoded)

    # Output layer
    decoded = layers.Dense(input_shape[0], activation='sigmoid')(hidden2)

    # Create the autoencoder model
    autoencoder = keras.Model(input_img, decoded)
    autoencoder.compile(optimizer='adam', loss='binary_crossentropy')
    print("Autoencoder model initialised and parameters set!\n")

    # Training the model
    print(f"Training autoencoder model...\n")
    autoencoder.fit(train_df_scaled, train_df_scaled,
                    epochs=5,
                    batch_size=256,
                    shuffle=True,
                    validation_data=(val_df_scaled, val_df_scaled))
    
    # Saving model
    print("Saving model...")
    joblib.dump(autoencoder, "../../../model/autoencoder")
    print("Model saved!")

    
