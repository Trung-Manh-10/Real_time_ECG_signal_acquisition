#include <Arduino.h>
#include "ESP32TimerInterrupt.h"
#include <SPI.h>
#include <SD.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

#define SD_CS 5  // Chân CS cho module SD

volatile bool isRecordingFiltered = false;
volatile bool isRecordingRaw = false;

int filteredFileIndex = 0;
int rawFileIndex = 0;

File filteredFile;
File rawFile;

QueueHandle_t rawQueue;
QueueHandle_t ecgQueue;

typedef struct {
  unsigned long timestamp;
  double rawValue;
} RawSample;

typedef struct {
  unsigned long timestamp;
  double ecgValue;
} ECGSample;

const int adcPin = 32;
const int sampleIntervalMicros = 2000; // 500Hz sampling

ESP32TimerInterrupt Itimer(0);

const double Gain = 100.0;
const double Vref = 3.3;

// Filter coefficients và trạng thái
double a0_lp, a1_lp, a2_lp, a3_lp;
double b0_lp, b1_lp, b2_lp, b3_lp, b4_lp;
double a0_hp, a1_hp, a2_hp, a3_hp;
double b0_hp, b1_hp, b2_hp, b3_hp, b4_hp;

double x_lp[5] = {0};
double y_lp[4] = {0};
double x_hp[5] = {0};
double y_hp[4] = {0};

// Thời gian bắt đầu ghi dữ liệu
unsigned long filteredStartTime = 0;
unsigned long rawStartTime = 0;
const unsigned long maxRecordDuration = 120000; // 2p

// === Hàm tính hệ số Low-Pass Filter ===22
void calculateLowPassCoefficients(double f0_lp, double fs) {
  double alpha[] = {1.0, 2.6231, 3.4142, 2.6231, 1.0};
  double omega0 = 2.0 * PI * f0_lp;
  double dt = 1.0 / fs;
  double beta = omega0 * dt;

  double betaSq = beta * beta;
  double betaCube = betaSq * beta;
  double betaQuad = betaCube * beta;

  double D = (betaQuad * alpha[0]) + (2.0 * betaCube * alpha[1]) +
             (4.0 * betaSq * alpha[2]) + (8.0 * beta * alpha[3]) +
             (16.0 * alpha[4]);

  b0_lp = betaQuad / D;
  b1_lp = 4.0 * b0_lp;
  b2_lp = 6.0 * b0_lp;
  b3_lp = 4.0 * b0_lp;
  b4_lp = b0_lp;

  a0_lp = (4.0 * alpha[0] * betaQuad + 4.0 * alpha[1] * betaCube -
           16.0 * alpha[3] * beta - 64.0 * alpha[4]) / D;
  a1_lp = (6.0 * alpha[0] * betaQuad - 8.0 * alpha[2] * betaSq + 96.0 * alpha[4]) / D;
  a2_lp = (4.0 * alpha[0] * betaQuad - 4.0 * alpha[1] * betaCube +
           16.0 * alpha[3] * beta - 64.0 * alpha[4]) / D;
  a3_lp = (alpha[0] * betaQuad - 2.0 * alpha[1] * betaCube + 4.0 * alpha[2] * betaSq -
           8.0 * alpha[3] * beta + 16.0 * alpha[4]) / D;
}

// === Hàm lọc Low-Pass ===
double applyFilter(double rawInput) {
  x_lp[4] = x_lp[3];
  x_lp[3] = x_lp[2];
  x_lp[2] = x_lp[1];
  x_lp[1] = x_lp[0];
  x_lp[0] = rawInput;

  double filteredValue = b0_lp * x_lp[0] + b1_lp * x_lp[1] + b2_lp * x_lp[2] + b3_lp * x_lp[3] + b4_lp * x_lp[4] -
                         (a0_lp * y_lp[0] + a1_lp * y_lp[1] + a2_lp * y_lp[2] + a3_lp * y_lp[3]);

  y_lp[3] = y_lp[2];
  y_lp[2] = y_lp[1];
  y_lp[1] = y_lp[0];
  y_lp[0] = filteredValue;

  return filteredValue;
}

