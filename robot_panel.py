import socket
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

class RobotPanel:
    def __init__(self):
        try:
            self.serial = i2c(port=1, address=0x3C)
            self.device = ssd1306(self.serial)
            self.has_display = True
            
            try:
                self.font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
                self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
                self.font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
            except IOError:
                self.font_bold = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
                self.font_normal = ImageFont.load_default()

        except Exception as e:
            print(f"OLED tidak terdeteksi: {e}")
            self.has_display = False

    def get_ip_address(self):
        return "192.168.11.110:3000"

    def tampilkan_loading(self):
        if not self.has_display:
            return
        
        ip = self.get_ip_address()
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            
            # Kalkulasi posisi tengah secara otomatis (Center Alignment)
            w_title = draw.textlength("ACCESS IP", font=self.font_bold)
            w_boot = draw.textlength("[*] BOOTING...", font=self.font_bold)
            w_ip = draw.textlength(ip, font=self.font_normal)
            
            draw.text(((128 - w_title) / 2, 8), "ACCESS IP", fill="white", font=self.font_bold)
            draw.text(((128 - w_boot) / 2, 26), "[*] BOOTING...", fill="white", font=self.font_bold)
            draw.text(((128 - w_ip) / 2, 46), ip, fill="white", font=self.font_normal)
        
        time.sleep(1.5)

    def update_display(self, status_teks, ticks_l, ticks_r):
        if not self.has_display:
            return

        ip = self.get_ip_address()
        with canvas(self.device) as draw:
            # Baris 1: Header IP (Centered)
            ip_str = f"IP: {ip}"
            w_ip = draw.textlength(ip_str, font=self.font_bold)
            draw.text(((128 - w_ip) / 2, 2), ip_str, fill="white", font=self.font_bold)
            draw.line((4, 14, 124, 14), fill="white")
            
            # Baris 2: Status Trajectory (Centered)
            status_str = f"[{status_teks}]"
            w_status = draw.textlength(status_str, font=self.font_large)
            draw.text(((128 - w_status) / 2, 24), status_str, fill="white", font=self.font_large)
            
            # Baris 3: Footer Ticks Encoder (Centered)
            draw.line((4, 46, 124, 46), fill="white")
            ticks_str = f"L:{ticks_l}  R:{ticks_r}"
            w_ticks = draw.textlength(ticks_str, font=self.font_normal)
            draw.text(((128 - w_ticks) / 2, 50), ticks_str, fill="white", font=self.font_normal)
