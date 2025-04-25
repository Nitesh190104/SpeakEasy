from flask import Flask, render_template, request, jsonify, session
import os
import json
import random
from datetime import datetime, date
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY environment variable is not set")
logger.info("Gemini API configured successfully")

genai.configure(api_key=GEMINI_API_KEY)

# Configure default safety settings
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Mock database - in a real app, you would use a proper database
USERS_DB = {}
PROMPTS = {
    "english": [
        "Tell me about your favorite hobby.",
        "Describe your ideal vacation.",
        "What did you do last weekend?",
        "Talk about your favorite movie or TV show.",
        "Describe your morning routine."
    ],
    "spanish": [
        "Háblame de tu pasatiempo favorito.",
        "Describe tus vacaciones ideales.",
        "¿Qué hiciste el fin de semana pasado?",
        "Habla sobre tu película o programa de televisión favorito.",
        "Describe tu rutina matutina."
    ],
    "french": [
        "Parle-moi de ton passe-temps préféré.",
        "Décris tes vacances idéales.",
        "Qu'as-tu fait le week-end dernier ?",
        "Parle de ton film ou émission de télévision préféré.",
        "Décris ta routine matinale."
    ],
    "german": [
        "Erzähl mir von deinem Lieblingshobby.",
        "Beschreibe deinen idealen Urlaub.",
        "Was hast du letztes Wochenende gemacht?",
        "Sprich über deinen Lieblingsfilm oder deine Lieblingssendung.",
        "Beschreibe deine Morgenroutine."
    ]
}