// === Hàm tính hệ số High-Pass Filter ===
void calculateHighPassCoefficients(double f0_hp, double fs) {
  double alpha[] = {1.0, 2.6231, 3.4142, 2.6231, 1.0};
  double omega0 = 2.0 * PI * f0_hp;
  double dt = 1.0 / fs;
  double beta = omega0 * dt;

  double betaSq = beta * beta;
  double betaCube = betaSq * beta;
  double betaQuad = betaCube * beta;

  double D = (betaQuad * alpha[0]) + (2.0 * betaCube * alpha[1]) +
             (4.0 * betaSq * alpha[2]) + (8.0 * beta * alpha[3]) +
             (16.0 * alpha[4]);

  b0_hp = 16.0 / D;
  b1_hp = -64.0 / D;
  b2_hp = 96.0 / D;
  b3_hp = -64.0 / D;
  b4_hp = 16.0 / D;

  a0_hp = (4.0 * alpha[0] * betaQuad + 4.0 * alpha[1] * betaCube -
           16.0 * alpha[3] * beta - 64.0 * alpha[4]) / D;
  a1_hp = (6.0 * alpha[0] * betaQuad - 8.0 * alpha[2] * betaSq + 96.0 * alpha[4]) / D;
  a2_hp = (4.0 * alpha[0] * betaQuad - 4.0 * alpha[1] * betaCube +
           16.0 * alpha[3] * beta - 64.0 * alpha[4]) / D;
  a3_hp = (alpha[0] * betaQuad - 2.0 * alpha[1] * betaCube + 4.0 * alpha[2] * betaSq -
           8.0 * alpha[3] * beta + 16.0 * alpha[4]) / D;
}

// === Hàm lọc High-Pass ===
double applyHighPassFilter(double hp_filteredValue) {
  x_hp[4] = x_hp[3];
  x_hp[3] = x_hp[2];
  x_hp[2] = x_hp[1];
  x_hp[1] = x_hp[0];
  x_hp[0] = hp_filteredValue;

  double hpFilteredValue = b0_hp * x_hp[0] + b1_hp * x_hp[1] + b2_hp * x_hp[2] + b3_hp * x_hp[3] + b4_hp * x_hp[4] -
                         (a0_hp * y_hp[0] + a1_hp * y_hp[1] + a2_hp * y_hp[2] + a3_hp * y_hp[3]);

  y_hp[3] = y_hp[2];
  y_hp[2] = y_hp[1];
  y_hp[1] = y_hp[0];
  y_hp[0] = hpFilteredValue;

  return hpFilteredValue;
}

// === ISR đọc ADC ===
// === Hàm ngắt đọc ADC ===
void IRAM_ATTR readADC_ISR() {
  int rawECG = analogRead(adcPin);
  double voltage = (rawECG * Vref) / 4095.0;
  double vin = voltage / Gain;
  double ecg_mV = vin * 1000.0;

  unsigned long timeStamp = millis();

  // Luôn chạy bộ lọc để giữ trạng thái cập nhật
  double filteredValue = applyFilter(ecg_mV);
  double hpFilteredValue = applyHighPassFilter(filteredValue);

  BaseType_t xHigherPriorityTaskWokenFiltered = pdFALSE;
  if (isRecordingFiltered) {
    ECGSample sample;
    sample.timestamp = timeStamp;
    sample.ecgValue = hpFilteredValue;
    // Cân nhắc kiểm tra giá trị trả về ở đây để phát hiện hàng đợi đầy
    xQueueSendFromISR(ecgQueue, &sample, &xHigherPriorityTaskWokenFiltered);
  }

  BaseType_t xHigherPriorityTaskWokenRaw = pdFALSE;
  if (isRecordingRaw) {
    RawSample rawSample;
    rawSample.timestamp = timeStamp;
    rawSample.rawValue = ecg_mV;
    // Cân nhắc kiểm tra giá trị trả về ở đây để phát hiện hàng đợi đầy
    xQueueSendFromISR(rawQueue, &rawSample, &xHigherPriorityTaskWokenRaw);
  }

  if (xHigherPriorityTaskWokenFiltered || xHigherPriorityTaskWokenRaw) {
    portYIELD_FROM_ISR();
  }
}



