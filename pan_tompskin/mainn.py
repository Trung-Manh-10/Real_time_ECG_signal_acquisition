from Pan_Tom import Pan_Tompkins_QRS
from Pan_Tom import heart_rate
from Pan_Tom import ECGCycleCutter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

file_path_1 = r"D:\1_Nghien_cuu\TinyML\data_ecg_6.txt"
fs = 500  # tần số mẫu của dữ liệu

# Đọc tín hiệu ECG
ecg_signal = Pan_Tompkins_QRS.read_ecg_file(file_path_1, column_index=1)
ecg_df = pd.DataFrame({
    'TimeStamp': np.arange(len(ecg_signal)),
    'ecg': ecg_signal
})

# Khởi tạo detector với fs
detector = Pan_Tompkins_QRS(fs=fs)

# Xử lý
output_signal = detector.solve(ecg_df)
# Xử lý và nhận về 4 kết quả
bpass, der, sqr, mwin = detector.solve(ecg_df)


start = int(0 * fs)
end = int(10 * fs)

time_axis = np.arange(start, end) / fs  # Đổi mẫu sang giây


plt.figure(figsize=(15,4))
plt.plot(time_axis, bpass[start:end])
#plt.title('Bandpassed Signal (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

plt.figure(figsize=(15,4))
plt.plot(time_axis, der[start:end])
#plt.title('Derivative Signal (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

plt.figure(figsize=(15,4))
plt.plot(time_axis, sqr[start:end])
#plt.title('Squared Signal (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

plt.figure(figsize=(15,4))
plt.plot(time_axis, mwin[start:end])
#plt.title('Moving Window Integrated Signal (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()


r_detector = heart_rate(raw_signal=bpass, filtered_signal=bpass, integrated_signal=mwin, fs=fs)
r_peaks = r_detector.find_r_peaks()
filtered_r_peaks = [r_peaks[0]]
for r in r_peaks[1:]:
    if r - filtered_r_peaks[-1] > int(0.3 * fs):  # 300ms
        filtered_r_peaks.append(r)


# Vẽ đỉnh R
plt.figure(figsize=(15,4))
plt.plot(time_axis, bpass[start:end])
r_peaks_in_window = [p for p in r_peaks if start <= p < end]
plt.scatter(np.array(r_peaks_in_window)/fs, bpass[r_peaks_in_window], color='red', label='R Peaks')
#plt.title('Detected R-peaks (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

rr_intervals = np.diff(r_peaks) / fs  # đơn vị giây

# Tính và in min, max, mean
rr_min = np.min(rr_intervals)
rr_max = np.max(rr_intervals)
rr_mean = np.mean(rr_intervals)

print("\n--- Thống kê RR Intervals ---")
print(f"Số lượng N:  {len(rr_intervals)}")
print(f"Min RR interval   = {rr_min:.3f} s")
print(f"Max RR interval   = {rr_max:.3f} s")
print(f"Mean RR interval  = {rr_mean:.3f} s")
print()






# === Kiểm tra các khoảng R-R bất thường ===
threshold_high = 1.6  # giây
threshold_low = 0.3   # giây

abnormal_indices = np.where((rr_intervals > threshold_high) | (rr_intervals < threshold_low))[0]

print("===== R-R interval bất thường =====")
print(f"Tổng số khoảng R-R bất thường: {len(abnormal_indices)}")
if len(abnormal_indices) > 0:
    for idx in abnormal_indices:
        t1 = r_peaks[idx] / fs
        t2 = r_peaks[idx + 1] / fs
        rr = rr_intervals[idx]
        print(f"R-R bất thường tại đỉnh R thứ {idx} và {idx + 1} (t1={t1:.2f}s, t2={t2:.2f}s) - RR = {rr:.3f} s")
else:
    print("Không có khoảng R-R bất thường.")
print()

#print("R peaks (first 20):", r_peaks[:20])
#print("RR intervals (first 20):", rr_intervals[:20])
# Lấy biên độ tại các đỉnh R trên tín hiệu bpass
r_values = bpass[r_peaks]

# Giá trị lớn nhất và nhỏ nhất tại đỉnh R
Rmax = np.max(r_values)
Rmin = np.min(r_values)

# Tổng số đỉnh R
total_r = len(r_peaks)

print(f"Tổng số đỉnh R phát hiện: {total_r}")
print(f"Giá trị lớn nhất tại đỉnh R (Rmax): {Rmax:.4f}")
print(f"Giá trị nhỏ nhất tại đỉnh R (Rmin): {Rmin:.4f}")
print()

# Ngưỡng thấp để phát hiện đỉnh R bất thường (ví dụ 10% Rmax)
threshold_low_amplitude = 0.4 * Rmax

# Tìm các đỉnh R có biên độ thấp hơn ngưỡng này
abnormal_r_indices = np.where(r_values < threshold_low_amplitude)[0]

