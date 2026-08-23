import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import seaborn as sns

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

# ==== Vùng hiển thị ====
display_start_sec = 0
display_end_sec = 3
display_start_sample = int(display_start_sec * sample_rate)
display_end_sample = int(display_end_sec * sample_rate)
ecg1_display = ecg1[display_start_sample:display_end_sample]
ecg2_display = ecg2[display_start_sample:display_end_sample]
time_display = np.arange(display_start_sample, display_end_sample) / sample_rate

import seaborn as sns
sns.set(style="whitegrid")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=False)

sns.lineplot(x=time_display, y=ecg1_display, ax=ax1, color='red', label='Tín hiệu gốc')
#ax1.set_title(f"Tín hiệu gốc từ {display_start_sec}s đến {display_end_sec}s", fontsize=17)
ax1.set_ylabel("Biên độ (mV)", fontsize=17)
ax1.tick_params(axis='both', labelsize=15)
ax1.legend(fontsize=15)
ax1.grid(True)

sns.lineplot(x=time_display, y=ecg2_display, ax=ax2, color='blue', label='Tín hiệu đã lọc')
#ax2.set_title(f"Tín hiệu đã lọc từ {display_start_sec}s đến {display_end_sec}s", fontsize=17)
ax2.set_xlabel("Thời gian (giây)", fontsize=17)
ax2.set_ylabel("Biên độ (mV)", fontsize=17)
ax2.tick_params(axis='both', labelsize=15)
ax2.legend(fontsize=15)
ax2.grid(True)

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

plt.figure(figsize=(12, 5))
plt.plot(fft_freq1, fft_mag1, label='FFT gốc', color='red', linewidth=1)
plt.plot(fft_freq2, fft_mag2, label='FFT sau lọc', color='blue', linewidth=1)
plt.title("So sánh phổ tần số (FFT)")
plt.xlabel("Tần số (Hz)")
plt.ylabel("Biên độ (mV)")
plt.ylim(0, 1)
plt.xlim(-1, 100)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ==== PHÁT HIỆN R ====
peaks_all, _ = find_peaks(ecg2, distance=sample_rate*0.4, height=0.3)
rr_intervals_all = np.diff(peaks_all) / sample_rate
avg_rr_all = np.mean(rr_intervals_all)
bpm_all = 60 / avg_rr_all

#print(f"[Toàn bộ file] N: {len(rr_intervals_all)}")
#print(f"[Toàn bộ file] R-R trung bình: {avg_rr_all*1000:.2f} ms")
#print()
#print(f"[Toàn bộ file] Nhịp tim (BPM): {bpm_all:.2f}")

# ==== VẼ R TRONG VÙNG HIỂN THỊ ====
peaks_display = [p for p in peaks_all if display_start_sample <= p < display_end_sample]
peaks_display_relative = np.array(peaks_display) - display_start_sample