// === Task ghi dữ liệu ra thẻ SD ===
void sdWriteTask(void *pvParameters) {
  ECGSample ecgSample;
  RawSample rawSample;
  char buf[64];

  for (;;) {
        while (isRecordingFiltered && filteredFile && xQueueReceive(ecgQueue, &ecgSample, 0) == pdTRUE) {
          snprintf(buf, sizeof(buf), "%lu,%.5f\r\n", ecgSample.timestamp, ecgSample.ecgValue);
          filteredFile.print(buf);
        }

        while (isRecordingRaw && rawFile && xQueueReceive(rawQueue, &rawSample, 0) == pdTRUE) {
          snprintf(buf, sizeof(buf), "%lu,%.5f\r\n", rawSample.timestamp, rawSample.rawValue);
          rawFile.print(buf);
        }


    static unsigned long lastFlushTime = 0;
    if (millis() - lastFlushTime >= 2000) {
      if (filteredFile) filteredFile.flush();
      if (rawFile) rawFile.flush();
      lastFlushTime = millis();
    }

    vTaskDelay(pdMS_TO_TICKS(1));
  }
}

void clearECGQueue(QueueHandle_t queue) {
  ECGSample dummy;
  while (xQueueReceive(queue, &dummy, 0) == pdTRUE) {}
}

void clearRawQueue(QueueHandle_t queue) {
  RawSample dummy;
  while (xQueueReceive(queue, &dummy, 0) == pdTRUE) {}
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  if (!SD.begin(SD_CS)) {
    Serial.println("Lỗi: Không thể khởi động thẻ SD!");
    while (1) vTaskDelay(1000);
  }

  double fs = 500.0;
  double f0_lp = 40.0;
  double f0_hp = 0.5;

  calculateLowPassCoefficients(f0_lp, fs);
  calculateHighPassCoefficients(f0_hp, fs);

  ecgQueue = xQueueCreate(500, sizeof(ECGSample));
  rawQueue = xQueueCreate(500, sizeof(RawSample));

  xTaskCreate(sdWriteTask, "SD Write Task", 8192, NULL, 2, NULL);

  if (Itimer.attachInterruptInterval(sampleIntervalMicros, (esp32_timer_callback)readADC_ISR)) { // Gọi hàm ngắt đọc ADC
    Serial.println("Timer initialized successfully!");
  } else {
    Serial.println("Error: Could not initialize timer!");
  }

  //Serial.println("Nhấn '1' để bắt đầu/dừng ghi dữ liệu ECG đã lọc.");
  //Serial.println("Nhấn '2' để bắt đầu/dừng ghi dữ liệu raw.");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();

    if (c == '1') {
      // Chỉ ghi nếu chưa bắt đầu
      if (!isRecordingFiltered && !isRecordingRaw) {
        // Mở file filtered
        char filteredFilename[32];
        do {
          filteredFileIndex++;
          snprintf(filteredFilename, sizeof(filteredFilename), "/data_ecg_%d.txt", filteredFileIndex);
        } while (SD.exists(filteredFilename));
        filteredFile = SD.open(filteredFilename, FILE_WRITE);

        // Mở file raw
        char rawFilename[32];
        do {
          rawFileIndex++;
          snprintf(rawFilename, sizeof(rawFilename), "/raw_ecg_%d.txt", rawFileIndex);
        } while (SD.exists(rawFilename));
        rawFile = SD.open(rawFilename, FILE_WRITE);

        if (filteredFile && rawFile) {
          Serial.println("Bắt đầu ghi dữ liệu trong 2 phút.");
          Serial.print("→ Filtered file: "); Serial.println(filteredFilename);
          Serial.print("→ Raw file: "); Serial.println(rawFilename);

          // Ghi dòng tiêu đề CSV
          filteredFile.println("timestamp(ms),filtered(mV)");
          rawFile.println("timestamp(ms),raw(mV)");

          isRecordingFiltered = true;
          isRecordingRaw = true;
          filteredStartTime = rawStartTime = millis();
        } else {
          Serial.println("Lỗi mở file raw hoặc filtered!");
          isRecordingFiltered = false;
          isRecordingRaw = false;
        }
      } else {
        Serial.println("Đang ghi, vui lòng chờ đủ 2 phút để tự dừng.");
      }
    }
  }

  // Tự động dừng sau 2 phút
  if ((isRecordingFiltered || isRecordingRaw) && (millis() - filteredStartTime >= maxRecordDuration)) {
    Serial.println("Đã ghi đủ 2 phút. Dừng ghi dữ liệu.");

    isRecordingFiltered = false;
    isRecordingRaw = false;

    clearECGQueue(ecgQueue);
    clearRawQueue(rawQueue);

    if (filteredFile) {
      filteredFile.flush();
      filteredFile.close();
    }

    if (rawFile) {
      rawFile.flush();
      rawFile.close();
    }
  }
}
