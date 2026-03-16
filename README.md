# PUC Trilho — Sistema de Monitoramento de Encoders com ESP32

Sistema embarcado para leitura de encoders industriais e rotativos com visualização em tempo real, desenvolvido para o projeto de trilho da PUC.

---

## 🧰 Hardware

| Componente | Modelo | Pinos ESP32 |
|---|---|---|
| ESP32 | WROOM-32 | — |
| Encoder Industrial | E6B2-CWZ3E | GPIO 18 (Phase A), GPIO 19 (Phase B) |
| Encoder Rotativo | KY-040 | GPIO 25 (CLK), GPIO 33 (DT), GPIO 32 (SW/Button) |
| Chave Fim de Curso | — | GPIO 27 |

> Todos os pinos de entrada usam `INPUT_PULLUP` interno do ESP32.

### Esquema de Ligação

```
ESP32 WROOM-32
│
├── GPIO 18 ──── E6B2 Phase A
├── GPIO 19 ──── E6B2 Phase B
│
├── GPIO 25 ──── KY-040 CLK
├── GPIO 33 ──── KY-040 DT
├── GPIO 32 ──── KY-040 SW (Botão)
│
└── GPIO 27 ──── Fim de Curso (fecha pra GND)
```

---

## 📁 Estrutura do Projeto

```
puc_trilho/
├── esp32_firmware/
│   └── esp32_firmware.ino    # Firmware Arduino para ESP32
├── viewer.py                 # Visualizador Python (recomendado)
├── index.html                # Visualizador Web (Chrome/Edge/Opera)
└── README.md
```

---

## 🔧 Firmware (esp32_firmware.ino)

### Funcionalidades

- **Encoder Industrial E6B2**: leitura por interrupções (`CHANGE`) nas fases A e B — decodificação quadratura completa
- **Encoder Rotativo KY-040**: leitura por **State Machine de quadratura** (imune a ruído de bounce mecânico)
- **Botão KY-040**: debounce de 250ms para eliminar falsos positivos
- **Fim de Curso**: interrupção `FALLING` no GPIO 27 que zera a posição do encoder industrial
- **Reset via Serial**: envia o caractere `R` (ASCII 82) pela serial para zerar o encoder industrial via software
- **Saída JSON**: dados enviados a 20fps pela serial em formato JSON

### Formato de Saída Serial

```json
{"e6b2": -1523, "ky040": 7, "btn": false, "lim_sw": false}
```

| Campo | Descrição |
|---|---|
| `e6b2` | Posição absoluta do encoder industrial (pulsos) |
| `ky040` | Posição do encoder rotativo |
| `btn` | `true` por 1 frame quando o botão KY-040 é pressionado |
| `lim_sw` | `true` por 1 frame quando o fim de curso é acionado |

### Como gravar

```bash
# Compilar
arduino-cli compile --fqbn esp32:esp32:esp32 esp32_firmware/

# Gravar (ajuste a porta)
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32 esp32_firmware/
```

### Requisito: Variável de baud rate
```
Serial: 115200 baud
```

---

## 🖥️ Visualizador Python (Recomendado)

Interface gráfica tkinter com visualização em tempo real e botão de reset.

### Dependências

```bash
pip install pyserial
```

### Uso

```bash
python viewer.py
```

1. Digite a porta serial (ex: `COM3`) e clique **Conectar**
2. Aguarde ~3 segundos para a ESP32 iniciar
3. Gire os encoders para ver os valores em tempo real
4. Clique **Zerar Agora (R)** ou pressione a tecla `R` para zerar o encoder industrial

### Screenshot

| Elemento | Descrição |
|---|---|
| **Encoder Industrial** | Valor em pulsos (azul) |
| **Fim de Curso** | Indicador vermelho ao acionar o switch |
| **Encoder Rotativo** | Valor em rosa |
| **Botão KY-040** | Pisca verde ao ser pressionado |

---

## 🌐 Visualizador Web (index.html)

Interface Web via **Web Serial API** (Chrome / Edge / Opera — sem suporte Firefox/Safari).

> ⚠️ **Limitação conhecida**: o Chrome no Windows com driver CH340 bloqueia escrita simultânea à leitura, o que impede o botão de reset de funcionar pela interface Web. Use o **visualizador Python** para a funcionalidade completa.

### Uso

1. Abra `index.html` no Chrome/Edge
2. Clique em **Conectar via USB**
3. Selecione a porta COM da ESP32

---

## ⚙️ Protocolo Serial

### ESP32 → Computador
JSON a cada 50ms (20fps):
```json
{"e6b2": 0, "ky040": 0, "btn": false, "lim_sw": false}
```

### Computador → ESP32
| Comando | Ação |
|---|---|
| `R` (ASCII 82) | Zera o contador do encoder industrial (`e6b2_pos = 0`) |

---

## 🔍 Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| Nenhum valor lido ao conectar | ESP32 resetou via DTR | Aguarde os ~3s de boot |
| Encoder rotativo contando errado | Bounce mecânico do KY-040 | Já tratado pela State Machine no firmware |
| Botão com cliques fantasma | Hardware do KY-040 | Debounce de 250ms no firmware |
| Reset não funciona no browser | Limitação CH340 + Chrome Web Serial no Windows | Use o `viewer.py` |
| Porta ocupada ao gravar | Browser/viewer segurando a COM | Feche o visualizador antes de gravar |

---

## 📦 Dependências

### Firmware
- Arduino CLI
- Board: `esp32:esp32:esp32`

### Python
```
python >= 3.8
pyserial
tkinter (incluso no Python padrão)
```

---

## 👤 Autores

Projeto desenvolvido para o laboratório de sistemas embarcados — PUC.
