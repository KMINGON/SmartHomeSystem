#include <WiFi.h>
#include <WiFiServer.h>
#include <WiFiClient.h>
#include <DHT.h>
#define DHTTYPE DHT22
#define DHTPIN 4

const char* ssid = "mingon";
const char* password = "123456780";
// Create an instance of the server
WiFiServer server(8080);
// Create an instance of DHT sensor
DHT dht(DHTPIN, DHTTYPE);
float temp, humi;
String webString="";
unsigned long previousMillis = 0;
const long interval = 1000;
void gettemphumi();


void setup() {
  Serial.begin(115200);
  delay(10);
  dht.begin();
  
  // Connect to WiFi network
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    }
 
 Serial.println("WiFi connected");
 // Start the server
 server.begin();
 
 // Print the IP address
 Serial.println(WiFi.localIP());
}

void loop() {
  line:
  // listen for incoming clients
  WiFiClient client = server.available();
  if (client) {
    Serial.println("New client");
    String currentLine = ""; // for holding incoming data
    webString="";
  while (client.connected()) {
    if(client.available()) {
      char c = client.read();
      Serial.write(c);
      if (c=='\n') {
        if (currentLine.length()==0) {
          client.println("HTTP/1.1 200 OK");
          client.println("Content-type:text/json");
          client.println();
          client.print(webString);
          client.println();
          break;
        }
        else {
          currentLine ="";
        }
      } else if (c!='\r') {
        currentLine += c;
      }

      if (currentLine.endsWith("GET /dhtevents")) {
        gettemphumi();
        webString="{\"temperature\": \"" +String(temp) + "\", \"humidity\": \"" + String(humi)+ "\" }";
        }
       }
      }
      delay(1);

      client.stop();
      Serial.println(webString);
      Serial.println("client disconnected");
    }
  }


void gettemphumi() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    humi = dht.readHumidity();
    temp = dht.readTemperature(false);
    if (isnan(humi) || isnan(temp)) {
      Serial.println("Failed to read dht sensor.");
      return;
    }
    Serial.print("Humidity: ");
    Serial.print(humi);
    Serial.print("% Temperature: ");
    Serial.print(temp);
    Serial.println("'c");
}
}
