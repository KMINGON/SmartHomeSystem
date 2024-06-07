#include <WiFi.h>

 const char* ssid = "mingon";
 const char* password = "123456780";

int flame = 36; // ESP32의 아날로그 핀
int LED = 13; // ESP32의 디지털 핀
WiFiServer server(8080);

void setup() {
  Serial.begin(230400);
  pinMode(flame, INPUT);
  pinMode(LED, OUTPUT);

  // WiFi 연결
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  server.begin();

  // IP 주소 출력
  Serial.println(WiFi.localIP());
}

void loop() {
  int val = analogRead(flame);
  Serial.print("flame_sensor : ");
  Serial.println(val);

  if (val > 3000) {
    digitalWrite(LED, HIGH);
    Serial.println("FIRE!!!!");
  } else {
    digitalWrite(LED, LOW);
    Serial.println("NO FIRE");
  }

  // 클라이언트 연결 처리
  WiFiClient client = server.available();
  if (client) {
    Serial.println("New client");
    String currentLine = "";
    String webString = "";

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        Serial.write(c);
        if (c == '\n') {
          if (currentLine.length() == 0) {
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:application/json");
            client.println();
            client.print(webString);
            client.println();
            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }

        if (currentLine.endsWith("GET /fireevents")) {
          if (val > 3000) {
            webString = "{\"status\": \"FIRE\"}";
          } else {
            webString = "{\"status\": \"NO FIRE\"}";
          }
        }
      }
    }
    delay(1);
    client.stop();
    Serial.println("client disconnected");
  }
  delay(400);
}
