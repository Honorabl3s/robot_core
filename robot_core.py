import asyncio
import websockets
import json
from gpiozero import Robot, DigitalInputDevice
from robot_panel import RobotPanel

# ==========================================
# 1. KONFIGURASI HARDWARE & OLED PANEL
# ==========================================
robot = Robot(left=(24, 23, 12), right=(6, 5, 13))

sensor_kiri = DigitalInputDevice(22, pull_up=True)
sensor_kanan = DigitalInputDevice(27, pull_up=True)

# Inisialisasi Layar OLED HUD Fisik
panel = RobotPanel()
panel.tampilkan_loading()  

# Memori Ticks Absolut (Bisa minus/plus)
ticks_kiri = 0
ticks_kanan = 0

# ==========================================
# 2. PENGATURAN KECEPATAN & STATUS
# ==========================================
MAX_SPEED = 0.7
RAMP_STEP = 1.0

current_kiri = 0.0
current_kanan = 0.0

current_status_text = "STANDBY"

# --- LOGIKA TRIGGER ENCODER (SOFTWARE ODOMETRY) ---
def hitung_kiri():
    global ticks_kiri
    if current_kiri < 0:
        ticks_kiri -= 1
    else:
        ticks_kiri += 1

def hitung_kanan():
    global ticks_kanan
    if current_kanan < 0:
        ticks_kanan -= 1
    else:
        ticks_kanan += 1

sensor_kiri.when_activated = hitung_kiri
sensor_kanan.when_activated = hitung_kanan

def smooth_step(current, target, step):
    if current < target:
        return min(current + step, target)
    elif current > target:
        return max(current - step, target)
    return current

def hitung_kecepatan_motor(x, throttle_input):
    global current_kiri, current_kanan, current_status_text

    throttle = -throttle_input * MAX_SPEED
    turn = -x * MAX_SPEED

    if abs(throttle) > 0.05:  
        turn = turn * 0.5

    target_kiri = throttle + turn
    target_kanan = throttle - turn

    max_mag = max(abs(target_kiri), abs(target_kanan))
    if max_mag > MAX_SPEED:
        target_kiri = (target_kiri / max_mag) * MAX_SPEED
        target_kanan = (target_kanan / max_mag) * MAX_SPEED

    current_kiri = smooth_step(current_kiri, target_kiri, RAMP_STEP)
    current_kanan = smooth_step(current_kanan, target_kanan, RAMP_STEP)

    robot.value = (current_kiri, current_kanan)

    if current_kiri == 0 and current_kanan == 0:
        current_status_text = "STANDBY"
    elif current_kiri > 0 and current_kanan > 0:
        current_status_text = "MUNDUR"
    elif current_kiri < 0 and current_kanan < 0:
        current_status_text = "MAJU"
    else:
        current_status_text = "BELOK"

# ==========================================
# 3. SERVER KOMUNIKASI (WEBSOCKET)
# ==========================================
async def terima_perintah(websocket):
    global current_kiri, current_kanan, current_status_text
    print("🚀 GCS Terhubung! Siap menerima komando.")
    
    async def kirim_telemetri():
        try:
            while True:
                panel.update_display(current_status_text, ticks_kiri, ticks_kanan)
                
                telemetri = {
                    "ticks_l": ticks_kiri,
                    "ticks_r": ticks_kanan
                }
                await websocket.send(json.dumps(telemetri))
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    task_telemetri = asyncio.create_task(kirim_telemetri())

    try:
        async for pesan in websocket:
            data = json.loads(pesan)
            x = data.get('x', 0.0)
            y = data.get('y', 0.0)
            
            hitung_kecepatan_motor(x, y)

    except websockets.exceptions.ConnectionClosed:
        print("🔴 Koneksi Terputus.")
    finally:
        task_telemetri.cancel()
        robot.stop()
        current_kiri = 0.0
        current_kanan = 0.0
        current_status_text = "STANDBY"
        panel.update_display(current_status_text, ticks_kiri, ticks_kanan)

async def main():
    print("🤖 Sistem Aktif (Directional Odometry & OLED HUD).")

    async with websockets.serve(terima_perintah, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        robot.stop()
        panel.update_display("MATI", ticks_kiri, ticks_kanan)
        print("\nProgram dimatikan.")
