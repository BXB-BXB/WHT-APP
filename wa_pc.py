import customtkinter as ctk
import zipfile
import re
import io
from PIL import Image, ImageTk

class WA_PC_App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WhatsApp Private Viewer - PC Version")
        self.geometry("1100x800")
        
        self.db = []
        self.media_map = {}
        self.owner = ""

        # Layout: Sidebar (Stânga) + Main (Dreapta)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.load_btn = ctk.CTkButton(self.sidebar, text="📁 ÎNCARCĂ ZIP", command=self.load_zip, fg_color="#25d366", hover_color="#128c7e")
        self.load_btn.pack(pady=20, padx=10)

        self.btn_chat = ctk.CTkButton(self.sidebar, text="MESAJE", command=lambda: self.show_view("chat"))
        self.btn_chat.pack(pady=5, padx=10)

        self.btn_media = ctk.CTkButton(self.sidebar, text="MEDIA SEPARATĂ", command=lambda: self.show_view("media"))
        self.btn_media.pack(pady=5, padx=10)
        
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Caută text...")
        self.search_entry.pack(pady=20, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.render_chat())

        # MAIN VIEW
        self.container = ctk.CTkFrame(self, fg_color="#efe7de")
        self.container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.chat_view = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.chat_view.grid(row=0, column=0, sticky="nsew")

        self.media_view = ctk.CTkScrollableFrame(self.container, fg_color="#ffffff")
        # Se va afișa doar la cerere

    def load_zip(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Arhiva ZIP", "*.zip")])
        if not path: return
        
        with zipfile.ZipFile(path, 'r') as z:
            # 1. Citire Text
            txt_n = [n for n in z.namelist() if n.lower().endswith('.txt')][0]
            raw = z.read(txt_n).decode('utf-8')
            
            # 2. Indexare Media
            for n in z.namelist():
                if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    img_data = z.read(n)
                    self.media_map[n.split('/').pop()] = Image.open(io.BytesIO(img_data))

            # 3. Parsare Linii
            reg = r'^\[?(\d{1,2}[\/\.]\d{1,2}[\/\.]\d{2,4},?\s\d{1,2}:\d{2})\]?\s-?\s?(.*?):\s(.*)'
            for i, line in enumerate(raw.split('\n')):
                m = re.match(reg, line)
                if m:
                    if not self.owner: self.owner = m.group(2)
                    self.db.append({'id': i, 'time': m.group(1), 'user': m.group(2), 'text': m.group(3)})
        
        self.render_chat()
        self.render_media()

    def render_chat(self):
        # Ștergem ce era înainte
        for child in self.chat_view.winfo_children(): child.destroy()
        
        query = self.search_entry.get().lower()
        self.message_widgets = {} # Pentru funcția Jump

        for m in self.db:
            if query and query not in m['text'].lower(): continue
            
            is_me = m['user'] == self.owner
            frame = ctk.CTkFrame(self.chat_view, fg_color="#ffffff" if is_me else "#d9fdd3", corner_radius=10)
            frame.pack(pady=5, padx=10, anchor="w" if is_me else "e", fill="x")
            
            self.message_widgets[m['id']] = frame
            
            # Media în chat
            att = re.search(r'<(.*?)adatat>|<attached: (.*?)>', m['text'])
            if att:
                fname = (att.group(1) or att.group(2)).strip()
                if fname in self.media_map:
                    img = self.media_map[fname].copy()
                    img.thumbnail((300, 300))
                    img_tk = ImageTk.PhotoImage(img)
                    img_lbl = ctk.CTkLabel(frame, image=img_tk, text="")
                    img_lbl.image = img_tk
                    img_lbl.pack(pady=5, padx=10)

            txt_lbl = ctk.CTkLabel(frame, text=f"{m['user']}\n{m['text']}\n{m['time']}", justify="left", wraplength=600)
            txt_lbl.pack(pady=5, padx=10)

    def render_media(self):
        for child in self.media_view.winfo_children(): child.destroy()
        
        row, col = 0, 0
        for m in self.db:
            att = re.search(r'<(.*?)adatat>|<attached: (.*?)>', m['text'])
            if att:
                fname = (att.group(1) or att.group(2)).strip()
                if fname in self.media_map:
                    img = self.media_map[fname].copy()
                    img.thumbnail((150, 150))
                    img_tk = ImageTk.PhotoImage(img)
                    
                    btn = ctk.CTkButton(self.media_view, image=img_tk, text="", width=150, height=150, 
                                        fg_color="transparent", command=lambda mid=m['id']: self.jump_to(mid))
                    btn.image = img_tk
                    btn.grid(row=row, column=col, padx=5, pady=5)
                    
                    col += 1
                    if col > 4: 
                        col = 0
                        row += 1

    def jump_to(self, mid):
        self.show_view("chat")
        target = self.message_widgets.get(mid)
        if target:
            # Highlight efect
            original_color = target.cget("fg_color")
            target.configure(fg_color="#fff59d")
            self.chat_view._parent_canvas.yview_moveto(target.winfo_y() / self.chat_view.winfo_height())
            self.after(2000, lambda: target.configure(fg_color=original_color))

    def show_view(self, view):
        if view == "chat":
            self.chat_view.grid(row=0, column=0, sticky="nsew")
            self.media_view.grid_forget()
        else:
            self.media_view.grid(row=0, column=0, sticky="nsew")
            self.chat_view.grid_forget()

if __name__ == "__main__":
    app = WA_PC_App()
    app.mainloop()
