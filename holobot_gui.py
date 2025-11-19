#!/usr/bin/env python3
"""
HoloBot GUI - Tkinter interface for the Holographic Assistant

Features:
- ChatGPT-like dark mode UI
- Scrollable chat with left/right aligned message bubbles
- Text input with Send button
- Optional Speak button for voice input (uses existing HoloBot voice methods)
- Real-time display and TTS via existing HoloBot.speak
- Uses existing memory persistence in memory.json
"""

import os
import threading
import queue
import tkinter as tk
from tkinter import messagebox
from typing import Optional
import requests

from dotenv import load_dotenv

# Local import
from holobot import HoloBot


class HoloBotGUI:
    """Tkinter GUI wrapper around HoloBot."""

    def __init__(self, root: tk.Tk):
        load_dotenv()
        self.root = root
        self.root.title("HoloBot - Holographic Assistant")
        self.root.geometry("900x600")
        self.root.minsize(700, 480)

        # Dark theme colors
        self.color_bg = "#0f172a"       # slate-900
        self.color_panel = "#111827"    # gray-900
        self.color_user = "#1f2937"     # gray-800 bubble
        self.color_assistant = "#0b3d2e"# deep green-tinted bubble
        self.color_text = "#e5e7eb"     # gray-200
        self.color_subtle = "#9ca3af"   # gray-400
        self.color_accent = "#22c55e"   # green-500
        self.color_button = "#1f2937"   # gray-800

        self.root.configure(bg=self.color_bg)

        # Initialize bot
        try:
            self.bot = HoloBot()
        except Exception as exc:
            error_msg = str(exc)
            if "DEEPSEEK_API_KEY" in error_msg:
                messagebox.showerror("Configuration Error", 
                    "DeepSeek API key not found!\n\n"
                    "Please ensure your .env file contains:\n"
                    "DEEPSEEK_API_KEY=your_api_key_here\n\n"
                    "Get your API key from: https://platform.deepseek.com/")
            else:
                messagebox.showerror("Initialization Error", f"Failed to initialize HoloBot:\n{exc}")
            raise

        # Async queues and threading state
        self.response_queue: queue.Queue[str] = queue.Queue()
        self.voice_queue: queue.Queue[str] = queue.Queue()
        self.active_request_lock = threading.Lock()

        # Streaming state for assistant output
        self.current_assistant_label: Optional[tk.Label] = None
        self.current_assistant_text: str = ""

        # Build UI
        self._build_widgets()
        self._load_prior_conversation()
        # Test connection after UI is ready so system messages can render
        self._test_ai_connection()

        # Poll for async responses
        self.root.after(100, self._poll_queues)

    def _build_widgets(self) -> None:
        # Top header
        header = tk.Frame(self.root, bg=self.color_bg)
        header.pack(fill=tk.X, padx=16, pady=(12, 6))
        title = tk.Label(header, text="HoloBot - Holographic Assistant", fg=self.color_text, bg=self.color_bg, font=("Segoe UI Semibold", 14))
        title.pack(side=tk.LEFT)

        # Chat area: Canvas + Scrollable Frame for bubbles
        chat_wrapper = tk.Frame(self.root, bg=self.color_bg)
        chat_wrapper.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        self.canvas = tk.Canvas(chat_wrapper, bg=self.color_panel, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(chat_wrapper, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.messages_frame = tk.Frame(self.canvas, bg=self.color_panel)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")

        # Bind resizing and scrollregion updates
        self.messages_frame.bind("<Configure>", lambda _e: self._on_frame_configure())
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_configure(e))

        # Bottom input panel
        bottom = tk.Frame(self.root, bg=self.color_bg)
        bottom.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.entry = tk.Entry(bottom, font=("Segoe UI", 11), bg=self.color_button, fg=self.color_text, insertbackground=self.color_text, relief=tk.FLAT)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=8)
        self.entry.bind("<Return>", lambda _e: self.on_send())

        self.btn_send = tk.Button(bottom, text="Send", command=self.on_send, width=10, bg=self.color_accent, fg="#052e16", relief=tk.FLAT, activebackground="#16a34a", activeforeground="#052e16")
        self.btn_send.pack(side=tk.LEFT)

        self.btn_speak = tk.Button(bottom, text="Speak", command=self.on_speak, width=10, bg=self.color_button, fg=self.color_text, relief=tk.FLAT, activebackground="#374151", activeforeground=self.color_text)
        self.btn_speak.pack(side=tk.LEFT, padx=(8, 0))

        # Disable speak if voice input unavailable
        if not getattr(self.bot, "voice_input_enabled", False):
            self.btn_speak.configure(state=tk.DISABLED, bg="#374151")
            self._append_line("system", "Voice input unavailable. Using text chat mode.")
        else:
            self._append_line("system", "Say 'Hey Holo' or use Speak to talk.")

    def _load_prior_conversation(self) -> None:
        # Render any prior conversation from bot.messages (ensure initial system prompt visible)
        for idx, msg in enumerate(self.bot.messages):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            if idx == 0 and role == "system":
                self._append_line("system", content)
                continue
            if role in ("user", "assistant") and content:
                self._append_line(role, content)

    def _append_line(self, role: str, text: str) -> None:
        # Create a message bubble aligned per role
        bubble_wrapper = tk.Frame(self.messages_frame, bg=self.color_panel)
        bubble_wrapper.pack(fill=tk.X, padx=12, pady=6)

        align = "w" if role in ("assistant", "system") else "e"
        inner = tk.Frame(bubble_wrapper, bg=self.color_panel)
        inner.pack(fill=tk.X)

        # Bubble color and label prefix
        if role == "user":
            bubble_bg = self.color_user
            prefix = "You"
        elif role == "assistant":
            bubble_bg = self.color_assistant
            prefix = "HoloBot"
        else:
            bubble_bg = "#0b1220"  # darker for system
            prefix = "System"

        # Container to control alignment
        container = tk.Frame(inner, bg=self.color_panel)
        container.pack(anchor=align, fill=None)

        # Name label (small, subtle)
        name_lbl = tk.Label(container, text=prefix, font=("Segoe UI", 9), fg=self.color_subtle, bg=self.color_panel)
        name_lbl.pack(anchor=align, padx=4, pady=(0, 2))

        # Bubble label
        bubble = tk.Label(
            container,
            text=text,
            justify=tk.LEFT,
            wraplength=max(400, int(self.root.winfo_width() * 0.5)),
            font=("Segoe UI", 11),
            bg=bubble_bg,
            fg=self.color_text,
            padx=12,
            pady=8,
        )
        bubble.pack(anchor=align, padx=4)

        # Auto-scroll to bottom
        self.root.after(10, lambda: self.canvas.yview_moveto(1.0))

    def _start_assistant_stream(self) -> None:
        # Create an empty assistant bubble we can update as tokens arrive
        bubble_wrapper = tk.Frame(self.messages_frame, bg=self.color_panel)
        bubble_wrapper.pack(fill=tk.X, padx=12, pady=6)

        align = "w"  # assistant is left-aligned
        inner = tk.Frame(bubble_wrapper, bg=self.color_panel)
        inner.pack(fill=tk.X)

        container = tk.Frame(inner, bg=self.color_panel)
        container.pack(anchor=align, fill=None)

        name_lbl = tk.Label(container, text="HoloBot", font=("Segoe UI", 9), fg=self.color_subtle, bg=self.color_panel)
        name_lbl.pack(anchor=align, padx=4, pady=(0, 2))

        self.current_assistant_text = ""
        self.current_assistant_label = tk.Label(
            container,
            text="",
            justify=tk.LEFT,
            wraplength=max(400, int(self.root.winfo_width() * 0.5)),
            font=("Segoe UI", 11),
            bg=self.color_assistant,
            fg=self.color_text,
            padx=12,
            pady=8,
        )
        self.current_assistant_label.pack(anchor=align, padx=4)
        self.root.after(10, lambda: self.canvas.yview_moveto(1.0))

    def _append_to_assistant_stream(self, text: str) -> None:
        if not text:
            return
        if self.current_assistant_label is None:
            self._start_assistant_stream()
        self.current_assistant_text += text
        # Update label text
        if self.current_assistant_label is not None:
            self.current_assistant_label.configure(text=self.current_assistant_text)
            # Auto-scroll
            self.root.after(10, lambda: self.canvas.yview_moveto(1.0))

    def _end_assistant_stream(self) -> None:
        self.current_assistant_label = None
        self.current_assistant_text = ""

    def on_send(self) -> None:
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, tk.END)
        self._append_line("user", user_text)
        self._ask_async(user_text)

    def on_speak(self) -> None:
        # Capture one utterance after wake word (optional) using bot's existing methods
        if not getattr(self.bot, "voice_input_enabled", False):
            messagebox.showinfo("Voice Input", "Voice input is not available on this system.")
            return
        # Run voice capture on a background thread
        threading.Thread(target=self._capture_voice_once, daemon=True).start()

    def _capture_voice_once(self) -> None:
        try:
            # Optionally honor wake word. If not heard, still allow manual capture.
            heard = self.bot.listen_for_wake_word()
            if not heard:
                # If wake word not detected quickly, prompt user and capture directly
                self._append_line("system", "(Wake word not detected. Listening now...)")
            text = self.bot.listen_for_input()
            text = (text or "").strip()
            if not text:
                self._append_line("system", "Sorry, I didn't catch that.")
                return
            self._append_line("user", text)
            self._ask_async(text)
        except Exception as exc:
            self._append_line("system", f"Voice error: {exc}")

    def _ask_async(self, prompt_text: str) -> None:
        # Ensure only one active request to avoid overlapping updates
        if not self.active_request_lock.acquire(blocking=False):
            self._append_line("system", "Please wait for the current response...")
            return
        # Start an empty assistant bubble and stream tokens into it
        self._start_assistant_stream()
        threading.Thread(target=self._worker_stream_request, args=(prompt_text,), daemon=True).start()

    def _worker_stream_request(self, prompt_text: str) -> None:
        try:
            full_text = ""
            for chunk in self.bot.stream_ai_response(prompt_text):
                if chunk:
                    self.response_queue.put(("chunk", chunk))
                    full_text += chunk
            # If streaming yielded nothing, fall back to non-streaming once
            if not full_text:
                try:
                    fallback = self.bot.get_ai_response(prompt_text)
                    if fallback:
                        for ch in fallback:
                            self.response_queue.put(("chunk", ch))
                        full_text = fallback
                except Exception as fe:
                    print(f"Fallback error: {fe}")
            # Stream finished (or fallback completed)
            if full_text:
                try:
                    self.bot.speak(full_text)
                except Exception as e:
                    print(f"TTS Error: {e}")
            self.response_queue.put(("end", full_text))
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"Worker error: {error_msg}")
            self.response_queue.put(("end", "I'm having trouble connecting to my AI brain. Please check your DeepSeek API configuration and internet connection."))
        finally:
            self.active_request_lock.release()

    def _worker_request(self, prompt_text: str) -> None:
        try:
            reply = self.bot.get_ai_response(prompt_text)
            if reply:
                # Speak via TTS
                try:
                    self.bot.speak(reply)
                except Exception as e:
                    print(f"TTS Error: {e}")
                self.response_queue.put(reply)
            else:
                self.response_queue.put("I'm sorry, I couldn't process your request right now.")
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"Worker error: {error_msg}")
            self.response_queue.put("I'm having trouble connecting to my AI brain. Please check your DeepSeek API configuration and internet connection.")
        finally:
            self.active_request_lock.release()

    def _poll_queues(self) -> None:
        # Display any pending assistant replies
        try:
            while True:
                item = self.response_queue.get_nowait()
                if isinstance(item, tuple) and len(item) == 2:
                    kind, payload = item
                    if kind == "chunk":
                        self._append_to_assistant_stream(payload)
                    elif kind == "end":
                        # Finalize stream; if nothing was produced, show a fallback message
                        if payload:
                            # Ensure the final text is rendered (already appended chunk by chunk)
                            pass
                        else:
                            # Replace empty bubble with a fallback line
                            self._append_to_assistant_stream("I'm having trouble processing that right now.")
                        self._end_assistant_stream()
                else:
                    # Backward compatibility: full reply string
                    self._append_line("assistant", str(item))
        except queue.Empty:
            pass
        # Continue polling
        self.root.after(100, self._poll_queues)

    # Scroll/resize helpers
    def _on_frame_configure(self) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Ensure inner frame width matches canvas width
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_canvas_configure(self, event) -> None:
        # Update window width when canvas resizes
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _test_ai_connection(self) -> None:
        """Test AI connection on startup"""
        try:
            # Test DeepSeek API connection
            if not hasattr(self.bot, 'deepseek_api_key') or not self.bot.deepseek_api_key:
                self._append_line("system", "⚠️ DeepSeek API key not found. Please check your .env file.")
                return
            
            # Test with a simple API call
            try:
                headers = {
                    "Authorization": f"Bearer {self.bot.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.bot.model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                }
                
                response = requests.post(
                    self.bot.api_url,
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self._append_line("system", f"✅ Connected to DeepSeek API")
                    self._append_line("system", f"🤖 Using model: {self.bot.model}")
                elif response.status_code == 402:
                    self._append_line("system", "⚠️ DeepSeek API: Insufficient balance")
                    self._append_line("system", "Please add credits to your DeepSeek account")
                else:
                    self._append_line("system", f"⚠️ DeepSeek API issue: HTTP {response.status_code}")
                    self._append_line("system", f"Response: {response.text[:100]}...")
                    
            except requests.RequestException as e:
                self._append_line("system", f"❌ Cannot connect to DeepSeek API: {e}")
                self._append_line("system", "Please check your internet connection and API key.")
                
        except Exception as e:
            self._append_line("system", f"Connection test failed: {e}")


def main() -> None:
    root = tk.Tk()
    app = HoloBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


