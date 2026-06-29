import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading
import time
import re
import os
from pathlib import Path
import pyttsx3
import tempfile

# ============================================================
# TEXT PREPROCESSOR
# ============================================================

class TextPreprocessor:
    @staticmethod
    def preprocess(text):
        abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Misses',
            'Ms.': 'Miss',
            'Sr.': 'Senior',
            'Jr.': 'Junior',
            'St.': 'Saint',
            'Ave.': 'Avenue',
            'Blvd.': 'Boulevard',
            'Rd.': 'Road',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'et cetera',
            'vs.': 'versus',
            'w/': 'with',
            'w/o': 'without',
            '&': 'and',
            '@': 'at',
            '%': 'percent',
            '₹': 'rupees',
            '$': 'dollars'
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # Fix numbers
        def expand_numbers(match):
            num = match.group(0)
            if len(num) == 4 and num.startswith('20'):
                return 'two thousand ' + num[2:]
            return num
        
        text = re.sub(r'\b\d{1,4}\b', expand_numbers, text)
        return text

# ============================================================
# MAIN APPLICATION (Using pyttsx3)
# ============================================================

class TTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Offline Text-to-Speech Pro")
        self.geometry("800x700")
        self.configure(bg="#f0f4f8")
        self.resizable(True, True)
        
        # ============================================================
        # TTS ENGINE
        # ============================================================
        self.engine = None
        self.voices = []
        self.current_voice_index = 0
        self.speed = 200  # Default speed
        self.volume = 1.0
        
        # Initialize engine
        self._init_engine()
        
        # ============================================================
        # PLAYBACK STATE
        # ============================================================
        self.is_playing = False
        self.is_paused = False
        self.stop_playback = False
        self.play_thread = None
        self.text_to_speak = ""
        
        # ============================================================
        # BUILD GUI
        # ============================================================
        self.preprocessor = TextPreprocessor()
        self.build_gui()
        if self.voices:
            self.update_voice_info()
    
    def _init_engine(self):
        """Initialize TTS engine"""
        try:
            if self.engine is not None:
                try:
                    self.engine.stop()
                except:
                    pass
            
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            if not self.voices:
                self.voices = []
            
            if self.voices:
                self.engine.setProperty('voice', self.voices[0].id)
            self.engine.setProperty('rate', self.speed)
            self.engine.setProperty('volume', self.volume)
            
            return True
        except Exception as e:
            print(f"Engine init error: {e}")
            self.engine = None
            self.voices = []
            return False
    
    def build_gui(self):
        """Build all GUI components"""
        
        # ---------- HEADER ----------
        header = tk.Label(self, text="🗣️ Offline Text-to-Speech Pro", 
                          font=("Arial", 20, "bold"), bg="#f0f4f8", fg="#2c3e50")
        header.pack(pady=10)
        
        subtitle = tk.Label(self, text="100% Free • No Internet Required • Windows Voices", 
                           font=("Arial", 10), bg="#f0f4f8", fg="#7f8c8d")
        subtitle.pack(pady=(0, 10))
        
        # ---------- MAIN FRAME ----------
        main_frame = tk.Frame(self, bg="#f0f4f8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ---------- LEFT: CONTROLS ----------
        control_frame = tk.LabelFrame(main_frame, text="Controls", 
                                     font=("Arial", 12, "bold"), bg="#f0f4f8", padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Quick Phrases
        quick_label = tk.Label(control_frame, text="Quick Phrases:", 
                              font=("Arial", 10, "bold"), bg="#f0f4f8")
        quick_label.pack(anchor=tk.W, pady=(0, 5))
        
        quick_frame = tk.Frame(control_frame, bg="#f0f4f8")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        phrases = ["Hello!", "Thank you!", "I need help", "Good morning", "Good night"]
        for phrase in phrases:
            btn = tk.Button(quick_frame, text=phrase, 
                          command=lambda p=phrase: self.insert_quick_phrase(p),
                          bg="#3498db", fg="white", font=("Arial", 8), padx=5, pady=2)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Voice Selection
        voice_label = tk.Label(control_frame, text="Voice:", 
                              font=("Arial", 10, "bold"), bg="#f0f4f8")
        voice_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.voice_var = tk.StringVar()
        voice_menu = ttk.Combobox(control_frame, textvariable=self.voice_var, 
                                 state="readonly", width=25)
        voice_menu.pack(fill=tk.X, pady=(0, 5))
        voice_menu.bind('<<ComboboxSelected>>', self.change_voice)
        
        voice_names = []
        for voice in self.voices:
            name = voice.name if voice.name else f"Voice {len(voice_names)}"
            voice_names.append(name)
        voice_menu['values'] = voice_names
        if voice_names:
            self.voice_var.set(voice_names[0])
        
        voice_btn = tk.Button(control_frame, text="👤 Next Voice", 
                            command=self.next_voice, bg="#9b59b6", fg="white",
                            font=("Arial", 10))
        voice_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Speed Control
        speed_label = tk.Label(control_frame, text="Speed:", 
                              font=("Arial", 10, "bold"), bg="#f0f4f8")
        speed_label.pack(anchor=tk.W, pady=(10, 0))
        
        speed_frame = tk.Frame(control_frame, bg="#f0f4f8")
        speed_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Button(speed_frame, text="🐢", command=lambda: self.change_speed(-20),
                 bg="#2ecc71", fg="white", font=("Arial", 10), width=3).pack(side=tk.LEFT)
        
        self.speed_label = tk.Label(speed_frame, text="200", 
                                   font=("Arial", 10), bg="#f0f4f8", width=5)
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(speed_frame, text="🐇", command=lambda: self.change_speed(20),
                 bg="#e67e22", fg="white", font=("Arial", 10), width=3).pack(side=tk.LEFT)
        
        # Volume Control
        volume_label = tk.Label(control_frame, text="Volume:", 
                               font=("Arial", 10, "bold"), bg="#f0f4f8")
        volume_label.pack(anchor=tk.W, pady=(10, 0))
        
        volume_frame = tk.Frame(control_frame, bg="#f0f4f8")
        volume_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(volume_frame, text="🔇", command=lambda: self.change_volume(-0.1),
                 bg="#e74c3c", fg="white", font=("Arial", 10), width=3).pack(side=tk.LEFT)
        
        self.volume_label = tk.Label(volume_frame, text="100%", 
                                    font=("Arial", 10), bg="#f0f4f8", width=5)
        self.volume_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(volume_frame, text="🔊", command=lambda: self.change_volume(0.1),
                 bg="#2ecc71", fg="white", font=("Arial", 10), width=3).pack(side=tk.LEFT)
        
        tk.Frame(control_frame, height=2, bg="#bdc3c7").pack(fill=tk.X, pady=10)
        
        # Playback Controls
        playback_label = tk.Label(control_frame, text="Playback:", 
                                 font=("Arial", 10, "bold"), bg="#f0f4f8")
        playback_label.pack(anchor=tk.W)
        
        play_frame = tk.Frame(control_frame, bg="#f0f4f8")
        play_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(play_frame, text="▶ Play", command=self.start_playback,
                 bg="#27ae60", fg="white", font=("Arial", 10), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(play_frame, text="⏸ Pause", command=self.pause_playback,
                 bg="#f39c12", fg="white", font=("Arial", 10), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(play_frame, text="⏹ Stop", command=self.stop_playback_func,
                 bg="#e74c3c", fg="white", font=("Arial", 10), width=8).pack(side=tk.LEFT, padx=2)
        
        tk.Frame(control_frame, height=2, bg="#bdc3c7").pack(fill=tk.X, pady=10)
        
        # File Operations
        file_label = tk.Label(control_frame, text="Files:", 
                             font=("Arial", 10, "bold"), bg="#f0f4f8")
        file_label.pack(anchor=tk.W)
        
        tk.Button(control_frame, text="📄 Import File", command=self.import_file,
                 bg="#8e44ad", fg="white", font=("Arial", 10)).pack(fill=tk.X, pady=2)
        tk.Button(control_frame, text="💾 Save as Audio", command=self.save_audio,
                 bg="#2980b9", fg="white", font=("Arial", 10)).pack(fill=tk.X, pady=2)
        
        # ---------- RIGHT: TEXT AREA ----------
        text_frame = tk.LabelFrame(main_frame, text="Text Input", 
                                  font=("Arial", 12, "bold"), bg="#f0f4f8", padx=10, pady=10)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.text_box = scrolledtext.ScrolledText(text_frame, height=15, 
                                                   font=("Arial", 12), wrap=tk.WORD)
        self.text_box.pack(fill=tk.BOTH, expand=True)
        
        # ---------- PROGRESS BAR ----------
        progress_frame = tk.Frame(self, bg="#f0f4f8")
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, length=100, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        self.status_label = tk.Label(progress_frame, text="Ready", 
                                    font=("Arial", 9), bg="#f0f4f8", fg="#7f8c8d")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # ---------- VOICE INFO ----------
        self.voice_info = tk.Label(self, text="", font=("Arial", 9), 
                                  bg="#f0f4f8", fg="#7f8c8d")
        self.voice_info.pack(pady=(0, 10))
    
    # ============================================================
    # QUICK PHRASES
    # ============================================================
    
    def insert_quick_phrase(self, phrase):
        self.text_box.insert(tk.END, phrase + " ")
        self.text_box.focus()
    
    # ============================================================
    # VOICE SELECTION
    # ============================================================
    
    def change_voice(self, event=None):
        if not self.voices:
            return
        selection = self.voice_var.get()
        for i, voice in enumerate(self.voices):
            name = voice.name if voice.name else f"Voice {i}"
            if name == selection:
                self.current_voice_index = i
                if self.engine:
                    self.engine.setProperty('voice', voice.id)
                self.voice_info.config(text=f"Current Voice: {selection}")
                break
    
    def next_voice(self):
        if not self.voices:
            return
        self.current_voice_index = (self.current_voice_index + 1) % len(self.voices)
        voice = self.voices[self.current_voice_index]
        if self.engine:
            self.engine.setProperty('voice', voice.id)
        name = voice.name if voice.name else f"Voice {self.current_voice_index}"
        self.voice_var.set(name)
        self.voice_info.config(text=f"Current Voice: {name}")
    
    def update_voice_info(self):
        if self.voices:
            voice = self.voices[self.current_voice_index]
            name = voice.name if voice.name else f"Voice {self.current_voice_index}"
            self.voice_info.config(text=f"Current Voice: {name}")
    
    # ============================================================
    # SPEED & VOLUME
    # ============================================================
    
    def change_speed(self, delta):
        self.speed = max(50, min(400, self.speed + delta))
        if self.engine:
            self.engine.setProperty('rate', self.speed)
        self.speed_label.config(text=str(self.speed))
    
    def change_volume(self, delta):
        self.volume = max(0.0, min(1.0, self.volume + delta))
        if self.engine:
            self.engine.setProperty('volume', self.volume)
        self.volume_label.config(text=f"{int(self.volume * 100)}%")
    
    # ============================================================
    # TEXT PREPROCESSING
    # ============================================================
    
    def get_processed_text(self):
        raw_text = self.text_box.get("1.0", tk.END).strip()
        if not raw_text:
            return ""
        return self.preprocessor.preprocess(raw_text)
    
    # ============================================================
    # PLAYBACK (FIXED)
    # ============================================================
    
    def start_playback(self):
        if self.engine is None:
            messagebox.showerror("Error", "TTS engine not initialized!")
            self._init_engine()
            if self.engine is None:
                return
        
        if self.is_paused:
            self.is_paused = False
            self.status_label.config(text="▶ Resumed")
            if self.engine:
                self.engine.resume()
            return
        
        if self.is_playing:
            return
        
        text = self.get_processed_text()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text first!")
            return
        
        self.stop_playback = False
        self.is_playing = True
        self.text_to_speak = text
        
        self.status_label.config(text="▶ Speaking...")
        self.progress['value'] = 0
        
        # Start in separate thread
        self.play_thread = threading.Thread(target=self._speak_text, args=(text,))
        self.play_thread.daemon = True
        self.play_thread.start()
    
    def _speak_text(self, text):
        try:
            # Create a fresh engine for speaking
            engine = pyttsx3.init()
            
            # Set properties
            if self.voices:
                voice = self.voices[self.current_voice_index]
                engine.setProperty('voice', voice.id)
            engine.setProperty('rate', self.speed)
            engine.setProperty('volume', self.volume)
            
            # Split into sentences for progress
            sentences = re.split(r'(?<=[.!?])\s+', text)
            total = len(sentences)
            
            for i, sentence in enumerate(sentences):
                if self.stop_playback:
                    break
                
                while self.is_paused:
                    time.sleep(0.1)
                    if self.stop_playback:
                        break
                
                if self.stop_playback:
                    break
                
                # Speak the sentence
                engine.say(sentence)
                engine.runAndWait()
                
                # Update progress
                self.after(0, self._update_progress, int((i + 1) / total * 100))
            
            # Clean up
            try:
                engine.stop()
            except:
                pass
            
            if not self.stop_playback:
                self.after(0, self._playback_finished)
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Speech error: {str(e)}"))
            self.after(0, self._playback_finished)
    
    def _update_progress(self, value):
        self.progress['value'] = value
    
    def _playback_finished(self):
        self.is_playing = False
        self.is_paused = False
        self.status_label.config(text="✅ Done")
        self.progress['value'] = 100
    
    def pause_playback(self):
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.status_label.config(text="⏸ Paused")
            if self.engine:
                self.engine.stop()
    
    def stop_playback_func(self):
        self.stop_playback = True
        self.is_playing = False
        self.is_paused = False
        self.status_label.config(text="⏹ Stopped")
        self.progress['value'] = 0
    
    # ============================================================
    # SAVE AS AUDIO
    # ============================================================
    
    def save_audio(self):
        if self.engine is None:
            messagebox.showerror("Error", "TTS engine not initialized!")
            return
        
        raw_text = self.text_box.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showwarning("Warning", "Please enter some text first!")
            return
        
        text = self.preprocessor.preprocess(raw_text)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV Audio", "*.wav")]
        )
        
        if not file_path:
            return
        
        try:
            self.status_label.config(text="💾 Saving...")
            self.update()
            
            engine = pyttsx3.init()
            
            if self.voices:
                voice = self.voices[self.current_voice_index]
                engine.setProperty('voice', voice.id)
            engine.setProperty('rate', self.speed)
            engine.setProperty('volume', self.volume)
            
            engine.save_to_file(text, file_path)
            engine.runAndWait()
            
            try:
                engine.stop()
            except:
                pass
            
            self.status_label.config(text="✅ Saved!")
            messagebox.showinfo("Success", f"Audio saved to:\n{file_path}")
            
        except Exception as e:
            self.status_label.config(text="❌ Error")
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    # ============================================================
    # IMPORT FILE
    # ============================================================
    
    def import_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported", "*.txt *.pdf *.docx"),
                ("Text Files", "*.txt"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx")
            ]
        )
        
        if not file_path:
            return
        
        try:
            self.status_label.config(text="📄 Reading file...")
            self.update()
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                except ImportError:
                    messagebox.showerror("Error", "PyPDF2 not installed. Run: pip install PyPDF2")
                    return
            
            elif ext == '.docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    messagebox.showerror("Error", "python-docx not installed. Run: pip install python-docx")
                    return
            
            else:
                messagebox.showerror("Error", "Unsupported file format")
                return
            
            if not text.strip():
                messagebox.showwarning("Warning", "No text found in the file!")
                return
            
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert("1.0", text)
            
            self.status_label.config(text="✅ File loaded!")
            messagebox.showinfo("Success", f"Loaded: {os.path.basename(file_path)}\n{len(text)} characters")
            
        except Exception as e:
            self.status_label.config(text="❌ Error")
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    try:
        app = TTSApp()
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")