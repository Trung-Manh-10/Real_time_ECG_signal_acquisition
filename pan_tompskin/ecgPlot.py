import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Use an interactive backend
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
def butter_lowpass(cutoff, fs, order=6):
    nyq = 0.5 * fs  # Tần số Nyquist
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=6):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

# Define the transform_data2 function
def transform_data2(input_file_path, cutoff_freq=0.5, sample_rate=500): 
    # Read data from the input file
    data = np.genfromtxt(input_file_path, delimiter=',', invalid_raise=False)

    # Apply low-pass filter to each column
    filtered_data = np.zeros_like(data)
    for i in range(data.shape[1]):
        filtered_data[:, i] = lowpass_filter(data[:, i], cutoff_freq, sample_rate) * 1000  # Volt to MilliVolt

    # Transform the data as per the requirements
    transformed_data = np.zeros((12, filtered_data.shape[0]))
    transformed_data[0, :] = filtered_data[:, 0]  # Row 1 = Column 1 (L1)
    transformed_data[1, :] = filtered_data[:, 1]  # Row 2 = Column 2 (L2)
    transformed_data[2, :] = filtered_data[:, 1] - filtered_data[:, 0]  # Row 3 = L3
    transformed_data[3, :] = -(filtered_data[:, 0] + filtered_data[:, 1]) / 2  # Row 4 = aVR
    transformed_data[4, :] = (filtered_data[:, 0] - (filtered_data[:, 1] - filtered_data[:, 0])) / 2  # Row 5 = aVL
    transformed_data[5, :] = (filtered_data[:, 1] + (filtered_data[:, 1] - filtered_data[:, 0])) / 2  # Row 6 = aVF
    transformed_data[6, :] = filtered_data[:, 11]  # Row 7 = Column 12 (V1)
    transformed_data[7, :] = filtered_data[:, 10]  # Row 8 = Column 11 (V2)
    transformed_data[8, :] = filtered_data[:, 9]   # Row 9 = Column 10 (V3)
    transformed_data[9, :] = filtered_data[:, 8]   # Row 10 = Column 9 (V4)
    transformed_data[10, :] = filtered_data[:, 7]  # Row 11 = Column 8 (V5)
    transformed_data[11, :] = filtered_data[:, 6]  # Row 12 = Column 7 (V6)

    return transformed_data



# Step 1: Define the input file path
input_file_path  = 'D:/1_Nghien_cuu/1_Luan_zan/data/ECG_27.txt'

# Step 2: Transform the data using transform_data2
transformed_data = transform_data2(input_file_path)

# Step 3: Define titles for each row
titles = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

# Function to plot all data in a single window with 2 columns and 6 rows
def plot_all_in_one_window(data, titles):
    fig, axes = plt.subplots(6, 2, figsize=(15, 24))  # Create a 6x2 grid of subplots
    axes = axes.flatten()  # Flatten the 2D array of axes for easy iteration

    for i in range(data.shape[0]):
        axes[i].plot(data[i, :], label=titles[i])  # Plot the data in the corresponding subplot
        axes[i].set_title(titles[i])  # Set the title for each subplot
        axes[i].set_xlabel('Sample Index')
        axes[i].set_ylabel('Amplitude')
        axes[i].legend()
        axes[i].grid(True)

    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()

# Step 4: Plot each row in a separate window
for i in range(transformed_data.shape[0]):
    plt.figure(figsize=(10, 6))  # Create a new figure for each row
    plt.plot(transformed_data[i, :], label=titles[i])  # Use the corresponding title
    plt.title(f'ECG Data Visualization - {titles[i]}')
    plt.xlabel('Sample Index')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid(True)
    plt.show()  # Show the plot for the current row

# Step 5: Call the function to plot all data in a single window
plot_all_in_one_window(transformed_data, titles)

