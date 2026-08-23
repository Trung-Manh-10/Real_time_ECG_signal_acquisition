import numpy as np
import matplotlib.pyplot as plt

# ==== Hàm đọc ECG từ cột thứ 2 ====
def read_ecg_file(path, column_index=1):
    ecg = []
    with open(path, 'r') as f:
        for line in f:
            try:
                parts = line.strip().split(",")
                if len(parts) > column_index:
                    ecg.append(float(parts[column_index]))
            except ValueError:
                pass
    return np.array(ecg)

# ==== Đường dẫn file ====
file_path_1 = r"D:\1_Nghien_cuu\TinyML\raw_ecg_3.txt"
file_path_2 = r"D:\1_Nghien_cuu\TinyML\data_ecg_3.txt"

# ==== Đọc dữ liệu ECG ====
ecg1 = read_ecg_file(file_path_1, column_index=1)  # Tín hiệu gốc
ecg2 = read_ecg_file(file_path_2, column_index=1)  # Tín hiệu đã lọc

# ==== Thông số ====
sample_rate = 500  # Hz
start_sec = 2
end_sec =  6  # Cắt từ giây thứ 5 đến giây thứ 15  
start_sample = int(start_sec * sample_rate)
end_sample = int(end_sec * sample_rate)

# ==== Cảnh báo nếu file không đủ dữ liệu ====
min_available_len = min(len(ecg1), len(ecg2))
if end_sample > min_available_len:
    print(f"[!] File không đủ dài, cắt đến {min_available_len/sample_rate:.2f} giây thay vì {end_sec}s")
    end_sample = min_available_len

# ==== Cắt tín hiệu ====
ecg1 = ecg1[start_sample:end_sample]
ecg2 = ecg2[start_sample:end_sample]

# ==== Đồng bộ độ dài và tạo trục thời gian ====
min_len = min(len(ecg1), len(ecg2))
ecg1 = ecg1[:min_len]
ecg2 = ecg2[:min_len]
time_axis = np.arange(min_len) / sample_rate

# ==== In thông tin ====
print(f"Số mẫu: {min_len} → thời gian: {min_len/sample_rate:.2f} giây")

# ==== VẼ TÍN HIỆU ECG ====
plt.figure(figsize=(12, 5))
plt.plot(time_axis, ecg1, label='Tín hiệu gốc', color='red', linewidth=1)
plt.title("Tín hiệu ECG gốc (miền thời gian)")
plt.xlabel("Thời gian (giây)")
plt.ylabel("Biên độ (mV)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 5))
plt.plot(time_axis, ecg2, label='Tín hiệu đã lọc', color='blue', linewidth=1)
plt.title("Tín hiệu ECG đã lọc (miền thời gian)")
plt.xlabel("Thời gian (giây)")
plt.ylabel("Biên độ (mV)")
plt.legend(
    loc='upper center',
    bbox_to_anchor=(0.92, 1),  # 0.5 là giữa, 1.15 là cao hơn trục y trên
    ncol=2  # Số cột hiển thị chú thích
)
plt.grid(True)
plt.tight_layout()
plt.show()

# ==== FFT ====
def compute_fft(signal, fs):
    n = len(signal)
    fft_result = np.fft.fft(signal)
    fft_freq = np.fft.fftfreq(n, d=1/fs)
    fft_magnitude = np.abs(fft_result) / n
    return fft_freq[:n // 2], fft_magnitude[:n // 2]

fft_freq1, fft_mag1 = compute_fft(ecg1, sample_rate)
fft_freq2, fft_mag2 = compute_fft(ecg2, sample_rate)

# ==== VẼ PHỔ TẦN (FFT) ====
plt.figure(figsize=(7, 4))
plt.plot(fft_freq1, fft_mag1, label='FFT gốc', color='red', linewidth=1)
plt.plot(fft_freq2, fft_mag2, label='FFT sau lọc', color='blue', linewidth=1)
#plt.title("So sánh phổ tần số (FFT)")
plt.xlabel("Tần số (Hz)", fontsize=15)
plt.ylabel("Biên độ (mV)", fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.ylim(0, 1)
plt.xlim(-1, 100)
plt.grid(True)
plt.show()
