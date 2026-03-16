import serial
import time

try:
    print("Conectando na COM3...")
    ser = serial.Serial('COM3', 115200, timeout=0.1)
    time.sleep(2) # Espera a ESP32 resetar ao abrir a porta
    
    # Esvazia lixo de boot
    ser.read_all()

    for i in range(5):
        print("Enviando 'R' tentativa", i)
        ser.write(b'R\n')
        ser.flush()
        
        # Le por 1 segundo
        for _ in range(10):
            line = ser.readline()
            if line:
                print("Recebido:", line.decode('utf-8', errors='ignore').strip())
            time.sleep(0.1)
            
    ser.close()
    print("Concluído.")
except Exception as e:
    print(f"Erro: {e}")
