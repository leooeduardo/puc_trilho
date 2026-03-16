#include <Arduino.h>

// ========== ENCODER INDUSTRIAL E6B2 ==========
#define E6B2_PHA 18
#define E6B2_PHB 19
volatile long e6b2_pos = 0;
int last_e6b2_a = 0;

// ========== ENCODER ROTATIVO KY-040 ==========
#define KY040_CLK 25
#define KY040_DT  33
#define KY040_SW  32
volatile long ky040_pos = 0;

// Variáveis para decodificação precisa do KY-040 (State Machine)
volatile uint8_t ky040_state = 0;
// Tabela de transição de estados para encoder quadratura (tende a ignorar ruído de bounce)
const int8_t ky040_table[] = {0,1,-1,0,-1,0,0,1,1,0,0,-1,0,-1,1,0};

// Botão KY-040 (Debouncing ainda mais estrito via loop de contagem)
volatile bool ky040_btn_event = false;
volatile unsigned long last_ky_btn_time = 0;
const unsigned long KY_DEBOUNCE_MS = 250; // Aumentado para 250ms (evita cliques acidentais múltiplos)

// ========== FIM DE CURSO (ZERO SENSOR) ==========
// Sugerindo pino 27 (GPIO livre e seguro para input)
#define LIMIT_SWITCH_PIN 27
volatile bool limit_switch_triggered = false;
volatile unsigned long last_limit_time = 0;
const unsigned long LIMIT_DEBOUNCE_MS = 100;

// Flag extra para ZERAGEM VIA SERIAL/UI
volatile bool serial_zero_requested = false;

// ==============================================

// ISR Encoder Industrial
void IRAM_ATTR isr_e6b2() {
  int a = digitalRead(E6B2_PHA);
  int b = digitalRead(E6B2_PHB);
  
  if (a != last_e6b2_a) {
    if (a != b) {
      e6b2_pos--; // Invertido se necessário dependendo do referencial
    } else {
      e6b2_pos++;
    }
    last_e6b2_a = a;
  }
}

// ISR Rotary KY-040
void IRAM_ATTR isr_ky040() {
  ky040_state = (ky040_state << 2) | (digitalRead(KY040_DT) << 1) | digitalRead(KY040_CLK);
  int8_t movement = ky040_table[ky040_state & 0x0F];
  if (movement != 0) {
    ky040_pos += movement;
  }
}

// ISR Botão KY-040
void IRAM_ATTR isr_ky040_btn() {
  unsigned long now = millis();
  if (now - last_ky_btn_time > KY_DEBOUNCE_MS) {
    // Algoritmo extra para bounces severos (Hardware ruim)
    // Se ainda for LOW depois de dar a interrupção FALLING, confia no clique.
    if (digitalRead(KY040_SW) == LOW) { 
      ky040_btn_event = true;
      last_ky_btn_time = now;
    }
  }
}

// ISR Fim de Curso (Zerar Encoder Industrial Fisico)
void IRAM_ATTR isr_limit_switch() {
  unsigned long now = millis();
  if (now - last_limit_time > LIMIT_DEBOUNCE_MS) {
    if (digitalRead(LIMIT_SWITCH_PIN) == LOW) { // Assume fim de curso fecha pro GND (PULLUP)
      e6b2_pos = 0;
      limit_switch_triggered = true;
      last_limit_time = now;
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(E6B2_PHA, INPUT_PULLUP);
  pinMode(E6B2_PHB, INPUT_PULLUP);
  
  pinMode(KY040_CLK, INPUT_PULLUP);
  pinMode(KY040_DT, INPUT_PULLUP);
  // Algumas placas KY-040 tem resistores de pull-up na própria placa, outras não! 
  // O INPUT_PULLUP garante que pinos que "flutuariam" fiquem 3.3V estáveis
  pinMode(KY040_SW, INPUT_PULLUP); 
  
  pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
  
  last_e6b2_a = digitalRead(E6B2_PHA);
  ky040_state = (digitalRead(KY040_DT) << 1) | digitalRead(KY040_CLK);
  
  attachInterrupt(digitalPinToInterrupt(E6B2_PHA), isr_e6b2, CHANGE);
  
  attachInterrupt(digitalPinToInterrupt(KY040_CLK), isr_ky040, CHANGE);
  attachInterrupt(digitalPinToInterrupt(KY040_DT),  isr_ky040, CHANGE);
  
  attachInterrupt(digitalPinToInterrupt(KY040_SW), isr_ky040_btn, FALLING);
  
  attachInterrupt(digitalPinToInterrupt(LIMIT_SWITCH_PIN), isr_limit_switch, FALLING);
  
  Serial.println("{\"msg\": \"Firmware v3 Iniciado - Comandos Seriais Aceitos\"}");
}

void loop() {
  
  // LER COMANDOS VIA SERIAL limpando TODO o buffer pendente
  while (Serial.available() > 0) {
    int cmd = Serial.read();
    
    // Ecoa o byte recebido para debug (vai aparecer no log da pagina)
    Serial.print("{\"dbg\": \"recv_byte:\", \"val\": ");
    Serial.print(cmd);
    Serial.println("}");
    
    // 82 = 'R', 114 = 'r' em ASCII
    if (cmd == 82 || cmd == 114) {
      noInterrupts();
      e6b2_pos = 0;
      limit_switch_triggered = true;
      interrupts();
      Serial.println("{\"msg\": \"Comando R processado!\"}" );
    }
  }

  // Cópia das vars e checagem de zero via software
  noInterrupts();
  long current_e6b2 = e6b2_pos;
  long current_ky040 = ky040_pos / 4; 
  bool current_ky_btn = ky040_btn_event;
  ky040_btn_event = false; 
  bool current_limit = limit_switch_triggered;
  limit_switch_triggered = false;
  
  interrupts();
  
  // Monta o JSON para visualização
  Serial.print("{\"e6b2\": ");
  Serial.print(current_e6b2);
  Serial.print(", \"ky040\": ");
  Serial.print(current_ky040);
  Serial.print(", \"btn\": ");
  Serial.print(current_ky_btn ? "true" : "false");
  Serial.print(", \"lim_sw\": ");
  Serial.print(current_limit ? "true" : "false");
  Serial.println("}");
  
  delay(50); // Baixei pra 50ms (20fps) para UI mais fluida e captar botões rápidos
}