# Daily vocabulary words
VOCABULARY = {
    "english": [
        {"word": "Serendipity", "definition": "The occurrence of events by chance in a happy or beneficial way", "example": "Finding a perfect book while looking for something else was pure serendipity."},
        {"word": "Eloquent", "definition": "Fluent or persuasive in speaking or writing", "example": "Her eloquent speech moved the entire audience."},
        {"word": "Resilience", "definition": "The capacity to recover quickly from difficulties", "example": "His resilience helped him overcome many challenges in life."},
        {"word": "Meticulous", "definition": "Showing great attention to detail", "example": "She is meticulous about keeping records of all transactions."},
        {"word": "Pragmatic", "definition": "Dealing with things sensibly and realistically", "example": "We need a pragmatic approach to solve this problem."},
        {"word": "Ephemeral", "definition": "Lasting for a very short time", "example": "The beauty of cherry blossoms is ephemeral, lasting only a few days."},
        {"word": "Ambivalent", "definition": "Having mixed feelings or contradictory ideas", "example": "She felt ambivalent about moving to a new city."},
        {"word": "Ubiquitous", "definition": "Present, appearing, or found everywhere", "example": "Smartphones have become ubiquitous in modern society."},
        {"word": "Paradigm", "definition": "A typical example or pattern of something", "example": "This discovery represents a paradigm shift in our understanding."},
        {"word": "Juxtapose", "definition": "Place or deal with close together for contrasting effect", "example": "The article juxtaposes the lives of the rich and the poor."}
    ],
    "spanish": [
        {"word": "Efímero", "definition": "Que dura poco tiempo o es pasajero", "example": "La belleza de las flores es efímera."},
        {"word": "Serendipia", "definition": "Hallazgo valioso que se produce de manera accidental", "example": "Conocer a mi mejor amigo fue una serendipia."},
        {"word": "Resiliencia", "definition": "Capacidad para adaptarse a situaciones adversas", "example": "Su resiliencia le permitió superar momentos difíciles."},
        {"word": "Meticuloso", "definition": "Que muestra gran atención al detalle", "example": "Es un trabajador meticuloso que nunca comete errores."},
        {"word": "Pragmático", "definition": "Que se basa en la práctica y utilidad", "example": "Necesitamos un enfoque pragmático para resolver este problema."},
        {"word": "Elocuente", "definition": "Que habla o se expresa con facilidad y de modo persuasivo", "example": "Su discurso elocuente conmovió a todos."},
        {"word": "Ambivalente", "definition": "Que presenta dos interpretaciones o valores diferentes", "example": "Tengo sentimientos ambivalentes sobre ese tema."},
        {"word": "Ubicuo", "definition": "Que está presente en todas partes al mismo tiempo", "example": "La tecnología es ubicua en nuestra sociedad moderna."},
        {"word": "Paradigma", "definition": "Ejemplo o modelo de algo", "example": "Este descubrimiento representa un cambio de paradigma."},
        {"word": "Yuxtaponer", "definition": "Poner una cosa junto a otra", "example": "El artista yuxtapone colores brillantes y oscuros."}
    ],
    "french": [
        {"word": "Sérendipité", "definition": "Découverte heureuse faite par hasard", "example": "Trouver ce livre rare était une sérendipité."},
        {"word": "Éloquent", "definition": "Qui s'exprime avec aisance et de façon persuasive", "example": "Son discours éloquent a ému tout le public."},
        {"word": "Résilience", "definition": "Capacité à surmonter les chocs et les traumatismes", "example": "Sa résilience lui a permis de surmonter cette épreuve."},
        {"word": "Méticuleux", "definition": "Qui montre un grand souci du détail", "example": "Il est méticuleux dans son travail."},
        {"word": "Pragmatique", "definition": "Qui est orienté vers l'action pratique", "example": "Nous avons besoin d'une approche pragmatique."},
        {"word": "Éphémère", "definition": "Qui ne dure qu'un temps très court", "example": "La beauté des fleurs est éphémère."},
        {"word": "Ambivalent", "definition": "Qui présente deux aspects ou valeurs contradictoires", "example": "J'ai des sentiments ambivalents à ce sujet."},
        {"word": "Ubiquitaire", "definition": "Qui est présent partout", "example": "Les smartphones sont devenus ubiquitaires."},
        {"word": "Paradigme", "definition": "Modèle de référence", "example": "Cette découverte représente un changement de paradigme."},
        {"word": "Juxtaposer", "definition": "Placer des éléments côte à côte", "example": "L'artiste juxtapose des couleurs contrastées."}
    ],
    "german": [
        {"word": "Serendipität", "definition": "Glücklicher Zufall, bei dem man etwas findet, was man nicht gesucht hat", "example": "Die Entdeckung war reine Serendipität."},
        {"word": "Eloquent", "definition": "Redegewandt, ausdrucksstark", "example": "Seine eloquente Rede beeindruckte alle Anwesenden."},
        {"word": "Resilienz", "definition": "Psychische Widerstandsfähigkeit", "example": "Ihre Resilienz half ihr, die schwierige Zeit zu überstehen."},
        {"word": "Akribisch", "definition": "Sehr genau und sorgfältig", "example": "Er arbeitet akribisch an jedem Detail."},
        {"word": "Pragmatisch", "definition": "Praktisch orientiert, sachbezogen", "example": "Wir brauchen einen pragmatischen Ansatz."},
        {"word": "Ephemer", "definition": "Kurzlebig, flüchtig", "example": "Die Schönheit der Kirschblüten ist ephemer."},
        {"word": "Ambivalent", "definition": "Zwiespältig, gegensätzliche Gefühle habend", "example": "Ich bin ambivalent, was dieses Thema betrifft."},
        {"word": "Ubiquitär", "definition": "Allgegenwärtig, überall vorkommend", "example": "Smartphones sind heutzutage ubiquitär."},
        {"word": "Paradigma", "definition": "Denkmuster, Beispiel", "example": "Diese Entdeckung stellt einen Paradigmenwechsel dar."},
        {"word": "Juxtaponieren", "definition": "Nebeneinanderstellen zum Vergleich", "example": "Der Künstler juxtaponiert helle und dunkle Farben."}
    ]
}

# Achievement badges
ACHIEVEMENTS = [
    {"id": "first_practice", "name": "First Steps", "description": "Complete your first practice session", "icon": "🎯"},
    {"id": "five_practices", "name": "Getting Fluent", "description": "Complete 5 practice sessions", "icon": "🔥"},
    {"id": "perfect_score", "name": "Perfect Pronunciation", "description": "Get a perfect score on a practice", "icon": "🌟"},
    {"id": "three_day_streak", "name": "Consistency is Key", "description": "Practice for 3 days in a row", "icon": "📆"},
    {"id": "vocabulary_master", "name": "Word Wizard", "description": "Learn 10 new vocabulary words", "icon": "📚"},
    {"id": "multilingual", "name": "Global Citizen", "description": "Practice in at least 2 different languages", "icon": "🌍"}
]

