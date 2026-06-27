import tkinter as tk
from tkinter import filedialog, messagebox, font
from tkinter.scrolledtext import ScrolledText
import configparser
import socket
import os

BackGnd = '#2b2b2b'
INI_FILE = 'SCPI_sender.ini'
DEFAULT_IP = '192.168.58.102'
DEFAULT_SCPI = '*IDN?\n:SYST:ERR?\n:SYST:ERR?'
PORT = 5025

class SCPISender:
    def __init__(self, root):
        self.root = root
        self.root.title('SCPI Sender')
        self.root.iconbitmap("SCPI_sender.ico")
        self.root.geometry('600x600')
        self.root.config(bg=BackGnd)
        self.bold_font = font.Font(weight='bold')

        self.root.bind("<F5>", lambda event: self.send_scpi())

        top = tk.Frame(root, bg=BackGnd)
        top.pack(fill='x', padx=5, pady=5)

        tk.Label(top, text='Instr_IP', bg=BackGnd, fg='white').pack(side='left')
        self.ip_entry = tk.Entry(top, width=30, bg='black', fg='yellow', insertbackground='white')
        self.ip_entry.pack(side='left', padx=5)

        tk.Label(root, text='SCPI to send', bg=BackGnd, fg='white').pack(anchor='w', padx=5)
        self.scpi_text = ScrolledText(root, height=10, wrap=tk.NONE, bg='black', fg='white', insertbackground='white')
        self.scpi_text.pack(fill='both', expand=True, padx=5)

        tk.Label(root, text='Output', bg=BackGnd, fg='white').pack(anchor='w', padx=5)
        self.output_text = ScrolledText(root, height=10, wrap=tk.NONE, bg='black', fg='white', insertbackground='white')
        self.output_text.pack(fill='both', expand=True, padx=5, pady=(0, 5))
        self.output_text.tag_configure('green', foreground="#00ff00")
        self.output_text.tag_configure('red', foreground="#430000", background="#FD0303")

        btn_frame = tk.Frame(root, height=15, bg=BackGnd)
        btn_frame.pack(fill="x", padx=5, pady=2)

        tk.Button(btn_frame, text="📂 File", width=10, command=self.load_file).pack(side="left", padx=5)
        # tk.Button(btn_frame, text="🗑 Clear", width=10, command=self.clear_all).pack(side="left", padx=5)
        tk.Button(btn_frame, text="↺ Reset", width=10, command=self.default_vals).pack(side="left", padx=5)
        tk.Button(btn_frame, text="▶ Send", width=10, command=self.send_scpi, bg='green', fg='white').pack(side="left", padx=5)
        tk.Button(btn_frame, text="⏻ Exit", width=10, command=self.exit_program).pack(side="right", padx=5)

        # buttons = tk.Frame(root)
        # buttons.pack(fill='x', padx=5, pady=5)

        # tk.Button(buttons, text='File', width=10, command=self.load_file).pack(side='left', padx=4)
        # tk.Button(buttons, text='Clear', width=10, command=self.clear_all).pack(side='left', padx=4)
        # tk.Button(buttons, text='Reset', width=10, command=self.default_vals).pack(side='left', padx=4)
        # tk.Button(buttons, text='Send', width=10, command=self.send_scpi, bg='green', fg='white').pack(side='left', padx=4)
        # tk.Button(buttons, text='Exit', width=10, command=self.exit_program).pack(side='right', padx=4)

        self.load_ini()
        self.root.protocol('WM_DELETE_WINDOW', self.exit_program)

    def log(self, msg, tag=None):
        if tag:
            self.output_text.insert(tk.END, msg + '\n', tag)
        else:
            self.output_text.insert(tk.END, msg + '\n')
        self.output_text.see(tk.END)

    def load_ini(self):
        ip = DEFAULT_IP
        scpi = DEFAULT_SCPI
        output = ''

        if os.path.exists(INI_FILE):
            cfg = configparser.ConfigParser()
            cfg.read(INI_FILE)
            if cfg.has_section('Settings'):
                ip = cfg.get('Settings', 'ip', fallback=DEFAULT_IP)
                scpi = cfg.get('Settings', 'scpi', fallback=DEFAULT_SCPI)
                output = cfg.get('Settings', 'output', fallback='')

        self.ip_entry.insert(0, ip)
        self.scpi_text.insert('1.0', scpi)
        self.output_text.insert('1.0', output)

    def save_ini(self):
        cfg = configparser.ConfigParser()
        cfg['Settings'] = {
            'ip': self.ip_entry.get().strip(),
            'scpi': self.scpi_text.get('1.0', tk.END).rstrip(),
            'output': self.output_text.get('1.0', tk.END).rstrip()
        }

        with open(INI_FILE, 'w') as f:
            cfg.write(f)

    def load_file(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

        filename = filedialog.askopenfilename(
            title='Select SCPI File',
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
        )
        if filename:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            self.scpi_text.delete('1.0', tk.END)
            self.scpi_text.insert('1.0', data)

    def send_scpi(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror('Error', 'Invalid IP address.')
            return

        commands = self.scpi_text.get('1.0', tk.END).splitlines()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, PORT))

            for cmd in commands:
                cmd = cmd.strip()
                if not cmd:
                    continue

                self.log(f'--> {cmd}')
                sock.sendall((cmd + '\n').encode())

                if '?' in cmd:
                    response = sock.recv(8192).decode(errors='ignore').strip()
                    self.log(f'<-- {response}', 'green')

            sock.close()

        except Exception as e:
            self.log(f'ERROR: {e}', 'red')

    def clear_all(self):
        self.scpi_text.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)

    def default_vals(self):
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, DEFAULT_IP)
        self.scpi_text.delete('1.0', tk.END)
        self.scpi_text.insert('1.0', DEFAULT_SCPI)
        self.output_text.delete('1.0', tk.END)

    def exit_program(self):
        self.save_ini()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    SCPISender(root)
    root.mainloop()
