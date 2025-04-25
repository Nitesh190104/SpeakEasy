# SpeakEasy - AI Language Practice Bot

SpeakEasy is an interactive web application that helps users practice speaking foreign languages with AI-powered feedback. It provides conversation prompts, analyzes speech responses, and offers detailed feedback on grammar, pronunciation, fluency, and vocabulary.

## Features

- Multi-language Support: Practice English, Spanish, French, and German
- AI-Powered Feedback: Get detailed analysis of your speech using Google's Gemini AI
- Daily Vocabulary: Learn 5 new words every day in your target language
- Progress Tracking: Track your improvement with session history and scores
- Gamification: Earn XP, level up, and unlock achievements
- Streaks: Maintain practice streaks to build consistency

## Technologies Used

### Backend
- Python
- Flask (web framework)
- Google Gemini AI (for speech analysis)
- dotenv (for environment variables)

### Frontend
- HTML5
- Tailwind CSS (for styling)
- JavaScript (for interactive features)
- Web Speech API (for speech recognition)

### Data
- Mock database (in-memory storage - would be replaced with a real database in production)

## Installation

1. Install dependencies:
   ```bash
  ```
  flask==3.0.2
  python-dotenv==1.0.1
  google-generativeai==0.3.2
  uuid==1.30
  ```

2. Create a `.env` file in the root directory with your Google Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSyB7rew-wWsKdMzM6oiGsYI54XTZA5RsLUg 
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure

```
speakeasy/
│
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not included in repo)
│
├── static/               # Static files (CSS, JS, images)
│
└── templates/            # HTML templates
    ├── layout.html       # Base template
    ├── index.html        # Home page
    ├── practice.html     # Practice interface
    ├── progress.html     # Progress tracking
    └── vocabulary.html   # Vocabulary learning
```

## Configuration

The application can be configured through environment variables:

- `GEMINI_API_KEY`: Required - Your Google Gemini API key
- `FLASK_SECRET_KEY`: Optional - Secret key for Flask sessions (defaults to random value)

## Usage

1. Home Page: Select a language to practice from the home screen
2. Practice Interface:
   - Get a conversation prompt
   - Click the microphone button to record your response
   - Receive detailed feedback on your speech
3. Vocabulary: Learn new words and mark them as learned
4. Progress: View your practice history, achievements, and statistics

## Future Improvements

- Add more languages
- Implement user accounts with persistent storage
- Add more detailed pronunciation analysis
- Include conversation simulations
- Add mobile app version

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini for the AI analysis capabilities
- Tailwind CSS for the styling framework
- Flask for the web framework