@app.route('/')
def home():
    # Generate a user ID if not present
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        USERS_DB[session['user_id']] = {
            'progress': [],
            'sessions': 0,
            'total_score': 0,
            'achievements': [],
            'learned_words': [],
            'last_practice_date': None,
            'streak': 0,
            'xp': 0,
            'level': 1,
            'languages_practiced': set()
        }
    return render_template('index.html')

@app.route('/practice')
def practice():
    language = request.args.get('language', 'english')
    
    # Update user data for streaks
    user_id = session.get('user_id')
    if user_id and user_id in USERS_DB:
        today = date.today().isoformat()
        last_date = USERS_DB[user_id].get('last_practice_date')
        
        # Add language to practiced languages
        if language not in USERS_DB[user_id]['languages_practiced']:
            USERS_DB[user_id]['languages_practiced'].add(language)
            
            # Check for multilingual achievement
            if len(USERS_DB[user_id]['languages_practiced']) >= 2:
                add_achievement(user_id, "multilingual")
    
    return render_template('practice.html', language=language)

@app.route('/progress')
def progress():
    user_id = session.get('user_id')
    if not user_id or user_id not in USERS_DB:
        return render_template('progress.html', progress=None)
    
    return render_template('progress.html', progress=USERS_DB[user_id], achievements=ACHIEVEMENTS)

@app.route('/vocabulary')
def vocabulary():
    language = request.args.get('language', 'english')
    user_id = session.get('user_id')
    
    # Get user's learned words
    learned_words = []
    if user_id and user_id in USERS_DB:
        learned_words = USERS_DB[user_id]['learned_words']
    
    # Get today's words (limit to 5)
    today_words = VOCABULARY.get(language, [])[:5]
    
    return render_template('vocabulary.html', language=language, vocabulary=today_words, learned_words=learned_words)

@app.route('/api/prompt', methods=['GET'])
def get_prompt():
    language = request.args.get('language', 'english')
    if language not in PROMPTS:
        language = 'english'
    
    prompt = random.choice(PROMPTS[language])
    return jsonify({'prompt': prompt, 'language': language})