plt.figure(figsize=(12, 5))
plt.plot(time_display, ecg2_display, label='Tín hiệu đã lọc', color='blue')
plt.plot(time_display[peaks_display_relative], ecg2_display[peaks_display_relative], 'ro', label='Đỉnh R')
plt.title(f"Phát hiện đỉnh R từ {display_start_sec}s đến {display_end_sec}s")
plt.xlabel("Thời gian (giây)")
plt.ylabel("Biên độ (mV)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ==== TÌM Q, S ====
def find_q_s_points(signal, r_peaks, sample_rate, window=0.06): 
    q_points = []
    s_points = []
    samples_window = int(window * sample_rate)
    for r in r_peaks:
        start_q = max(r - samples_window, 0)
        q_region = signal[start_q:r]
        q = start_q + np.argmin(q_region) if len(q_region) > 0 else np.nan
        q_points.append(q)
        end_s = min(r + samples_window, len(signal))
        s_region = signal[r:end_s]
        s = r + np.argmin(s_region) if len(s_region) > 0 else np.nan
        s_points.append(s)
    return np.array(q_points), np.array(s_points)

q_points, s_points = find_q_s_points(ecg2, peaks_all, sample_rate)
qrs_durations = (s_points - q_points) / sample_rate

#print(f"[Toàn bộ file] Thời gian QRS trung bình: {np.nanmean(qrs_durations)*1000:.2f} ms")

# ==== TÌM P ====
def find_p_points(signal, r_peaks, sample_rate, window=0.12, delay=0.08):
    p_points = []
    samples_window = int(window * sample_rate)
    samples_delay = int(delay * sample_rate)
    for r in r_peaks:
        end_p = max(r - samples_delay, 0)
        start_p = max(end_p - samples_window, 0)
        p_region = signal[start_p:end_p]
        p = start_p + np.argmax(p_region) if len(p_region) > 0 else np.nan
        p_points.append(p)
    return np.array(p_points)

p_points = find_p_points(ecg2, peaks_all, sample_rate)
pr_intervals = (peaks_all - p_points) / sample_rate
#print(f"[Toàn bộ file] Khoảng PR trung bình: {np.nanmean(pr_intervals)*1000:.2f} ms")

# ==== VẼ P-Q-R-S TRONG VÙNG ====
q_display = [q for q in q_points if display_start_sample <= q < display_end_sample]
r_display = [r for r in peaks_all if display_start_sample <= r < display_end_sample]
s_display = [s for s in s_points if display_start_sample <= s < display_end_sample]
p_display = [p for p in p_points if display_start_sample <= p < display_end_sample]

plt.figure(figsize=(12, 5))
plt.plot(time_display, ecg2_display, label='Tín hiệu đã lọc', color='blue')
plt.plot((np.array(p_display)/sample_rate), ecg2[p_display], 'ko', label='P')
plt.plot((np.array(q_display)/sample_rate), ecg2[q_display], 'go', label='Q')
plt.plot((np.array(r_display)/sample_rate), ecg2[r_display], 'ro', label='R')
plt.plot((np.array(s_display)/sample_rate), ecg2[s_display], 'mo', label='S')
plt.title(f"Đánh dấu P, Q, R, S từ {display_start_sec}s đến {display_end_sec}s")
plt.xlabel("Thời gian (giây)")
plt.ylabel("Biên độ (mV)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# ==== Tính thống kê khoảng RR ====
print(f"===== Khoảng RR (R-R interval) =====")
print(f"Số lượng N: {len(rr_intervals_all)}")
print(f"Giá trị nhỏ nhất (min): {np.min(rr_intervals_all)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(rr_intervals_all)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(rr_intervals_all)*1000:.2f} ms")
print()

# ==== Tính thống kê khoảng QRS ====
print(f"===== Thời gian QRS =====")
qrs_durations_clean = qrs_durations[~np.isnan(qrs_durations)]
print(f"Số lượng N: {len(qrs_durations_clean)}")
print(f"Giá trị nhỏ nhất (min): {np.min(qrs_durations_clean)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(qrs_durations_clean)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(qrs_durations_clean)*1000:.2f} ms")
print()

# ==== Tính thống kê khoảng PR ====
pr_intervals_clean = pr_intervals[~np.isnan(pr_intervals)]
print(f"===== Khoảng PR =====")
print(f"Số lượng N: {len(pr_intervals_clean)}")
print(f"Giá trị nhỏ nhất (min): {np.min(pr_intervals_clean)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(pr_intervals_clean)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(pr_intervals_clean)*1000:.2f} ms")
print()

# ==== Tính thời gian sóng P ====
def find_p_start_end(signal, p_peaks, sample_rate, window=0.04):
    """
    Tìm điểm bắt đầu và kết thúc sóng P dựa trên đỉnh P.
    window: thời gian cửa sổ tìm min biên độ (giây)
    """
    p_start_points = []
    p_end_points = []
    samples_window = int(window * sample_rate)
    
    for p in p_peaks:
        # Tìm điểm bắt đầu P: tìm min biên độ trong cửa sổ trước đỉnh P
        start_search = max(p - samples_window, 0)
        p_region_before = signal[start_search:p]
        if len(p_region_before) > 0:
            p_start = start_search + np.argmin(p_region_before)
        else:
            p_start = np.nan
        p_start_points.append(p_start)

        # Tìm điểm kết thúc P: tìm min biên độ trong cửa sổ sau đỉnh P
        end_search = min(p + samples_window, len(signal))
        p_region_after = signal[p:end_search]
        if len(p_region_after) > 0:
            p_end = p + np.argmin(p_region_after)
        else:
            p_end = np.nan
        p_end_points.append(p_end)
    
    return np.array(p_start_points), np.array(p_end_points)

# Áp dụng hàm để tìm điểm bắt đầu và kết thúc sóng P
p_start_points, p_end_points = find_p_start_end(ecg2, p_points, sample_rate)

# Tính thời gian sóng P thực tế
p_durations_real = (p_end_points - p_start_points) / sample_rate

# Lọc nan nếu có
p_durations_real_clean = p_durations_real[~np.isnan(p_durations_real)]

print(f"===== Thời gian sóng P thực tế =====")
print(f"Số lượng N: {len(p_durations_real_clean)}")
print(f"Giá trị nhỏ nhất (min): {np.min(p_durations_real_clean)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(p_durations_real_clean)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(p_durations_real_clean)*1000:.2f} ms")
print()

# ==== Tính toán nhịp tim (BPM) từ khoảng RR ====
bpm_all = 60 / rr_intervals_all  # mảng nhịp tim theo từng khoảng RR

print(f"===== Nhịp tim (BPM) =====")
print(f"Số lượng N: {len(bpm_all)}")
print(f"Giá trị nhỏ nhất (min): {np.min(bpm_all):.2f} BPM")
print(f"Giá trị lớn nhất (max): {np.max(bpm_all):.2f} BPM")
print(f"Trung bình (mean): {np.mean(bpm_all):.2f} BPM")


plt.figure(figsize=(10, 5))
plt.hist(bpm_all, bins=30, color='purple', alpha=0.7)
plt.title("Phân bố nhịp tim (BPM) từ khoảng RR")
plt.xlabel("Nhịp tim (BPM)")
plt.ylabel("Số lượng")
plt.grid(True)
plt.tight_layout()
plt.show()
