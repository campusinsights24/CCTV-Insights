import os
import sys
import cv2
import time
import glob
import threading
import subprocess
import tkinter as tk
import numpy as np
import ctypes
from datetime import datetime

try:
    import win32api
    import win32con
    import pythoncom
    import win32com.client
except ImportError:
    print("CRITICAL: pywin32 library missing. Run: pip install pywin32")
    sys.exit(1)

class UIOverlay:
    """Handles the Borderless Terminal UI with unbreakable State Locks."""
    def __init__(self, dvr_engine):
        self.dvr = dvr_engine
        self.root = tk.Tk()
        self.setup_window()
        self.build_ui()

    def setup_window(self):
        # 1. UI TITLE MATCHES PYTHON FILE NAME
        self.app_name = self.dvr.app_name.upper()
        
        self.root.title(f"{self.app_name} - TERMINAL")
        
        start_width = 850
        start_height = 550
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        pos_x = (screen_width - start_width) // 2
        pos_y = (screen_height - start_height) // 2
        
        self.root.geometry(f"{start_width}x{start_height}+{pos_x}+{pos_y}")
        self.root.configure(bg="#050505")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True) 
        self.root.bind("<Map>", self.on_window_restore)

    def on_window_restore(self, event):
        self.root.overrideredirect(True)

    def minimize_app(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def close_app_attempt(self):
        if self.dvr.is_armed:
            self.status_var.set("[ ACTION BLOCKED: ENTER PIN TO DISARM & EXIT ]")
            self.status_label.config(fg="#FF0000")
            self.pin_entry.focus()
        else:
            self.force_hardware_shutdown()

    def drag_start(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def drag_motion(self, event):
        deltax = event.x - self.start_x
        deltay = event.y - self.start_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def resize_start(self, event):
        self.res_start_x = event.x_root
        self.res_start_y = event.y_root
        self.start_w = self.root.winfo_width()
        self.start_h = self.root.winfo_height()

    def resize_motion(self, event):
        new_w = max(self.start_w + (event.x_root - self.res_start_x), 750)
        new_h = max(self.start_h + (event.y_root - self.res_start_y), 500)
        self.root.geometry(f"{new_w}x{new_h}")

    def build_ui(self):
        title_bar = tk.Frame(self.root, bg="#0A0A0A", relief="raised", bd=0, highlightbackground="#00FF00", highlightthickness=1)
        title_bar.pack(side="top", fill="x")
        
        title_bar.bind("<ButtonPress-1>", self.drag_start)
        title_bar.bind("<B1-Motion>", self.drag_motion)

        tk.Label(title_bar, text=f" {self.app_name} - SYSTEM TERMINAL", font=("Consolas", 10), bg="#0A0A0A", fg="#00FF00").pack(side="left", padx=5)

        close_btn = tk.Button(title_bar, text=" X ", bg="#0A0A0A", fg="#00FF00", bd=0, font=("Consolas", 10, "bold"), command=self.close_app_attempt, cursor="hand2")
        close_btn.pack(side="right", padx=5, pady=2)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#FF0000", fg="#FFFFFF"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#0A0A0A", fg="#00FF00"))

        min_btn = tk.Button(title_bar, text=" - ", bg="#0A0A0A", fg="#00FF00", bd=0, font=("Consolas", 12, "bold"), command=self.minimize_app, cursor="hand2")
        min_btn.pack(side="right", padx=5, pady=2)
        min_btn.bind("<Enter>", lambda e: min_btn.config(bg="#00FF00", fg="#000000"))
        min_btn.bind("<Leave>", lambda e: min_btn.config(bg="#0A0A0A", fg="#00FF00"))

        outer_frame = tk.Frame(self.root, bg="#050505", highlightbackground="#00FF00", highlightthickness=2)
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)

        content_frame = tk.Frame(outer_frame, bg="#050505")
        content_frame.pack(fill="both", expand=True, padx=40, pady=20) 

        tk.Label(content_frame, text=f"{self.app_name}", font=("Consolas", 38, "bold"), fg="#00FF00", bg="#050505").pack(pady=(10, 0))
        tk.Label(content_frame, text="CAMPUS INSIGHTS", font=("Consolas", 18, "bold"), fg="#00CC00", bg="#050505").pack(pady=(0, 20))

        features = [
            "> UG/PG REGULAR/DISTANCE COURSES",
            "> NET/JRF PAPER 1/2 ALL NOTES AVAILABLE",
            "> HINDI/ENGLISH EXPLANATION FORMAT",
            "> VARIOUS SOFTWARE SOLUTIONS AVAILABLE"
        ]
        for f in features:
            tk.Label(content_frame, text=f, font=("Consolas", 12), fg="#00FF00", bg="#050505").pack(pady=4)

        tk.Label(content_frame, text="CONTACT TO PURCHASE: 7988407499", font=("Consolas", 15, "bold"), fg="#FFFFFF", bg="#050505").pack(pady=25)

        self.status_var = tk.StringVar(value="[ SYSTEM AWAITING CONFIGURATION : SET NEW PIN ]")
        self.status_label = tk.Label(content_frame, textvariable=self.status_var, font=("Consolas", 14, "bold"), fg="#F2A900", bg="#050505")
        self.status_label.pack(pady=5)

        pin_frame = tk.Frame(content_frame, bg="#050505")
        pin_frame.pack(pady=10)
        
        self.pin_prompt = tk.StringVar(value="ENTER NEW PIN:")
        tk.Label(pin_frame, textvariable=self.pin_prompt, font=("Consolas", 14), fg="#00FF00", bg="#050505").pack(side="left", padx=5)
        
        self.pin_var = tk.StringVar()
        self.pin_entry = tk.Entry(pin_frame, textvariable=self.pin_var, show="*", font=("Consolas", 14), bg="#000000", fg="#00FF00", insertbackground="#00FF00", width=12)
        self.pin_entry.pack(side="left", padx=5)

        self.btn_toggle = tk.Button(pin_frame, text="[ SHOW ]", font=("Consolas", 10), bg="#050505", fg="#00FF00", bd=1, relief="solid", cursor="hand2", command=self.toggle_pin)
        self.btn_toggle.pack(side="left", padx=5)

        self.root.bind('<Return>', self.process_pin_action)
        self.pin_entry.focus()

        resize_grip = tk.Label(outer_frame, text="◢", font=("Consolas", 14), bg="#050505", fg="#00FF00", cursor="sizing")
        resize_grip.place(relx=1.0, rely=1.0, anchor="se") 
        resize_grip.bind("<ButtonPress-1>", self.resize_start)
        resize_grip.bind("<B1-Motion>", self.resize_motion)

    def toggle_pin(self):
        if self.pin_entry.cget('show') == '':
            self.pin_entry.config(show='*')
            self.btn_toggle.config(text="[ SHOW ]")
        else:
            self.pin_entry.config(show='')
            self.btn_toggle.config(text="[ HIDE ]")

    def process_pin_action(self, event=None):
        current_input = self.pin_var.get()
        
        # 2. IRON-CLAD STATE LOCK (No accidental resets)
        if not self.dvr.is_armed:
            if len(current_input) >= 4:
                # ARMING PROCESS
                self.dvr.master_pin = current_input
                self.pin_entry.delete(0, tk.END)
                self.pin_prompt.set("TERMINATION PIN:")
                self.status_var.set("[ SYSTEM STATUS : ARMED & RECORDING ]")
                self.status_label.config(fg="#00FF00")
                self.dvr.arm_system() 
            else:
                self.pin_entry.delete(0, tk.END)
                self.status_var.set("[ ERROR: PIN MUST BE AT LEAST 4 DIGITS ]")
                self.status_label.config(fg="#FF0000")
        else:
            # DISARMING PROCESS (Only if correctly matched)
            if current_input == self.dvr.master_pin:
                self.status_var.set("[ SYSTEM STATUS : DISARMED ]")
                self.status_label.config(fg="#00FFFF")
                self.dvr.is_armed = False
                self.root.after(500, self.force_hardware_shutdown)
            else:
                self.pin_entry.delete(0, tk.END)
                self.status_var.set("[ ERROR: INVALID AUTHORIZATION PIN ]")
                self.status_label.config(fg="#FF0000")

    def force_hardware_shutdown(self):
        """Immediately destroys UI and terminates Python process to release Webcam instantly."""
        self.root.destroy()
        os._exit(0) 

    def run(self):
        self.root.mainloop()


class CCTVInsightsDVR:
    """Core Engine with Google Drive Auto-Locator and 10-Sec Threat Burst."""
    def __init__(self):
        self.is_armed = False 
        self.master_pin = None
        self.fps = 5.0
        self.chunk_duration = 60.0
        self.cap = None
        self.latest_frame = None 
        self.frame_lock = threading.Lock()
        
        # 3. PYTHON FILE NAME BECOMES FOLDER NAME
        self.app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        
        # 4. SMART GOOGLE DRIVE AUTO-LOCATOR
        possible_drive_paths = [r"G:\My Drive", r"D:\My Drive", r"E:\My Drive", r"F:\My Drive", r"C:\My Drive"]
        self.master_folder = None
        
        for path in possible_drive_paths:
            if os.path.exists(path):
                self.master_folder = os.path.join(path, self.app_name)
                break
                
        # Fallback to desktop if Google Drive is completely missing from the system
        if not self.master_folder:
            user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.master_folder = os.path.join(user_desktop, self.app_name)
            
        os.makedirs(self.master_folder, exist_ok=True)
        
        win32api.SetConsoleCtrlHandler(self._os_shutdown_handler, True)

    def arm_system(self):
        self.is_armed = True
        
        session_ts = datetime.now().strftime("Session_%d_%b_%A_%I-%M_%p")
        self.session_path = os.path.join(self.master_folder, session_ts)
        os.makedirs(self.session_path, exist_ok=True)
        
        self.intruder_path = os.path.join(self.session_path, "INTRUDER_SNAPSHOTS")
        os.makedirs(self.intruder_path, exist_ok=True)

        threading.Thread(target=self._network_sentinel_daemon, daemon=True).start()
        threading.Thread(target=self.core_dvr_engine, daemon=True).start()
        threading.Thread(target=self._hardware_activity_monitor, daemon=True).start()

    def _os_shutdown_handler(self, ctrl_type):
        if ctrl_type in (win32con.CTRL_SHUTDOWN_EVENT, win32con.CTRL_LOGOFF_EVENT):
            self._take_snapshot_burst()
            return True
        return False

    def _safe_image_write(self, path, frame):
        try:
            is_success, im_buf_arr = cv2.imencode(".jpg", frame)
            if is_success:
                im_buf_arr.tofile(path)
        except Exception:
            pass

    def _take_snapshot_burst(self):
        with self.frame_lock:
            if self.latest_frame is not None:
                for i in range(5):
                    ts = datetime.now().strftime("%I-%M-%S_%p")
                    filepath = os.path.join(self.intruder_path, f"Intruder_Shutdown_{ts}_{i}.jpg")
                    self._safe_image_write(filepath, self.latest_frame)
                    time.sleep(1.0)

    def _hardware_activity_monitor(self):
        pythoncom.CoInitialize() 

        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong)]

        power_status = SYSTEM_POWER_STATUS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power_status))
        last_power = power_status.ACLineStatus
        last_mouse = win32api.GetCursorPos()

        try:
            wmi = win32com.client.GetObject("winmgmts:")
            last_usb_count = len(wmi.ExecQuery("Select * from Win32_USBControllerDevice"))
            usb_tracking = True
        except:
            usb_tracking = False

        alert_end_time = 0
        loop_counter = 0

        while self.is_armed:
            triggered_now = False
            
            # Fast Mouse
            current_mouse = win32api.GetCursorPos()
            if abs(current_mouse[0] - last_mouse[0]) > 30 or abs(current_mouse[1] - last_mouse[1]) > 30:
                triggered_now = True
            last_mouse = current_mouse

            # Fast Keyboard
            if not triggered_now:
                for i in range(8, 256):
                    if win32api.GetAsyncKeyState(i) & 0x0001: 
                        triggered_now = True
                        break

            # Power/Charger
            if not triggered_now:
                ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power_status))
                if power_status.ACLineStatus != last_power:
                    triggered_now = True
                    last_power = power_status.ACLineStatus

            # USB Monitoring
            if not triggered_now and usb_tracking and loop_counter % 10 == 0:
                try:
                    current_usb_count = len(wmi.ExecQuery("Select * from Win32_USBControllerDevice"))
                    if current_usb_count != last_usb_count:
                        triggered_now = True
                        last_usb_count = current_usb_count
                except: pass

            # 5. EXACTLY 10-SECOND BURST RULE
            if triggered_now:
                alert_end_time = time.time() + 10.0 # Changed from 60.0 to 10.0

            if time.time() < alert_end_time:
                # Capture 1 photo per second during the 10-second alert window
                with self.frame_lock:
                    if self.latest_frame is not None:
                        ts = datetime.now().strftime("%I-%M-%S_%p_%d_%b_%A")
                        filename = os.path.join(self.intruder_path, f"Snap_{ts}.jpg")
                        self._safe_image_write(filename, self.latest_frame)
                time.sleep(1.0)
                loop_counter = 0
            else:
                time.sleep(0.1) 
                loop_counter += 1

    def execute_global_fifo_cleanup(self):
        try:
            MAX_CAPACITY = 12 * 1024 * 1024 * 1024 
            all_videos = glob.glob(os.path.join(self.master_folder, "**", "*.mp4"), recursive=True)
            all_videos.sort(key=os.path.getctime)
            total_size = sum(os.path.getsize(f) for f in all_videos)
            
            while total_size > MAX_CAPACITY and all_videos:
                oldest = all_videos.pop(0)
                try: os.remove(oldest)
                except OSError: break
        except Exception: pass

    def _network_sentinel_daemon(self):
        while self.is_armed:
            try:
                subprocess.run(["ping", "-n", "1", "8.8.8.8"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except: pass
            time.sleep(10)

    def core_dvr_engine(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        target_frames = int(self.chunk_duration * self.fps)
        
        while self.is_armed:
            # 6. EXACT REQUESTED VIDEO NAMING FORMAT
            file_ts = datetime.now().strftime("%I-%M_%p_%d_%b_%A")
            video_output = os.path.join(self.session_path, f"Insights_CCTV_{file_ts}.mp4")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(video_output, fourcc, self.fps, (640, 480))
            
            frames_processed = 0
            while frames_processed < target_frames and self.is_armed:
                frame_start = time.time()
                ret, frame = self.cap.read()
                
                with self.frame_lock:
                    if ret:
                        self.latest_frame = frame.copy()
                
                if ret: video_writer.write(frame)
                else: video_writer.write(np.zeros((480, 640, 3), dtype=np.uint8))
                    
                frames_processed += 1
                sleep_time = max(0, (1.0 / self.fps) - (time.time() - frame_start))
                time.sleep(sleep_time)
                
            video_writer.release()
            threading.Thread(target=self.execute_global_fifo_cleanup, daemon=True).start()

        if self.cap: self.cap.release()

if __name__ == "__main__":
    dvr = CCTVInsightsDVR()
    app = UIOverlay(dvr)
    app.run()