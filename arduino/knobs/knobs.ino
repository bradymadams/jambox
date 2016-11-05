/*
  This program controls an AD5206 potentiometer and 10 LEDs
  via instructions sent over UART.
  
  It takes the following instructions:
  
  P:V N0 N1 ..NN
  This instruction sets a pot value, V (0-255) to the given
  pot numbers (0-5)
  
  L:N
  This instruction turns on the first N LEDs and turns the
  remaining LEDs off.
  
  M:N
  This instruction pulls the Mute pin LOW (N=0) or HIGH (N=1)
  
  Z:N
  This instruction pulls the Stand By pin LOW (N=0) or HIGH (N=1)
  
  S:N
  This instruction writes the current value of the N (0-5) pot
*/


#include <SPI.h>

#define BAUD 9600

const int potSlaveSelectPin = 10;
const int openValue = 0;
const char termCharacter = '$';

int pots[] = {openValue, openValue, openValue, openValue, openValue, openValue};

const int nleds = 10;
const int led_pins[] = {2, 3, 4, 5, 6, 7, 8, 9, 14, 15};
const int mute_pin = 18;
const int sdby_pin = 19;

void setup() {
  pinMode(potSlaveSelectPin, OUTPUT);
  
  SPI.begin();
  Serial.begin(BAUD);
  
  for (int i = 0; i <= 5; i++) {
    digital_pot_write(i, openValue);
  }
  
  for (int iled = 0; iled < nleds; iled++) {
    pinMode(led_pins[iled], OUTPUT);
    digitalWrite(led_pins[iled], LOW);
  }
  
  pinMode(mute_pin, OUTPUT);
  digitalWrite(mute_pin, LOW);
  
  pinMode(sdby_pin, OUTPUT);
  digitalWrite(sdby_pin, LOW);
}

void loop() {  
  if (Serial.available() > 0) {
    String inst = Serial.readStringUntil(termCharacter);
    process_instruction(inst);
  }
}

void process_instruction(String inst) {   
  // We've received an instruction - let's attempt to parse it
  int icolon = inst.indexOf(':');
  
  if (icolon == -1) {
    // Not a valid instruction
    return;
  }
  
  char inst_t = inst.charAt(0);
  
  int nargs = 0;
  int ispace = 0;
  while (ispace >= 0) {
    nargs++;
    ispace = inst.indexOf(' ', ispace+1);
  }
  
  // Limit the number of arguments to 10
  if (nargs > 10) {
    nargs = 10;
  }
  
  int* inst_a = new int[nargs];    
  
  int iarg = 0;
  int i1, i2;
  i1 = icolon; // start at colon
  for (int iarg = 0; iarg < nargs; iarg++) {
    if (iarg == (nargs - 1)) {
      i2 = inst.length();
    } else {
      i2 = inst.indexOf(' ', i1+1);
    }
    
    String sarg = inst.substring(i1+1, i2);
    inst_a[iarg] = sarg.toInt();
    
    i1 = i2;
  }
  
  if (inst_t == 'P') {
    process_instruction_P(nargs, inst_a);
  } else if (inst_t == 'L') {
    process_instruction_L(nargs, inst_a);
  } else if (inst_t == 'M') {
    process_instruction_M(nargs, inst_a);
  } else if (inst_t == 'Z') {
    process_instruction_Z(nargs, inst_a);
  } else if (inst_t == 'S') {
    process_instruction_S(nargs, inst_a);
  }
  
  delete inst_a;
}

void process_instruction_P(int nargs, int* args) {
  for (int i = 1; i < nargs; i++) {
    if (args[i] <= 5) {
      digital_pot_write(args[i], args[0]);
      pots[args[i]] = args[0];
    }
  }
}

void process_instruction_L(int nargs, int* args) {
  for (int iled = 0; iled < args[0]; iled++) {
    digitalWrite(led_pins[iled], HIGH);
  }
  
  for (int iled = args[0]; iled < nleds; iled++) {
    digitalWrite(led_pins[iled], LOW);
  }
}

void process_instruction_M(int nargs, int* args) {
  if (nargs >= 1) {
      if (args[0] == 0) {
        digitalWrite(mute_pin, LOW);
      } else if (args[0] == 1) {
        digitalWrite(mute_pin, HIGH);
      }
  }
}

void process_instruction_Z(int nargs, int* args) {
  if (nargs >= 1) {
      if (args[0] == 0) {
        digitalWrite(sdby_pin, LOW);
      } else if (args[0] == 1) {
        digitalWrite(sdby_pin, HIGH);
      }
  }
}

void process_instruction_S(int nargs, int* args) {
  if (nargs >= 1) {
    int stat = pots[args[0]];
    Serial.println(stat, DEC);
  }
}

void digital_pot_write(int channel, int value) {
  // take the SS pin low to select the chip:
  digitalWrite(potSlaveSelectPin, LOW);
  //  send in the address and value via SPI:
  SPI.transfer(channel);
  SPI.transfer(value);
  // take the SS pin high to de-select the chip:
  digitalWrite(potSlaveSelectPin, HIGH);
}