@app.route('/api/feedback', methods=['POST'])
def get_feedback():
    try:
        data = request.json
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({'error': 'No data provided'}), 400
            
        transcript = data.get('transcript', '')
        language = data.get('language', 'english')
        prompt = data.get('prompt', '')
        
        if not transcript:
            logger.error("No transcript provided in request")
            return jsonify({'error': 'No transcript provided'}), 400
            
        logger.info(f"Analyzing speech in {language} for prompt: {prompt}")
        logger.info(f"Transcript: {transcript}")
        
        # Use Gemini to analyze speech
        feedback = analyze_speech_with_gemini(transcript, prompt, language)
        
        # Store progress data and update achievements
        user_id = session.get('user_id')
        if user_id and user_id in USERS_DB:
            try:
                # Update session count
                USERS_DB[user_id]['sessions'] += 1
                
                # Check for first practice achievement
                if USERS_DB[user_id]['sessions'] == 1:
                    add_achievement(user_id, "first_practice")
                
                # Check for five practices achievement
                if USERS_DB[user_id]['sessions'] == 5:
                    add_achievement(user_id, "five_practices")
                
                # Update score and check for perfect score
                USERS_DB[user_id]['total_score'] += feedback['score']
                if feedback['score'] >= 9.5:
                    add_achievement(user_id, "perfect_score")
                
                # Update XP and level
                xp_gained = int(feedback['score'] * 10)
                USERS_DB[user_id]['xp'] += xp_gained
                
                # Level up logic (100 XP per level)
                new_level = (USERS_DB[user_id]['xp'] // 100) + 1
                level_up = new_level > USERS_DB[user_id]['level']
                USERS_DB[user_id]['level'] = new_level
                
                # Update streak
                today = date.today().isoformat()
                last_date = USERS_DB[user_id].get('last_practice_date')
                
                if last_date:
                    yesterday = (datetime.strptime(today, '%Y-%m-%d') - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    if last_date == yesterday:
                        USERS_DB[user_id]['streak'] += 1
                        
                        # Check for three-day streak achievement
                        if USERS_DB[user_id]['streak'] == 3:
                            add_achievement(user_id, "three_day_streak")
                    elif last_date != today:
                        # Reset streak if not consecutive days
                        USERS_DB[user_id]['streak'] = 1
                else:
                    USERS_DB[user_id]['streak'] = 1
                    
                USERS_DB[user_id]['last_practice_date'] = today
                
                # Store the practice session
                USERS_DB[user_id]['progress'].append({
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'language': language,
                    'prompt': prompt,
                    'transcript': transcript,
                    'score': feedback['score'],
                    'feedback': feedback['message'],
                    'xp_gained': xp_gained
                })
                
                # Add level up information to the response if applicable
                feedback['level_up'] = level_up
                feedback['new_level'] = new_level if level_up else None
                feedback['xp_gained'] = xp_gained
                feedback['total_xp'] = USERS_DB[user_id]['xp']
                feedback['streak'] = USERS_DB[user_id]['streak']
                
            except Exception as e:
                logger.error(f"Error updating user progress: {str(e)}")
                # Continue with the response even if progress update fails
        
        logger.info("Successfully generated feedback")
        return jsonify(feedback)
        
    except Exception as e:
        logger.error(f"Error in feedback endpoint: {str(e)}")
        return jsonify({
            'error': 'An error occurred while analyzing your response',
            'message': 'Please try again'
        }), 500

@app.route('/api/learn-word', methods=['POST'])
def learn_word():
    data = request.json
    word = data.get('word')
    
    user_id = session.get('user_id')
    if user_id and user_id in USERS_DB and word:
        if word not in USERS_DB[user_id]['learned_words']:
            USERS_DB[user_id]['learned_words'].append(word)
            USERS_DB[user_id]['xp'] += 5  # Award XP for learning a word
            
            # Check for vocabulary master achievement
            if len(USERS_DB[user_id]['learned_words']) >= 10:
                add_achievement(user_id, "vocabulary_master")
            
            return jsonify({'success': True, 'message': f'Added "{word}" to your learned words!', 'xp_gained': 5})
    
    return jsonify({'success': False, 'message': 'Failed to add word'})

def add_achievement(user_id, achievement_id):
    """Add an achievement to the user's profile if they don't already have it"""
    if user_id in USERS_DB:
        if achievement_id not in USERS_DB[user_id]['achievements']:
            USERS_DB[user_id]['achievements'].append(achievement_id)
            # Award XP for achievements
            USERS_DB[user_id]['xp'] += 50

def analyze_speech_with_gemini(transcript, prompt, language):
    """
    Use Google's Gemini Pro model to analyze speech with detailed feedback
    """
    try:
        if not GEMINI_API_KEY:
            print("No API key available, falling back to mock implementation")
            return mock_analyze_speech(transcript, prompt, language)
            
        # Configure the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create the prompt for Gemini
        analysis_prompt = f"""You are a language learning assistant. Analyze this speech response and provide detailed feedback with specific examples and improvements.

Language: {language}
Original Prompt: "{prompt}"
Student's Response: "{transcript}"

Analyze the response and provide detailed feedback in the following JSON format exactly:
{{
    "grammar_score": <number between 0-10>,
    "fluency_score": <number between 0-10>,
    "pronunciation_score": <number between 0-10>,
    "vocabulary_score": <number between 0-10>,
    "overall_score": <average of all scores>,
    "grammar_feedback": {{
        "issues": ["<specific grammar mistake 1>", "<specific grammar mistake 2>"],
        "corrections": ["<corrected version 1>", "<corrected version 2>"],
        "explanation": "<brief explanation of the grammar rules>"
    }},
    "fluency_feedback": {{
        "issues": ["<specific fluency issue 1>", "<specific fluency issue 2>"],
        "improvements": ["<how to improve 1>", "<how to improve 2>"]
    }},
    "pronunciation_feedback": {{
        "difficult_words": ["<word 1>", "<word 2>"],
        "correct_pronunciation": ["<pronunciation guide 1>", "<pronunciation guide 2>"]
    }},
    "vocabulary_feedback": {{
        "basic_words_used": ["<word 1>", "<word 2>"],
        "suggested_alternatives": ["<better word 1>", "<better word 2>"],
        "context": "<explanation of when to use these alternatives>"
    }},
    "overall_feedback": "<2-3 sentences of general feedback>",
    "suggestions": [
        "<specific actionable suggestion 1>",
        "<specific actionable suggestion 2>",
        "<specific actionable suggestion 3>"
    ]
}}

Important: 
1. Provide specific examples from the student's response
2. Give clear, actionable corrections
3. Include brief explanations of rules or patterns
4. Respond ONLY with the JSON object, no other text"""

        # Generate the analysis with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(analysis_prompt)
                response_text = response.text.strip()
                
                # Clean up the response text
                if "```json" in response_text:
                    json_content = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_content = response_text.split("```")[1].strip()
                else:
                    json_content = response_text
                
                # Parse JSON and validate required fields
                analysis = json.loads(json_content)
                required_fields = ['grammar_score', 'fluency_score', 'pronunciation_score', 
                                 'vocabulary_score', 'overall_score', 'grammar_feedback',
                                 'fluency_feedback', 'pronunciation_feedback', 
                                 'vocabulary_feedback', 'overall_feedback', 'suggestions']
                
                if all(field in analysis for field in required_fields):
                    # Format detailed feedback messages
                    grammar_msg = format_feedback_message(
                        analysis['grammar_feedback']['issues'],
                        analysis['grammar_feedback']['corrections'],
                        analysis['grammar_feedback']['explanation']
                    )
                    
                    fluency_msg = format_feedback_message(
                        analysis['fluency_feedback']['issues'],
                        analysis['fluency_feedback']['improvements']
                    )
                    
                    pronunciation_msg = format_pronunciation_feedback(
                        analysis['pronunciation_feedback']['difficult_words'],
                        analysis['pronunciation_feedback']['correct_pronunciation']
                    )
                    
                    vocabulary_msg = format_vocabulary_feedback(
                        analysis['vocabulary_feedback']['basic_words_used'],
                        analysis['vocabulary_feedback']['suggested_alternatives'],
                        analysis['vocabulary_feedback']['context']
                    )
                    
                    return {
                        'score': float(analysis['overall_score']),
                        'message': analysis['overall_feedback'],
                        'grammar': {
                            'score': float(analysis['grammar_score']),
                            'feedback': grammar_msg
                        },
                        'fluency': {
                            'score': float(analysis['fluency_score']),
                            'feedback': fluency_msg
                        },
                        'pronunciation': {
                            'score': float(analysis['pronunciation_score']),
                            'feedback': pronunciation_msg
                        },
                        'vocabulary': {
                            'score': float(analysis['vocabulary_score']),
                            'feedback': vocabulary_msg
                        },
                        'suggestions': analysis['suggestions']
                    }
                else:
                    print(f"Missing required fields in API response, attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise ValueError("Invalid API response format")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}")
        return mock_analyze_speech(transcript, prompt, language)

def format_feedback_message(issues, corrections, explanation=None):
    """Format feedback with issues and corrections"""
    message = ""
    for i, (issue, correction) in enumerate(zip(issues, corrections)):
        message += f"• Issue {i+1}: {issue}\n  Correction: {correction}\n"
    if explanation:
        message += f"\nNote: {explanation}"
    return message.strip()

def format_pronunciation_feedback(words, pronunciations):
    """Format pronunciation feedback with word guides"""
    message = "Focus on these words:\n"
    for word, pron in zip(words, pronunciations):
        message += f"• {word} → {pron}\n"
    return message.strip()

def format_vocabulary_feedback(basic_words, alternatives, context):
    """Format vocabulary feedback with alternatives and context"""
    message = "Consider using these alternatives:\n"
    for basic, better in zip(basic_words, alternatives):
        message += f"• Instead of '{basic}', try '{better}'\n"
    message += f"\nTip: {context}"
    return message.strip()

def mock_analyze_speech(transcript, prompt, language):
    """
    Mock AI analysis function with detailed feedback - used as fallback when Gemini API is unavailable
    """
    # Simple scoring based on transcript length and complexity
    word_count = len(transcript.split())
    
    # Base score on word count (more words = higher score, up to a point)
    base_score = min(word_count / 5, 10)
    
    # Adjust score based on variety of words (simple heuristic)
    unique_words = len(set(word.lower() for word in transcript.split()))
    vocabulary_score = min(unique_words / 3, 10)
    
    # Average the scores
    score = (base_score + vocabulary_score) / 2
    score = min(max(score, 0), 10)  # Ensure score is between 0 and 10
    
    # Generate detailed feedback based on score
    if score < 3:
        grammar_msg = format_feedback_message(
            ["Incomplete sentences", "Missing subject-verb agreement"],
            ["Form complete sentences with subject and verb", "Make sure verbs agree with their subjects"],
            "Remember to use complete sentences with proper structure: Subject + Verb + Object"
        )
        
        fluency_msg = format_feedback_message(
            ["Long pauses between words", "Hesitation sounds (um, uh)"],
            ["Practice speaking in shorter phrases first", "Record yourself and identify pause patterns"]
        )
        
        pronunciation_msg = format_pronunciation_feedback(
            ["hello", "practice"],
            ["heh-LOH", "PRAK-tis"]
        )
        
        vocabulary_msg = format_vocabulary_feedback(
            ["good", "nice"],
            ["excellent", "wonderful"],
            "Using more specific adjectives makes your speech more engaging and precise"
        )
        
        overall_feedback = "Keep practicing! Focus on forming complete sentences and speaking more confidently."
        suggestions = [
            "Record yourself speaking and listen for pauses",
            "Practice with simple, complete sentences first",
            "Use a dictionary to check word pronunciation"
        ]
        
    elif score < 7:
        grammar_msg = format_feedback_message(
            ["Occasional tense mixing", "Article usage"],
            ["Maintain consistent tense throughout", "Pay attention to a/an/the usage"],
            "Focus on maintaining consistent verb tenses in your speech"
        )
        
        fluency_msg = format_feedback_message(
            ["Some unnatural pauses", "Speed variations"],
            ["Practice linking words together", "Maintain a steady speaking pace"]
        )
        
        pronunciation_msg = format_pronunciation_feedback(
            ["vocabulary", "improvement"],
            ["voh-KAB-yuh-lair-ee", "im-PROOV-muhnt"]
        )
        
        vocabulary_msg = format_vocabulary_feedback(
            ["said", "big"],
            ["expressed", "substantial"],
            "Try incorporating more advanced vocabulary while maintaining natural speech"
        )
        
        overall_feedback = "Good effort! Your speech is improving. Focus on smoother delivery and more varied vocabulary."
        suggestions = [
            "Practice speaking at a consistent pace",
            "Try using synonyms for common words",
            "Work on linking words together smoothly"
        ]
        
    else:
        grammar_msg = format_feedback_message(
            ["Minor preposition usage", "Complex sentence structures"],
            ["Review preposition rules", "Break down complex thoughts into clear statements"],
            "Your grammar is strong - focus on fine-tuning complex expressions"
        )
        
        fluency_msg = format_feedback_message(
            ["Occasional rhythm breaks", "Natural flow"],
            ["Practice with longer passages", "Incorporate more idiomatic expressions"]
        )
        
        pronunciation_msg = format_pronunciation_feedback(
            ["sophisticated", "particularly"],
            ["suh-FIS-ti-kay-ted", "par-TIK-yuh-ler-lee"]
        )
        
        vocabulary_msg = format_vocabulary_feedback(
            ["interesting", "difficult"],
            ["intriguing", "challenging"],
            "Your vocabulary is good - try incorporating more idiomatic expressions"
        )
        
        overall_feedback = "Excellent work! Your speech is clear and well-structured. Focus on mastering more advanced expressions."
        suggestions = [
            "Practice with more complex topics",
            "Work on incorporating idiomatic expressions",
            "Try speaking at a faster pace while maintaining clarity"
        ]
    
    return {
        'score': round(score, 1),
        'message': overall_feedback,
        'grammar': {
            'score': round(min(score + random.uniform(-1, 1), 10), 1),
            'feedback': grammar_msg
        },
        'fluency': {
            'score': round(min(score + random.uniform(-1, 1), 10), 1),
            'feedback': fluency_msg
        },
        'pronunciation': {
            'score': round(min(score + random.uniform(-1, 1), 10), 1),
            'feedback': pronunciation_msg
        },
        'vocabulary': {
            'score': round(min(score + random.uniform(-1, 1), 10), 1),
            'feedback': vocabulary_msg
        },
        'suggestions': suggestions
    }

if __name__ == '__main__':
    app.run(debug=True)
