import customtkinter as ctk
import requests
import json
import subprocess
import sys
import os
import threading
import concurrent.futures
import ctypes
from ping3 import ping
from PIL import Image
from io import BytesIO

# Basic configuration
APP_NAME = "Steam Server Picker"
STEAM_CONFIG_URL = "https://api.steampowered.com/ISteamApps/GetSDRConfig/v1/?appid=730"
RULE_PREFIX = "SteamPicker-"
FLAG_API_URL = "https://flagcdn.com/w40/{code}.png"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        try:
            # Try to execute with admin rights
            res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            if res > 32: # Success
                os._exit(0) # Force immediate exit of the non-admin process
        except Exception:
            pass
    return False

class SteamServerPicker(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("1200x850")
        self.minsize(600, 500) # Reduced minimum size as requested

        # Set App Icon
        if os.path.exists("app_icon.ico"):
            self.iconbitmap("app_icon.ico")
        
        # Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Data
        self.servers = {}
        self.search_query = ""
        self.flag_images = {}
        self.server_rows = {}
        
        # Create a tiny transparent placeholder for initial rendering
        placeholder = Image.new('RGBA', (24, 16), (0, 0, 0, 0))
        self.placeholder_img = ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=(24, 16))
        
        self.regions = {
            "EUROPE": (["ams", "fra", "lhr", "mad", "par", "sto", "vie", "waw", "bud", "lux", "man", "mil", "mow", "sto2", "ham", "mrs", "mad2", "ath", "prg", "bru", "zrh"], "eu"),
            "NORTH AMERICA": (["atl", "ord", "dfw", "lax", "okc", "sea", "iad", "atl2", "ord2", "dfw2", "lax2", "sea2", "iad2", "tor", "mtl", "mex", "den"], "us"),
            "ASIA": (["hkg", "bom", "maa", "nrt", "icn", "sgp", "syd", "tpe", "can", "pvg", "tsn", "wuh", "hgh", "shat", "shau", "sha2", "hkg2", "tyo", "tyo2", "sel", "sel2", "sgp2", "syd2", "pek", "ctm", "ctt", "ctu", "pgm", "pgt", "pgu", "gnm", "gnt", "gnu", "shb", "pwg", "pwu", "pwj", "pww", "pwz", "tgdm", "tgdt", "tgdu", "seo"], "cn"),
            "OTHER": (["eze", "jnb", "lim", "scl", "gru", "dxb", "cpt", "bog", "qro"], "un")
        }

        self.city_to_country = {
            "ams": "nl", "fra": "de", "lhr": "gb", "mad": "es", "par": "fr", "sto": "se", "vie": "at", "waw": "pl",
            "atl": "us", "ord": "us", "dfw": "us", "lax": "us", "sea": "us", "iad": "us", "hkg": "hk", "bom": "in",
            "maa": "in", "nrt": "jp", "icn": "kr", "sgp": "sg", "syd": "au", "tpe": "tw", "can": "cn", "pvg": "cn",
            "tsn": "cn", "wuh": "cn", "hgh": "cn", "eze": "ar", "jnb": "za", "lim": "pe", "scl": "cl", "gru": "br",
            "dxb": "ae", "cpt": "za", "prg": "cz", "bud": "hu", "bru": "be", "zrh": "ch", "ath": "gr", "tor": "ca",
            "mtl": "ca", "mex": "mx", "pek": "cn", "ctm": "cn", "ctt": "cn", "ctu": "cn", "pgm": "cn", "pgt": "cn",
            "pgu": "cn", "gnm": "cn", "gnt": "cn", "gnu": "cn", "sha": "cn", "shb": "cn", "pwg": "cn", "pwu": "cn", 
            "pwj": "cn", "pww": "cn", "pwz": "cn", "tgd": "cn", "tyo": "jp", "sel": "kr", "seo": "kr", "sto2": "se"
        }
        
        self.active_preset = None
        self.ping_filter_min = 0
        self.ping_filter_max = 1000
        
        # Resize debouncing
        self._resize_timer = None
        self._last_width = 0
        self._last_height = 0
        
        self.setup_ui()
        
        # Bind resize event
        self.bind("<Configure>", self.on_window_resize)
        
        # Start prefetching flags
        self.prefetch_flags()
        
        # Start data loading immediately
        self.after(10, self.load_data_and_ping)

    def on_window_resize(self, event):
        # Only handle if it's the main window and size actually changed
        if event.widget == self:
            width = event.width
            height = event.height
            # Threshold to avoid triggering on tiny 1-2px fluctuations
            if abs(width - self._last_width) > 5 or abs(height - self._last_height) > 5:
                self._last_width = width
                self._last_height = height
                
                # If we are already timing, cancel it
                if self._resize_timer:
                    self.after_cancel(self._resize_timer)
                
                # AGGRESSIVE SMOOTHING: Hide the entire container during resize
                if hasattr(self, "main_container") and self.main_container.winfo_viewable():
                    self.main_container.grid_remove()
                
                # Longer timer (720ms) to ensure user actually stopped resizing
                self._resize_timer = self.after(720, self.finish_resize)

    def finish_resize(self):
        if hasattr(self, "main_container"):
            width = self.winfo_width()
            
            # Adaptive Layout Stage 1: Hide right panel
            if width < 950:
                if hasattr(self, "right_panel"):
                    self.right_panel.grid_remove()
                self.main_container.grid_columnconfigure(0, weight=1)
                self.main_container.grid_columnconfigure(1, weight=0)
            else:
                if hasattr(self, "right_panel"):
                    self.right_panel.grid(row=1, column=1, sticky="nsew")
                self.main_container.grid_columnconfigure(0, weight=3)
                self.main_container.grid_columnconfigure(1, weight=1)
            
            # Adaptive Layout Stage 2: Hide Ping column if extremely narrow
            if width < 650:
                if hasattr(self, "hdr_ping"): self.hdr_ping.grid_remove()
                self.table_header.grid_columnconfigure(1, minsize=0)
            else:
                if hasattr(self, "hdr_ping"): self.hdr_ping.grid(row=0, column=1)
                self.table_header.grid_columnconfigure(1, minsize=100)
            
            # Re-show the container
            self.main_container.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
            
            # Re-render servers to apply adaptive row changes
            self.render_servers()
            
        self._resize_timer = None
        self.update()

    def setup_ui(self):
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        self.main_container.grid_columnconfigure(0, weight=3)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # HEADER
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.title_label = ctk.CTkLabel(self.header_frame, text=APP_NAME, font=ctk.CTkFont(size=32, weight="bold"))
        self.title_label.pack(side="left")

        # LEFT PANEL
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="#1E1E1E", corner_radius=15)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 20))
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(3, weight=1)

        # Filter section
        self.filter_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.filter_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.filter_frame.columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="🔍 Filter servers...", height=45, fg_color="#2B2B2B", border_width=0)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Ping Range Filter
        self.ping_filter_frame = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.ping_filter_frame.grid(row=0, column=1)
        ctk.CTkLabel(self.ping_filter_frame, text="Ping Range:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        self.ping_min_entry = ctk.CTkEntry(self.ping_filter_frame, width=50, height=30, placeholder_text="0")
        self.ping_min_entry.pack(side="left")
        self.ping_min_entry.insert(0, "0")
        ctk.CTkLabel(self.ping_filter_frame, text="-").pack(side="left", padx=2)
        self.ping_max_entry = ctk.CTkEntry(self.ping_filter_frame, width=50, height=30, placeholder_text="999")
        self.ping_max_entry.pack(side="left")
        self.ping_max_entry.insert(0, "999")
        self.apply_ping_btn = ctk.CTkButton(self.ping_filter_frame, text="Apply", width=60, height=30, command=self.apply_ping_filter)
        self.apply_ping_btn.pack(side="left", padx=5)

        self.table_header = ctk.CTkFrame(self.left_panel, fg_color="#2B2B2B", height=50, corner_radius=0)
        self.table_header.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.table_header.grid_columnconfigure(0, weight=1)
        self.table_header.grid_columnconfigure(1, minsize=100)
        self.table_header.grid_columnconfigure(2, minsize=140)
        
        self.hdr_loc = ctk.CTkLabel(self.table_header, text="SERVER LOCATION", font=ctk.CTkFont(size=11, weight="bold"))
        self.hdr_loc.grid(row=0, column=0, padx=60, sticky="w")
        self.hdr_ping = ctk.CTkLabel(self.table_header, text="PING", font=ctk.CTkFont(size=11, weight="bold"))
        self.hdr_ping.grid(row=0, column=1)
        self.hdr_action = ctk.CTkLabel(self.table_header, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"))
        self.hdr_action.grid(row=0, column=2)

        self.scrollable_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent", corner_radius=0)
        self.scrollable_frame.grid(row=3, column=0, sticky="nsew")
        self.scrollable_frame.columnconfigure(0, weight=1)

        # RIGHT PANEL
        self.right_panel = ctk.CTkFrame(self.main_container, fg_color="#1E1E1E", corner_radius=15)
        self.right_panel.grid(row=1, column=1, sticky="nsew")

        ctk.CTkLabel(self.right_panel, text="QUICK PRESETS", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))
        self.preset_buttons = {}
        for region, (codes, flag_code) in self.regions.items():
            # Initialize with placeholder image so the button layout is ready
            btn = ctk.CTkButton(self.right_panel, text=f"   {region}", height=45, fg_color="#2B2B2B", 
                               image=self.placeholder_img, compound="left", anchor="w", 
                               command=lambda r=region: self.play_only_in(r))
            btn.pack(pady=5, padx=20, fill="x")
            self.preset_buttons[region] = btn

        self.main_action_btn = ctk.CTkButton(self.right_panel, text="BLOCK ALL", height=55, fg_color="#C0392B", hover_color="#962D22", font=ctk.CTkFont(size=14, weight="bold"), command=self.toggle_all_rules)
        self.main_action_btn.pack(side="bottom", pady=20, padx=20, fill="x")

        # ADMIN OVERLAY (MODERN)
        if not is_admin():
            self.overlay = ctk.CTkFrame(self, fg_color="#000000")
            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.overlay.lift()
            
            self.lock_box = ctk.CTkFrame(self.overlay, fg_color="#252525", corner_radius=20, border_width=2, border_color="#E67E22", width=450, height=350)
            self.lock_box.place(relx=0.5, rely=0.5, anchor="center")
            self.lock_box.pack_propagate(False)
            
            ctk.CTkLabel(self.lock_box, text="ADMIN RIGHTS REQUIRED", font=ctk.CTkFont(size=22, weight="bold"), text_color="#E67E22").pack(pady=(30, 5))
            
            self.info_text = ctk.CTkLabel(self.lock_box, text="Firewall modification requires elevation.", font=ctk.CTkFont(size=12), text_color="gray70")
            self.info_text.pack()

            self.help_icon = ctk.CTkLabel(self.lock_box, text="[ ? Why is this needed? ]", font=ctk.CTkFont(size=11, underline=True), text_color="#3498DB", cursor="hand2")
            self.help_icon.pack(pady=10)
            self.help_icon.bind("<Enter>", self.show_inline_help)
            self.help_icon.bind("<Leave>", self.hide_inline_help)

            self.admin_action_btn = ctk.CTkButton(self.lock_box, text="RUN AS ADMINISTRATOR", height=55, fg_color="#E67E22", hover_color="#D35400", font=ctk.CTkFont(size=14, weight="bold"), command=run_as_admin)
            self.admin_action_btn.pack(pady=(20, 10), padx=50, fill="x")

            self.cancel_btn = ctk.CTkButton(self.lock_box, text="CONTINUE IN READ-ONLY MODE", height=40, fg_color="transparent", border_width=1, border_color="gray40", text_color="gray70", command=self.dismiss_overlay)
            self.cancel_btn.pack(pady=5, padx=50, fill="x")

    def show_inline_help(self, event):
        self.info_text.configure(text="Windows Firewall prevents standard users from blocking IPs.\nAdministrator access is needed to 'cut off' servers.", text_color="#3498DB")

    def hide_inline_help(self, event):
        self.info_text.configure(text="Firewall modification requires elevation.", text_color="gray70")

    def apply_ping_filter(self):
        if not is_admin():
            self.show_admin_overlay()
            return
        try:
            self.ping_filter_min = int(self.ping_min_entry.get())
            self.ping_filter_max = int(self.ping_max_entry.get())
            self.active_preset = None
            self.update_preset_colors()
            
            def run_filter():
                for code, server in self.servers.items():
                    ping_val = server["ping"] if server["ping"] is not None else 999
                    should_block = not (self.ping_filter_min <= ping_val <= self.ping_filter_max)
                    if server["blocked"] != should_block:
                        server["blocked"] = should_block
                        self.after(0, lambda c=code, b=should_block: self.update_row_ui(c, b))
                        self.toggle_firewall(code, should_block)
                self.after(0, self.update_main_button)
            
            threading.Thread(target=run_filter, daemon=True).start()
        except ValueError:
            pass

    def show_admin_overlay(self):
        if hasattr(self, "overlay"):
            self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.overlay.lift()
            self.flash_admin_btn()

    def update_preset_colors(self):
        for region, btn in self.preset_buttons.items():
            if region == self.active_preset:
                btn.configure(fg_color="#3498DB", hover_color="#2980B9")
            else:
                btn.configure(fg_color="#2B2B2B", hover_color="#3D3D3D")

    def update_main_button(self):
        if not hasattr(self, "main_action_btn"): return
        any_blocked = any(s["blocked"] for s in self.servers.values())
        if any_blocked:
            self.main_action_btn.configure(text="UNBLOCK ALL", fg_color="#2ECC71", hover_color="#27AE60")
        else:
            self.main_action_btn.configure(text="BLOCK ALL", fg_color="#C0392B", hover_color="#962D22")

    def flash_admin_btn(self):
        if not hasattr(self, "admin_action_btn"): return
        original_color = self.admin_action_btn.cget("fg_color")
        def flash(count):
            if count <= 0:
                self.admin_action_btn.configure(fg_color=original_color)
                return
            new_color = "#F39C12" if count % 2 == 0 else "#E67E22"
            self.admin_action_btn.configure(fg_color=new_color)
            self.after(200, lambda: flash(count - 1))
        flash(6)

    def play_only_in(self, region_name):
        if not is_admin():
            self.show_admin_overlay()
            return
            
        self.active_preset = region_name
        self.update_preset_colors()
        
        allowed_codes = self.regions.get(region_name)[0]
        for code, server in self.servers.items():
            prefix = code[:3].lower()
            should_block = prefix not in allowed_codes
            
            if server["blocked"] != should_block:
                server["blocked"] = should_block
                self.update_row_ui(code, should_block)
        
        def run_firewall_logic():
            for code, server in self.servers.items():
                self.toggle_firewall(code, server["blocked"])
            self.after(0, self.update_main_button)
        
        threading.Thread(target=run_firewall_logic, daemon=True).start()

    def toggle_all_rules(self):
        if not is_admin():
            self.show_admin_overlay()
            return
        
        any_blocked = any(s["blocked"] for s in self.servers.values())
        target_state = not any_blocked 
        
        self.active_preset = None
        self.update_preset_colors()
        
        for code in self.servers:
            if self.servers[code]["blocked"] != target_state:
                self.servers[code]["blocked"] = target_state
                self.update_row_ui(code, target_state)
        
        def run():
            if not target_state: # UNBLOCK ALL
                result = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = result.stdout.decode('utf-8', errors='ignore')
                for line in output.splitlines():
                    if "Rule Name:" in line and RULE_PREFIX in line:
                        subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={line.split(':', 1)[1].strip()}"], capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else: # BLOCK ALL
                for code in self.servers:
                    self.toggle_firewall(code, True)
            self.after(0, self.update_main_button)
        
        threading.Thread(target=run, daemon=True).start()

    def dismiss_overlay(self):
        self.overlay.place_forget() 
        if not hasattr(self, "warning_btn"):
            self.warning_btn = ctk.CTkButton(self.right_panel, text="⚠️ READ ONLY MODE", height=40, fg_color="transparent", border_width=1, border_color="#E74C3C", text_color="#E74C3C", command=run_as_admin)
            self.warning_btn.pack(side="top", pady=10, padx=20, fill="x")

    def on_search(self, event=None):
        self.search_query = self.search_entry.get().lower()
        self.render_servers()

    def load_data_and_ping(self):
        threading.Thread(target=self.initial_data_fetch, daemon=True).start()

    def initial_data_fetch(self):
        try:
            response = requests.get(STEAM_CONFIG_URL, timeout=5)
            data = response.json()
            if "pops" in data:
                for code, info in data["pops"].items():
                    if "relays" in info and "cloud-test" not in code:
                        relays = [r["ipv4"] for r in info["relays"] if "ipv4" in r]
                        if relays:
                            self.servers[code] = {
                                "name": info.get("desc", code), 
                                "ips": relays, 
                                "ping": None, 
                                "blocked": False
                            }
                
                self.after(0, self.render_servers)
                self.after(0, self.ping_all_parallel)
                
                if is_admin():
                    self.sync_firewall_rules()
        except Exception as e:
            print(f"Error loading data: {e}")

    def sync_firewall_rules(self):
        try:
            result = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], 
                                 capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                output = result.stdout.decode('utf-8', errors='ignore') if b'\x00' not in result.stdout else result.stdout.decode('cp1250', errors='ignore')
                existing_rules = []
                for line in output.splitlines():
                    if "Rule Name:" in line and RULE_PREFIX in line:
                        existing_rules.append(line.split(":", 1)[1].strip().replace(RULE_PREFIX, ""))
                
                if existing_rules:
                    for code in existing_rules:
                        if code in self.servers:
                            self.servers[code]["blocked"] = True
                            self.after(0, lambda c=code: self.update_row_ui(c, True))
                    self.after(0, self.update_main_button)
        except Exception as e:
            print(f"Firewall sync error: {e}")

    def ping_all_parallel(self):
        def ping_server(code, ip):
            p = ping(ip, unit='ms', timeout=1)
            return code, int(p) if p is not None else None
        def run_parallel():
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                futures = [executor.submit(ping_server, code, s["ips"][0]) for code, s in self.servers.items()]
                for future in concurrent.futures.as_completed(futures):
                    code, p_val = future.result()
                    self.servers[code]["ping"] = p_val
                    self.after(0, lambda c=code, v=p_val: self.update_ping_ui(c, v))
        threading.Thread(target=run_parallel, daemon=True).start()

    def update_ping_ui(self, code, val):
        if code in self.server_rows:
            widgets = self.server_rows[code]
            if "ping_label" in widgets and widgets["ping_label"] is not None:
                label = widgets["ping_label"]
                if val is not None:
                    label.configure(text=f"{val} ms")
                    if val < 50: label.configure(text_color="#2ECC71")
                    elif val < 100: label.configure(text_color="#F1C40F")
                    else: label.configure(text_color="#E74C3C")
                else:
                    label.configure(text="Timeout", text_color="#555555")

    def prefetch_flags(self):
        countries = set(self.city_to_country.values())
        for _, flag_code in self.regions.values():
            countries.add(flag_code)
        
        def fetch_worker(code):
            if code in self.flag_images and self.flag_images[code] != self.placeholder_img: return
            try:
                url = FLAG_API_URL.format(code=code)
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    img_data = Image.open(BytesIO(response.content))
                    ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(24, 16))
                    self.flag_images[code] = ctk_img
                    self.after(0, lambda c=code: self.on_flag_loaded(c))
            except:
                pass

        # Pre-fill with placeholder
        for code in countries:
            if code not in self.flag_images:
                self.flag_images[code] = self.placeholder_img

        def run_prefetch():
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(fetch_worker, list(countries))
                
        threading.Thread(target=run_prefetch, daemon=True).start()

    def on_flag_loaded(self, country_code):
        # Update preset buttons
        img = self.flag_images.get(country_code)
        if img:
            for region, (codes, flag_code) in self.regions.items():
                if flag_code == country_code and region in self.preset_buttons:
                    btn = self.preset_buttons[region]
                    # Update image and also slightly update text to trigger redraw
                    current_text = btn.cget("text")
                    btn.configure(image=img, text=current_text)
            
            # Update server rows
            for code, widgets in self.server_rows.items():
                prefix = code[:3].lower()
                c_code = self.city_to_country.get(prefix)
                if c_code == country_code and "loc_label" in widgets:
                    widgets["loc_label"].configure(image=img)
        
        self.update() # More forceful than update_idletasks()

    def get_flag_by_code(self, country_code):
        if not country_code: return None
        return self.flag_images.get(country_code)

    def get_flag(self, city_code):
        prefix = city_code[:3].lower()
        country_code = self.city_to_country.get(prefix)
        return self.get_flag_by_code(country_code)

    def render_servers(self):
        filtered_codes = [c for c, s in self.servers.items() if self.search_query in s["name"].lower() or self.search_query in c.lower()]
        sorted_codes = sorted(filtered_codes, key=lambda c: self.servers[c]["name"])
        
        # Determine if we should show ping column based on width
        show_ping = self.winfo_width() >= 650
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.server_rows = {}

        for i, code in enumerate(sorted_codes):
            server = self.servers[code]
            is_blocked = server["blocked"]
            row = ctk.CTkFrame(self.scrollable_frame, fg_color="#252525" if i % 2 == 0 else "transparent", height=60, corner_radius=0)
            row.pack(fill="x", pady=0)
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, minsize=100 if show_ping else 0)
            row.grid_columnconfigure(2, minsize=140)
            row.grid_rowconfigure(0, weight=1)
            row.pack_propagate(False)
            
            loc_frame = ctk.CTkFrame(row, fg_color="transparent")
            loc_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
            
            loc_label = ctk.CTkLabel(loc_frame, text="")
            loc_label.pack(side="left", padx=(0, 15))
            flag = self.get_flag(code)
            if flag: loc_label.configure(image=flag)
            
            # Use wraplength if width is small to avoid pushing buttons
            name_text = f"{server['name']} ({code})"
            name_label = ctk.CTkLabel(loc_frame, text=name_text, font=ctk.CTkFont(size=14, weight="bold" if not is_blocked else "normal"), text_color="white" if not is_blocked else "#666666")
            name_label.pack(side="left")
            
            ping_label = None
            if show_ping:
                p_val = f"{server['ping']} ms" if server['ping'] is not None else "--"
                ping_label = ctk.CTkLabel(row, text=p_val, font=ctk.CTkFont(size=13, weight="bold"))
                if server['ping'] is not None and not is_blocked:
                    if server['ping'] < 50: ping_label.configure(text_color="#2ECC71")
                    elif server['ping'] < 100: ping_label.configure(text_color="#F1C40F")
                    else: ping_label.configure(text_color="#E74C3C")
                else:
                    ping_label.configure(text_color="#444444")
                ping_label.grid(row=0, column=1)
            
            btn_text = "BLOCKED ❌" if is_blocked else "BLOCK"
            btn_color = "#E74C3C" if is_blocked else "#333333"
            block_btn = ctk.CTkButton(row, text=btn_text, width=110, height=35, fg_color=btn_color, command=lambda c=code: self.on_toggle_server(c))
            block_btn.grid(row=0, column=2, padx=15)
            self.server_rows[code] = {"ping_label": ping_label, "block_btn": block_btn, "name_label": name_label, "loc_label": loc_label}
        
        self.update_main_button()

    def on_toggle_server(self, code):
        if not is_admin(): 
            self.show_admin_overlay()
            return
        self.active_preset = None
        self.update_preset_colors()
        new_val = not self.servers[code]["blocked"]
        self.servers[code]["blocked"] = new_val
        self.update_row_ui(code, new_val)
        threading.Thread(target=lambda: self.toggle_firewall(code, new_val), daemon=True).start()

    def update_row_ui(self, code, blocked):
        if code in self.server_rows:
            widgets = self.server_rows[code]
            widgets["block_btn"].configure(text="BLOCKED ❌" if blocked else "BLOCK", fg_color="#E74C3C" if blocked else "#333333")
            widgets["name_label"].configure(text_color="white" if not blocked else "#666666", font=ctk.CTkFont(size=14, weight="bold" if not blocked else "normal"))
            
            if "ping_label" in widgets and widgets["ping_label"] is not None:
                val = self.servers[code]["ping"]
                if val is not None and not blocked:
                    if val < 50: widgets["ping_label"].configure(text_color="#2ECC71")
                    elif val < 100: widgets["ping_label"].configure(text_color="#F1C40F")
                    else: widgets["ping_label"].configure(text_color="#E74C3C")
                else:
                    widgets["ping_label"].configure(text_color="#444444")
            
            flag = self.get_flag(code)
            if flag and "loc_label" in widgets:
                widgets["loc_label"].configure(image=flag)

    def toggle_firewall(self, server_code, block=True):
        if not is_admin(): return False
        rule_name = f"{RULE_PREFIX}{server_code}"
        subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"], capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if block:
            ips = ",".join(self.servers[server_code]["ips"])
            subprocess.run(f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=block remoteip={ips} protocol=UDP enable=yes', capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True

if __name__ == "__main__":
    if not is_admin():
        # Try to get admin rights immediately on startup
        run_as_admin()
    app = SteamServerPicker()
    app.mainloop()
