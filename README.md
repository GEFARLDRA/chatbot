# HoloBot - Holographic AI Assistant

A Python-based AI chatbot with voice interaction capabilities for your holographic assistant project, now powered by DeepSeek AI.

## Features

- 🤖 **DeepSeek AI Integration**: Advanced AI responses using DeepSeek's chat models
- 🎤 **Speech Recognition**: Voice input with wake word detection ("Hey Holo")
- 🔊 **Text-to-Speech**: Offline voice output with customizable settings
- 🧠 **Conversation Memory**: Maintains context across interactions
- 💾 **Persistence**: Saves conversation history to memory.json
- 🚪 **Graceful Exit**: Clean shutdown with "bye" or "exit" commands
- ⚡ **Error Handling**: Robust error handling for various scenarios
- 🌐 **Cloud AI**: Powered by DeepSeek's advanced language models

## Installation

1. **Get DeepSeek API Key:**
   - Sign up at: https://platform.deepseek.com/
   - Generate an API key from your dashboard

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure HoloBot:**
   - Copy `env_template.txt` to `.env`
   - Edit `.env` to set your API key:
     ```
     DEEPSEEK_API_KEY=your_api_key_here
     DEEPSEEK_MODEL=deepseek-chat
     DEEPSEEK_BASE_URL=https://api.deepseek.com
     ```

## Usage

1. **Run the chatbot:**
   ```bash
   python holobot.py
   ```

2. **Interact with HoloBot:**
   - Say "Hey Holo" to activate the assistant
   - Speak your question or request
   - HoloBot will respond with voice and text
   - Say "bye" or "exit" to end the conversation

## Configuration

### Voice Settings
The TTS engine is configured with:
- **Speech Rate**: 180 words per minute
- **Volume**: 90%
- **Voice**: Automatically selects a female voice if available

### Memory Management
- **Memory Limit**: Last 15 exchanges to control API costs
- **Persistence**: Conversation history saved to `memory.json`
- **Context**: Maintains conversation context for natural interactions

### Wake Word
- **Default**: "Hey Holo"
- **Customization**: Modify the `wake_word` variable in the code

## Troubleshooting

### Common Issues

1. **"DEEPSEEK_API_KEY not found"**
   - Make sure your `.env` file contains the correct API key
   - Verify the API key is valid and has sufficient credits
   - Check that the `.env` file is in the same directory as the script

2. **"Insufficient Balance" or API errors**
   - Check your DeepSeek account balance
   - Verify your API key has proper permissions
   - Ensure you have sufficient credits for API calls

3. **Microphone not working**
   - Check microphone permissions
   - Ensure microphone is not being used by other applications

4. **Speech recognition errors**
   - Check internet connection (uses Google Speech Recognition)
   - Speak clearly and avoid background noise

5. **TTS not working**
   - On Linux, you may need: `sudo apt-get install espeak`
   - On Windows, ensure you have a compatible TTS engine

6. **Slow responses**
   - Check your internet connection speed
   - Increase `DEEPSEEK_TIMEOUT` in `.env` for slower connections
   - Consider using `deepseek-coder` model for faster responses

### Performance Tips

- Speak clearly and avoid background noise
- Wait for the wake word confirmation before speaking
- Keep conversations focused to maintain context
- The bot automatically manages memory to control API costs
- Monitor your DeepSeek account usage to avoid exceeding limits

## File Structure

```
chatbot/
├── holobot.py          # Main chatbot script
├── requirements.txt    # Python dependencies
├── env_template.txt    # Environment variables template
├── README.md          # This file
└── memory.json        # Conversation memory (created automatically)
```

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve HoloBot!
