#include <Adafruit_NeoPXL8.h>

// Serial communication configuration
#define BAUD_RATE 9600
#define BUFFER_SIZE 32

// Neopixel configuration
#define NUM_LED 500
int8_t pins[8] = { 16, 17, 18, 19, 20, 21, 22, 23 };
Adafruit_NeoPXL8 strip(NUM_LED, pins, NEO_GRB);

char serialBuffer[BUFFER_SIZE];
uint8_t bufferIndex = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  strip.begin();
  strip.show();  // Initialize all pixels to 'off'
}

/*
どのLEDを何色にするのかをserialBufferからASCIIコードで受け取る
serialBufferには
セルの番号,カラーコードが送られてくる
100,#ffffff\n
*/
int processBuffer() {
  int my_index = atoi(strtok(serialBuffer, ",")); //serialBufferの文字列の,より前をindexに代入
  char* rgbString = strtok(NULL, "\n"); //28行目に呼び出したstrtokで引数として指定したserialBufferの残りからカラーコードを抜き出している。
  String rgbString1 = String(rgbString); //ASCIIコードから文字列に変換
  //抜き出した文字列がカラーコードかチェック
  if (rgbString1 && rgbString1.charAt(0) == '#' && rgbString1.length() == 7) {//serialBufferの文字列の,の後にも文字がある、抜き出した文字列の先頭文字が#である、抜き出した文字列の文字数が7文字である。
    //カラーコードからRGBの各値を取得
    int r = strtol(rgbString1.substring(1,3).c_str(), NULL, 16);
    int g = strtol(rgbString1.substring(3,5).c_str(), NULL, 16);
    int b = strtol(rgbString1.substring(5,7).c_str(), NULL, 16);
    setLEDColor(my_index, r, g, b); //セルの場所、RGBの値を引数にsetLEDColor関数を呼び出す
  } 
  // Clear the buffer
  memset(serialBuffer, 0, BUFFER_SIZE);
  bufferIndex = 0;
  return my_index;
}

void setLEDColor(int index, int red, int green, int blue) {
  Serial.print("Changing colors");
  

  if (index < strip.numPixels()) { //セルのインデックスがセルの数を上回っていない場合
    strip.setPixelColor(index, strip.Color(red, green, blue));
  }
}

void loop() {
  //シリアル通信で受け取ったデータが存在する間、ループが継続。ループ1回で1文字読み出してる。
  while (Serial.available()) { //シリアル通信の受信バッファ内のデータのバイト数を返す。データが無ければ0
    char c = Serial.read(); //シリアルポートから1文字をASCIIコードで読み出す。"1"を読み出すと49が格納される。
    if (c == '\n') { //1行読み出し終わると
      int my_index = processBuffer();
      if (my_index == 499){
        strip.show();
      } //processBufferを呼び出す。
    } 
    else if (bufferIndex < BUFFER_SIZE - 1) {
      serialBuffer[bufferIndex++] = c;
    }
  }
  //sleep_ms(200);
}

