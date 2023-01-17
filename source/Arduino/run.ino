#include<Servo.h>
#include <LiquidCrystal.h>
#include <Adafruit_MLX90614.h>

Servo Myservo;
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

int t0;
int t1;
int i;
int start = 1;
int up = 0;
int maskflag = 0;
int people = 0;
int volume = 0;
int crowded = 0;
int pos;
int state;
const int buzzer = 7;
const int door = 8;
byte trigPin = A0;
byte trigPin2 = A2;
byte trigPin3 = A3;
const int echoPin = 10;
const int echoPin2 = 9;
const int led = 13;
const float offset = 3.00;
String pe_do_vo;
float distance;
float temperature;
char input[10];

void setup() {
  Serial.begin(9600);
  mlx.begin();
  lcd.begin (16,2);
  pinMode(buzzer, OUTPUT);
  pinMode(door, INPUT_PULLUP);
  pinMode(trigPin, OUTPUT);
  pinMode(trigPin2, OUTPUT);
  pinMode(trigPin3, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(echoPin2, INPUT);
  pinMode(led, OUTPUT);
  Myservo.attach(6);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  while(start==1){
  Serial.write(0);
  if (Serial.available()> 0){
    char *p;
    Serial.readStringUntil('\n').toCharArray(input,10);
    p = strtok(input, "_");
    people = atoi(p);
    p = strtok(NULL, "_");
    volume = atoi(p);
    Serial.write(1);
    start=0;}
  }
  
  if(volume<=people){crowded=1;}
  while(volume<=people){
    lcd.setCursor(0,0);
    lcd.print("Inside is crowded");
    exitgate();
  }
  if(people<=volume){crowded=0;}
  
  digitalWrite(LED_BUILTIN, HIGH);
  
  do{
    if(Serial.available()>0){
      char *p;
      Serial.readStringUntil('\n').toCharArray(input,10);
      p = strtok(input, "_");
      maskflag = atoi(p);
    }
    lcd.setCursor(0,0);
    lcd.print("Show your mask");
    exitgate();
  }while(maskflag==0);
  
  digitalWrite(LED_BUILTIN, LOW);
  
  while(maskflag==1){
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("Show your palm");
    distance = dist(trigPin, echoPin);
  
    while(distance > 2){
      lcd.setCursor(0,1);
      lcd.print("Bring closer");
      distance = dist(trigPin, echoPin);
      exitgate();
    }
  
    if(distance < 2){
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Temperature ");
      lcd.setCursor(0,1);
      temperature = meas();
      lcd.print(temperature);
      lcd.print(" C");
      delay(2000);
      lcd.clear();
    }
  
    state = digitalRead(door);
    if(temperature >= 36.00 && temperature <= 37.50){
      lcd.setCursor(0,0);
      lcd.print("Door opening");
      for(pos=0;pos<=180;pos++){Myservo.write(pos);}  
      digitalWrite(led, HIGH); 
      t0 = millis();
      lcd.clear();
      while(state == LOW){
        lcd.setCursor(0,0);
        lcd.print("Door opened");
        state = digitalRead(door);
        t1 = millis();
        if(t1-t0 > 20000){break;}
        exitgate();
        }
      if(state == HIGH){
        t0 = millis();
        distance = dist(trigPin2, echoPin2);
        while(distance >= 5){
          t1 = millis();
          distance = dist(trigPin2, echoPin2);
          if(distance <= 5){up=1;}else{up=0;}
          if(t1-t0 > 10000){break;}
          exitgate();
          }
         people = people + up;
       }
      while(state == HIGH){
         lcd.setCursor(0,0);
         lcd.print("Close the door");
         state = digitalRead(door);
         exitgate();
      }
      lcd.print("Door closing");
      for(pos=180;pos>=0;pos--){Myservo.write(pos);}   
      digitalWrite(led, LOW);
      while(Serial.available()>0 and maskflag==1){
        pe_do_vo = String(people)+"_1_"+String(crowded);
        Serial.println(pe_do_vo);
        char *p;
        Serial.readStringUntil('\n').toCharArray(input,10);
        p = strtok(input, "_");
        maskflag = atoi(p);
      }
    }
  lcd.clear();  
  lcd.setCursor(0,1);
  lcd.print("People ");
  lcd.print(people);
  delay(1000);
}
}

float meas() {
float temperature, temp;
float sum = 0;
int i = 0;

while (i < 500) {
    temp = mlx.readObjectTempC();
    sum += temp; 
    i++;
  }
  temperature = sum/500.0;
  temperature = temperature + offset;
  sum = 0;
  i = 0;
  tone(buzzer, 1000);
  delay(200);
  noTone(buzzer);
  return temperature;
}

float dist(byte trigPin, int echoPin) {
long duration;
float distance;
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  delay(1);
  distance = duration * 0.034 / 2;
  return distance;
}

float exitgate() {
  for(i=0;i<=1000;i++){
    distance = dist(trigPin3, echoPin2);
    if(distance <= 5){up=-1;}else{up=0;}
  }
  people = people + up;
  pe_do_vo = String(people)+"_0_"+String(crowded);
  Serial.println(pe_do_vo);
}