if len(abnormal_r_indices) > 0:
    print(f"Có {len(abnormal_r_indices)} đỉnh R có biên độ thấp (dưới {threshold_low_amplitude:.4f}) - có thể bất thường:")
    for idx in abnormal_r_indices:
        peak_loc = r_peaks[idx]
        peak_val = r_values[idx]
        peak_time = peak_loc / fs  # thời gian tính theo giây
        print(f" - Đỉnh R tại mẫu {peak_loc} (thời gian {peak_time:.3f} s) với biên độ {peak_val:.4f}")
else:
    print("Không phát hiện đỉnh R có biên độ thấp bất thường.")
    print()









# Hàm tìm Q, S quanh đỉnh R
def find_q_s_points(signal, r_peaks, fs, window=0.07):
    q_points = []
    s_points = []
    samples_window = int(window * fs)

    for r in r_peaks:
        # === Tìm Q (trước R) ===
        start_q = max(r - samples_window, 0)
        q_region = signal[start_q:r]
        if len(q_region) > 0:
            q = start_q + np.argmin(q_region)
        else:
            q = np.nan
        q_points.append(q)

        # === Tìm S (sau R): điểm cực tiểu đầu tiên mà sau nó có xu hướng tăng ===
        end_s = min(r + samples_window, len(signal))
        s_region = signal[r:end_s]
        s = np.nan

        for i in range(1, len(s_region) - 1):
            if s_region[i] < s_region[i - 1] and s_region[i + 1] > s_region[i]:
                s = r + i
                break

        # Nếu không tìm thấy điểm thỏa mãn, fallback về argmin
        if np.isnan(s) and len(s_region) > 0:
            s = r + np.argmin(s_region)

        s_points.append(s)

    return np.array(q_points), np.array(s_points)


# Hàm tìm P trước đỉnh R
def find_p_points(signal, r_peaks, fs, window=0.12, delay=0.08):
    p_points = []
    samples_window = int(window * fs)
    samples_delay = int(delay * fs)
    for r in r_peaks:
        end_p = max(r - samples_delay, 0)
        start_p = max(end_p - samples_window, 0)
        p_region = signal[start_p:end_p]
        p = start_p + np.argmax(p_region) if len(p_region) > 0 else np.nan
        p_points.append(p)
    return np.array(p_points)

# Tìm Q, S, P
q_points, s_points = find_q_s_points(bpass, r_peaks, fs)
p_points = find_p_points(bpass, r_peaks, fs)
qrs_durations = (s_points - q_points) / fs

# Lọc các điểm nằm trong cửa sổ 5-10s để vẽ
p_display = [int(p) for p in p_points if not np.isnan(p) and start <= p < end]
q_display = [q for q in q_points if start <= q < end]
r_display = [r for r in r_peaks if start <= r < end]
s_display = [s for s in s_points if start <= s < end]

# Vẽ tín hiệu và các điểm sóng P, Q, R, S
plt.figure(figsize=(15,4))
plt.plot(time_axis, bpass[start:end])
plt.scatter(np.array(p_display)/fs, bpass[p_display], color='black', marker='o', label='P wave')
plt.scatter(np.array(q_display)/fs, bpass[q_display], color='green', marker='o', label='Q wave')
plt.scatter(np.array(r_display)/fs, bpass[r_display], color='red', marker='o', label='R peak')
plt.scatter(np.array(s_display)/fs, bpass[s_display], color='magenta', marker='o', label='S wave')
#plt.title('ECG Signal with P, Q, R, S waves (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

print()
# ==== Tính thống kê khoảng QRS ====
print(f"===== Thời gian QRS =====")
qrs_durations_clean = qrs_durations[~np.isnan(qrs_durations)]
print(f"Số lượng N: {len(qrs_durations_clean)}")
print(f"Giá trị nhỏ nhất (min): {np.min(qrs_durations_clean)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(qrs_durations_clean)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(qrs_durations_clean)*1000:.2f} ms")

# ==== Tính toán nhịp tim (BPM) từ khoảng RR ====
rrr_intervals = rr_intervals[rr_intervals !=0]
bpm_all = 60 / rrr_intervals # mảng nhịp tim theo từng khoảng RR

print()
print(f"===== Nhịp tim (BPM) =====")
print(f"Số lượng N: {len(bpm_all)}")
print(f"Giá trị nhỏ nhất (min): {np.min(bpm_all):.2f} BPM")
print(f"Giá trị lớn nhất (max): {np.max(bpm_all):.2f} BPM")
print(f"Trung bình (mean): {np.mean(bpm_all):.2f} BPM")
print()

