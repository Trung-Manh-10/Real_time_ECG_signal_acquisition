# REAL-TIME ECG SIGNAL ACQUISITION WITH MODULE AD8232 - COURSE PROJECT

A real-time ECG signal acquisition and processing system developed using the AD8232 ECG sensor module and ESP32.
The project focuses on acquiring ECG signals in real time, applying digital signal processing techniques,
and evaluating the quality of the acquired signals for academic research and learning purposes.

---
Citation:
You can check the document file there: 
```
https://docs.google.com/document/d/1ZuWx7JVmP6lc3u8-919ulYQq1VScYVbT/edit?usp=sharing&ouid=100423899415976353201&rtpof=true&sd=true
```
---
Description:
The system acquires ECG signals using the AD8232 module and processes the signals on an ESP32 microcontroller.
All firmware and signal-processing algorithms are organized in the Code_MCU folder.

The main processing pipeline includes:

Real-time ECG signal acquisition using the AD8232
ADC signal conversion and preprocessing
Low-pass and high-pass filtering for noise reduction
Data logging to an SD card
Real-time task management using FreeRTOS
ECG signal visualization and evaluation
The firmware is divided into multiple FreeRTOS tasks to improve task management and maintain reliable real-time signal acquisition.

<p align="center">
  <img width="1010" height="260" alt="image" src="https://github.com/user-attachments/assets/34f44fa7-3eb4-4d35-b4fe-57227f27b72d" />
  <br>
  <em>ECG Signal Acquisition Result</em>
</p>

---
After data acquisition, the recorded ECG signals are processed using the Pan-Tompkins algorithm for QRS complex and R-peak detection.

The processed signals are then evaluated using data collected from four volunteers, with a total of 12 ECG recordings, 
to assess the performance and reliability of the developed acquisition system for educational and research-oriented applications.

<p align="center">
  <img src="https://github.com/user-attachments/assets/32983188-6079-4de4-9673-7ee873ffd5d7" width="756">
</p>

<p align="center">
  <img width="760" height="260" alt="image" src="https://github.com/user-attachments/assets/b3593708-8a7f-4214-bc78-828d4ba73216" />
  <br>
  <em>ECG Signal Process System</em>
</p>

---
Technologies & Tools  
ESP32  
AD8232 ECG Sensor  
C/C++ – Arduino  
FreeRTOS  
SD Card  
Digital Signal Processing  
Pan-Tompkins Algorithm  




