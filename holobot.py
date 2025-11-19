#!/usr/bin/env python3
"""
HoloBot - A Python-based AI chatbot for holographic assistant project
Features: DeepSeek API integration, speech recognition, text-to-speech, conversation memory
"""

import os
import json
import time
import threading
import requests
from typing import List, Dict, Any
import logging

# Third-party imports
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HoloBot:
    """
    A holographic AI assistant with voice interaction capabilities
    """
    
    def __init__(self):
        """Initialize the HoloBot with all required components"""
        # Load environment variables from multiple locations
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try script's directory first (most reliable)
        script_env_path = os.path.join(script_dir, '.env')
        if os.path.exists(script_env_path):
            load_dotenv(script_env_path, override=True)
        
        # Try current working directory
        cwd_env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(cwd_env_path):
            load_dotenv(cwd_env_path, override=True)
        
        # Also try without path (default behavior)
        load_dotenv(override=False)
        
        # Try virtual environment directory relative to script
        venv_env_path = os.path.join(script_dir, '.venv', '.env')
        if os.path.exists(venv_env_path):
            load_dotenv(venv_env_path, override=True)
        
        # Also try virtual environment in current working directory
        cwd_venv_env = os.path.join(os.getcwd(), '.venv', '.env')
        if os.path.exists(cwd_venv_env):
            load_dotenv(cwd_venv_env, override=True)
        
        # AI Configuration - DeepSeek API
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.deepseek_api_key:
            # Provide helpful error message with paths checked
            checked_paths = [
                os.path.abspath('.env'),
                script_env_path,
                venv_env_path,
                cwd_venv_env
            ]
            error_msg = (
                "DEEPSEEK_API_KEY environment variable is required.\n"
                "Please set it in your .env file or environment variables.\n"
                f"Checked paths: {', '.join([p for p in checked_paths if p])}"
            )
            raise ValueError(error_msg)
        
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        self.max_api_retries = int(os.getenv('DEEPSEEK_MAX_RETRIES', '3'))
        self.base_backoff_seconds = float(os.getenv('DEEPSEEK_BASE_BACKOFF', '1.0'))
        self.request_timeout_seconds = float(os.getenv('DEEPSEEK_TIMEOUT', '120'))
        
        # DeepSeek API configuration
        self.api_key = self.deepseek_api_key
        self.api_url = f"{self.base_url}/v1/chat/completions"
        
        logger.info("Using DeepSeek API")
        
        # Conversation memory
        self.messages: List[Dict[str, str]] = [
            {
                "role": "system", 
                "content": "You are HoloBot, a friendly holographic AI assistant. You help users with various tasks and maintain a conversational, helpful tone. Keep responses concise but informative."
            }
        ]
        
        # Memory file for persistence
        self.memory_file = "memory.json"
        
        # Wake word
        self.wake_word = "hey holo"
        
        # Initialize speech recognition (graceful fallback if PyAudio missing)
        self.voice_input_enabled = True
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        except Exception as e:
            logger.error(f"Voice input unavailable: {e}")
            self.voice_input_enabled = False
        
        # Initialize text-to-speech (graceful fallback if engine missing)
        self.voice_output_enabled = True
        try:
            self.tts_engine = pyttsx3.init()
            self._setup_tts()
        except Exception as e:
            logger.error(f"Text-to-speech unavailable: {e}")
            self.voice_output_enabled = False
        
        # Load previous conversation memory
        self._load_memory()
        
        # Conversation memory limit (to control API costs)
        self.max_memory_exchanges = 15
        
        logger.info("HoloBot initialized successfully!")
        # Track conversation for DeepSeek API
        self.conversation_history = []
    
    def _setup_tts(self):
        """Configure text-to-speech engine settings"""
        voices = self.tts_engine.getProperty('voices')
        
        # Try to set a female voice if available
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate and volume
        self.tts_engine.setProperty('rate', 180)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        logger.info("Text-to-speech engine configured")

    def _format_messages_for_deepseek(self) -> List[Dict[str, str]]:
        """Format conversation messages for DeepSeek API"""
        formatted_messages = []
        
        for message in self.messages:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return formatted_messages
    
    def _load_memory(self):
        """Load conversation memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    saved_messages = json.load(f)
                    # Only load user and assistant messages, not system message
                    for msg in saved_messages:
                        if msg['role'] in ['user', 'assistant']:
                            self.messages.append(msg)
                logger.info(f"Loaded {len(saved_messages)} previous messages from memory")
        except Exception as e:
            logger.warning(f"Could not load memory file: {e}")
    
    def _save_memory(self):
        """Save conversation memory to file"""
        try:
            # Save only user and assistant messages (exclude system message)
            memory_messages = [msg for msg in self.messages if msg['role'] in ['user', 'assistant']]
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_messages, f, indent=2, ensure_ascii=False)
            logger.info("Conversation memory saved")
        except Exception as e:
            logger.error(f"Could not save memory: {e}")
    
    def _truncate_memory(self):
        """Keep only the last N exchanges to control API costs"""
        if len(self.messages) > self.max_memory_exchanges * 2 + 1:  # +1 for system message
            # Keep system message + last N exchanges
            self.messages = [self.messages[0]] + self.messages[-(self.max_memory_exchanges * 2):]
            logger.info("Conversation memory truncated")
    
    def speak(self, text: str):
        """Convert text to speech and speak it out loud"""
        try:
            logger.info(f"HoloBot speaking: {text}")
            if self.voice_output_enabled:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                print(f"HoloBot: {text}")
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
    
    def listen_for_wake_word(self) -> bool:
        """Listen for the wake word 'hey holo'"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening for wake word...")
                
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                # Recognize speech
                text = self.recognizer.recognize_google(audio).lower()
                logger.info(f"Heard: {text}")
                
                # Check for wake word
                if self.wake_word in text:
                    logger.info("Wake word detected!")
                    return True
                else:
                    logger.info("Wake word not detected")
                    return False
                    
        except sr.WaitTimeoutError:
            logger.info("No speech detected within timeout")
            return False
        except sr.UnknownValueError:
            logger.info("Could not understand audio")
            return False
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in wake word detection: {e}")
            return False
    
    def listen_for_input(self) -> str:
        """Listen for user input after wake word is detected"""
        try:
            with self.microphone as source:
                logger.info("Listening for your input...")
                # Listen for audio with longer timeout
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                
                # Recognize speech
                text = self.recognizer.recognize_google(audio)
                logger.info(f"User said: {text}")
                return text
                
        except sr.WaitTimeoutError:
            logger.info("No speech detected within timeout")
            return ""
        except sr.UnknownValueError:
            logger.info("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            return ""
    
    def get_ai_response(self, user_input: str) -> str:
        """Get response from DeepSeek API"""
        try:
            # Add user message to conversation
            self.messages.append({"role": "user", "content": user_input})
            
            # Truncate memory if needed
            self._truncate_memory()
            
            # Prepare messages for DeepSeek API
            formatted_messages = self._format_messages_for_deepseek()
            
            # Retry loop for transient errors
            last_error = None
            for attempt_index in range(self.max_api_retries + 1):
                try:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": self.model,
                        "messages": formatted_messages,
                        "temperature": 0.7,
                        "max_tokens": 512
                    }
                    
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=self.request_timeout_seconds
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_response = result['choices'][0]['message']['content'].strip()
                        
                        # Add assistant response to conversation
                        self.messages.append({"role": "assistant", "content": assistant_response})
                        # Save memory
                        self._save_memory()
                        return assistant_response
                    else:
                        raise requests.RequestException(f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as api_error:
                    last_error = api_error
                    # If last attempt, break and handle below
                    if attempt_index >= self.max_api_retries:
                        break
                    # Exponential backoff with jitter
                    sleep_seconds = self.base_backoff_seconds * (2 ** attempt_index)
                    jitter = 0.25 * sleep_seconds
                    delay = max(0.1, sleep_seconds + (jitter if attempt_index % 2 == 0 else -jitter))
                    logger.info(f"DeepSeek API error (attempt {attempt_index + 1}/{self.max_api_retries + 1}). Backing off {delay:.2f}s...")
                    time.sleep(delay)
            
            # If we get here, retries exhausted
            logger.error(f"DeepSeek API error after retries: {last_error}")
            return "I'm having trouble connecting to my AI brain right now. Please check your internet connection and try again."
        except Exception as e:
            logger.error(f"Unexpected error getting AI response: {e}")
            return "I encountered an unexpected error. Please try again."
    
    def stream_ai_response(self, user_input: str):
        """Stream response from DeepSeek API, yielding token chunks as they arrive."""
        try:
            # Add user message and prepare messages
            self.messages.append({"role": "user", "content": user_input})
            self._truncate_memory()
            formatted_messages = self._format_messages_for_deepseek()

            accumulated_tokens = []

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": 0.7,
                "max_tokens": 512,
                "stream": True
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.request_timeout_seconds,
                stream=True
            )

            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        line = line[6:]  # Remove 'data: ' prefix
                        if line.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(line)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    token = delta['content']
                                    accumulated_tokens.append(token)
                                    yield token
                        except json.JSONDecodeError:
                            continue

            assistant_response = ("".join(accumulated_tokens)).strip()
            if assistant_response:
                self.messages.append({"role": "assistant", "content": assistant_response})
                self._save_memory()
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            # Record a brief failure message so the conversation remains coherent
            try:
                self.messages.append({"role": "assistant", "content": "I'm having trouble generating a response right now."})
                self._save_memory()
            except Exception:
                pass
            return

    
    def should_exit(self, user_input: str) -> bool:
        """Check if user wants to exit the conversation"""
        exit_phrases = ["bye", "exit", "goodbye", "see you later", "quit", "stop"]
        return any(phrase in user_input.lower() for phrase in exit_phrases)
    
    def run(self):
        """Main loop for the HoloBot"""
        logger.info("HoloBot is now active! Say 'Hey Holo' to start a conversation.")
        self.speak("Hello! I'm HoloBot, your holographic assistant. Say 'Hey Holo' to start talking to me.")
        
        # If voice input is unavailable, fall back to text mode
        if not self.voice_input_enabled:
            print("[Voice input unavailable. Falling back to text chat mode.]")
            try:
                while True:
                    user_input = input("You: ").strip()
                    if not user_input:
                        print("(Empty input. Please type something.)")
                        continue
                    if self.should_exit(user_input):
                        self.speak("Goodbye! It was great talking to you. See you next time!")
                        break
                    response = self.get_ai_response(user_input)
                    self.speak(response)
            except KeyboardInterrupt:
                logger.info("HoloBot interrupted by user")
                self.speak("Goodbye! See you next time!")
            finally:
                self._save_memory()
            return
        
        try:
            while True:
                # Listen for wake word
                if self.listen_for_wake_word():
                    self.speak("Yes, I'm listening!")
                    
                    # Listen for user input
                    user_input = self.listen_for_input()
                    
                    if user_input:
                        # Check for exit commands
                        if self.should_exit(user_input):
                            self.speak("Goodbye! It was great talking to you. See you next time!")
                            logger.info("User requested exit")
                            break
                        
                        # Get AI response
                        logger.info("Getting AI response...")
                        response = self.get_ai_response(user_input)
                        
                        # Speak the response
                        self.speak(response)
                    else:
                        self.speak("Sorry, I didn't catch that. Please try again.")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("HoloBot interrupted by user")
            self.speak("Goodbye! See you next time!")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            self.speak("I encountered an error and need to restart. Goodbye!")
        finally:
            # Save memory before exiting
            self._save_memory()
            logger.info("HoloBot shutting down")

def main():
    """Main function to run the HoloBot"""
    print("🤖 Initializing HoloBot...")
    
    # Ensure .env is loaded
    load_dotenv()
    
    # Check if DeepSeek API key is configured
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_api_key:
        print("❌ Error: DEEPSEEK_API_KEY environment variable is required")
        print("Please set your DeepSeek API key in the .env file")
        return
    
    try:
        # Create and run the bot
        bot = HoloBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start HoloBot: {e}")
        print(f"❌ Error starting HoloBot: {e}")

if __name__ == "__main__":
    main()