# ==== Tính thời gian sóng P ====
def find_p_start_end(signal, p_peaks, fs, window=0.07):
    p_start_points = []
    p_end_points = []
    samples_window = int(window * fs)
    
    for p in p_peaks:
        if np.isnan(p):
            p_start_points.append(np.nan)
            p_end_points.append(np.nan)
            continue
        
        p = int(p)  # ép kiểu trước khi dùng slice

        # Tìm điểm bắt đầu P
        start_search = max(p - samples_window, 0)
        p_region_before = signal[start_search:p]
        if len(p_region_before) > 0:
            p_start = start_search + np.argmin(p_region_before)
        else:
            p_start = np.nan
        p_start_points.append(p_start)

        # Tìm điểm kết thúc P
        end_search = min(p + samples_window, len(signal))
        p_region_after = signal[p:end_search]
        if len(p_region_after) > 0:
            p_end = p + np.argmin(p_region_after)
        else:
            p_end = np.nan
        p_end_points.append(p_end)
    
    return np.array(p_start_points), np.array(p_end_points)


# Áp dụng hàm để tìm điểm bắt đầu và kết thúc sóng P
p_start_points, p_end_points = find_p_start_end(bpass, p_points, fs)

# Tính thời gian sóng P thực tế
p_durations_real = (p_end_points - p_start_points) / fs

# Lọc nan nếu có
p_durations_real_clean = p_durations_real[~np.isnan(p_durations_real)]

print(f"===== Thời gian sóng P thực tế =====")
print(f"Số lượng N: {len(p_durations_real_clean)}")
print(f"Giá trị nhỏ nhất (min): {np.min(p_durations_real_clean)*1000:.2f} ms")
print(f"Giá trị lớn nhất (max): {np.max(p_durations_real_clean)*1000:.2f} ms")
print(f"Trung bình (mean): {np.mean(p_durations_real_clean)*1000:.2f} ms")
print()

# ===== Vẽ biểu đồ P_start và P_end =====
p_start_display = [int(p) for p in p_start_points if not np.isnan(p) and start <= p < end]
p_end_display = [int(p) for p in p_end_points if not np.isnan(p) and start <= p < end]

plt.figure(figsize=(15,4))
plt.plot(time_axis, bpass[start:end], label='Bandpassed Signal')

# Vẽ điểm bắt đầu và kết thúc sóng P
plt.scatter(np.array(p_start_display)/fs, bpass[p_start_display], color='blue', marker='v', label='P start')
plt.scatter(np.array(p_end_display)/fs, bpass[p_end_display], color='orange', marker='^', label='P end')

#plt.title('P wave Start and End Points (5-10s)')
plt.xlabel('Time (s)',fontsize=15)
plt.ylabel('Amplitude',fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.grid(True)
plt.show()







#CẮT VÀ HẠ MẪU CHU KỲ
# Cắt chu kỳ ECG 500 mẫu quanh mỗi đỉnh R
cutter = ECGCycleCutter(signal=bpass, r_peaks=r_peaks, fs=500)
ecg_cycles, valid_r_peaks = cutter.extract_cycles()

# Hạ mẫu các chu kỳ đã cắt từ 500Hz xuống 360Hz
cutter.downsample_all()
cycles_360Hz = cutter.cycles_360Hz

# Vẽ 1 chu kỳ ban đầu (500Hz)
plt.figure(figsize=(4, 4))
plt.plot(np.arange(len(ecg_cycles[1])) / 500, ecg_cycles[5], label='500Hz')
#plt.title("Một chu kỳ ECG gốc (500Hz)")
plt.xlabel("Time (s)",fontsize=15)
plt.ylabel("Amplitude",fontsize=15)
plt.grid(True)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()

# Vẽ chu kỳ tương ứng đã hạ mẫu xuống 360Hz
plt.figure(figsize=(4, 4))
time_axis = np.arange(len(cycles_360Hz[1])) / 360  # trục thời gian 360Hz
plt.plot(time_axis, cycles_360Hz[1], color='orange', label='360Hz')
#plt.title("Chu kỳ ECG sau khi hạ mẫu xuống 360Hz")
plt.xlabel("Time (s)",fontsize=15)
plt.ylabel("Amplitude",fontsize=15)
plt.grid(True)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()


plt.figure(figsize=(6, 6))

# Trục thời gian 500Hz
time_500Hz = np.arange(len(ecg_cycles[1])) / 500
plt.plot(time_500Hz, ecg_cycles[1], label='500Hz')

# Trục thời gian 360Hz
time_360Hz = np.arange(len(cycles_360Hz[1])) / 360
plt.plot(time_360Hz, cycles_360Hz[1], color='orange', label='360Hz')

plt.title("So sánh chu kỳ ECG 500Hz và 360Hz")
plt.xlabel("Time (s)",fontsize=15)
plt.ylabel("Amplitude",fontsize=15)
plt.grid(True)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.legend(fontsize=15)
plt.show()



