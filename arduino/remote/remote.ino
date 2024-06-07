#include <WiFi.h>
#include <WiFiServer.h>
#include <ESP32Servo.h> // 서보 모터 라이브러리 추가

// Wi-Fi 네트워크 이름 및 비밀번호
const char* ssid = "mingon";
const char* password = "123456780";

#define LIGHT1_PIN 2
#define LIGHT2_PIN 13
#define DOORPIN 4 // 서보 모터 핀

Servo servo; // 서보 모터 객체 생성

WiFiServer server(80);

void setup() {
  // 시리얼 통신 시작
  Serial.begin(57600);

  // LED 핀 설정
  pinMode(LIGHT1_PIN, OUTPUT);
  digitalWrite(LIGHT1_PIN, LOW); // 기본적으로 LED를 끔

  pinMode(LIGHT2_PIN, OUTPUT);
  digitalWrite(LIGHT2_PIN, LOW); // 기본적으로 LED를 끔


  // 서보 모터 핀 설정
  servo.attach(DOORPIN);


  // Wi-Fi 연결 시도
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  server.begin(); // 서버 시작
}

void loop() {
  // Wi-Fi 연결 상태 확인
  if (WiFi.status() == WL_CONNECTED) {
    // Wi-Fi 연결 상태 유지 코드
  } else {
    Serial.println("WiFi not connected");
  }
  delay(1000);

  WiFiClient client = server.available(); // 새로운 클라이언트가 연결되었는지 확인
  if (client) {
    Serial.println("New Client");
    String currentLine = ""; // 현재 읽고 있는 줄을 저장할 문자열
    while (client.connected()) { // 클라이언트가 연결되어 있는 동안
      if (client.available()) { // 클라이언트로부터 데이터를 받을 수 있으면
        char c = client.read(); // 한 문자를 읽어들임
        Serial.write(c); // 시리얼 모니터에 출력
        if (c == '\n') { // 새로운 줄 문자를 받으면
          if (currentLine.length() != 0) { // 빈 줄이면 HTTP 요청 끝
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text");
            client.println();
            // LED 제어 명령 확인
            if (currentLine.indexOf("light1_on") >= 0) {
              digitalWrite(LIGHT1_PIN, HIGH); // LED 켜기
              client.println("0");
            } else if (currentLine.indexOf("light1_off") >= 0) {
              digitalWrite(LIGHT1_PIN, LOW); // LED 끄기
              client.println("1");

            } else if (currentLine.indexOf("light2_on") >= 0) {
              digitalWrite(LIGHT2_PIN, HIGH); // LED 켜기
              client.println("0");
            } else if (currentLine.indexOf("light2_off") >= 0) {
              digitalWrite(LIGHT2_PIN, LOW); // LED 끄기
              client.println("1");

            }else if (currentLine.indexOf("open_door") >= 0) {
              // 서보 모터를 90도 회전
              servo.write(90);
              client.println("0");
            }else if (currentLine.indexOf("close_door") >= 0) {
              // 서보 모터를 90도 회전
              servo.write(0);
              client.println("1");
            } else {
              client.print("{\"status\": \"unknown command\"}");
            }

            client.println();
            break;
          } else { // 새로운 줄이 아니면
            currentLine = ""; // 현재 줄 초기화
          }
        }else if (c != '\r') { // 캐리지 리턴이 아니면
          currentLine += c; // 현재 줄에 문자 추가
        }
      }
    }
    client.stop();
    Serial.println("Client Disconnected");
  }
}
