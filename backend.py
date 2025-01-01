from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

app = FastAPI()
analyzer = SentimentIntensityAnalyzer()


FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "actually", "sort of", "kind of", "I mean", "you see", "aah", "hmm"]

# User-customizable parameters
USER_PREFERENCES = {
    "User1": {
        "preferred_pace": "normal",
        "allowed_filler_words": [],
    },
    "User2": {
        "preferred_pace": "fast",
        "allowed_filler_words": ["like", "you know"],
    }
}

def detect_context(text):
    """Determine the context of the conversation based on keywords and tone."""
    formal_keywords = ["meeting", "project", "strategy", "client"]
    persuasive_keywords = ["buy", "convince", "persuade", "sell"]
    informal_keywords = ["hangout", "chill", "cool", "friends"]

    if any(word in text.lower() for word in formal_keywords):
        return "Formal"
    elif any(word in text.lower() for word in persuasive_keywords):
        return "Persuasive"
    elif any(word in text.lower() for word in informal_keywords):
        return "Informal"
    else:
        return "General"

def analyze_tone(text):
    """Analyze the tone of the input text using VADER."""
    sentiment = analyzer.polarity_scores(text)
    if sentiment['compound'] >= 0.05:
        return "Positive", sentiment['compound']
    elif sentiment['compound'] <= -0.05:
        return "Negative", sentiment['compound']
    else:
        return "Neutral", sentiment['compound']

def detect_filler_words(text, user):
    """Detect filler words in the text for a specific user."""
    words = re.findall(r'\b\w+\b', text.lower())
    allowed_filler_words = USER_PREFERENCES[user]["allowed_filler_words"]
    detected = [word for word in words if word in FILLER_WORDS and word not in allowed_filler_words]
    if detected:
        return f"Avoid using filler words: {', '.join(set(detected))}."
    else:
        return "No filler words detected."

def suggest_improvement(text, tone, context):
    """Suggest improvements based on tone and context."""
    if tone == "Negative":
        if context == "Formal":
            return "Reframe negative language to focus on solutions. For example, 'problem' can be rephrased as 'challenge to address.'"
        elif context == "Persuasive":
            return "Use positive framing to inspire confidence in your audience. Avoid words like 'fail' or 'difficult.'"
        else:
            return "Consider rephrasing with more optimistic language."
    elif tone == "Neutral":
        if context == "Formal":
            return "Consider making the tone more engaging by adding details or examples."
        elif context == "Persuasive":
            return "Add enthusiasm to make the statement more compelling."
        else:
            return "Neutral tone works, but adding warmth or enthusiasm could help."
    else:
        return "Great job! Your tone is positive. Keep it up."

def speaking_advice(context, user):
    """Provide general speaking advice based on context and user preferences."""
    pace = USER_PREFERENCES[user]["preferred_pace"]
    advice = {
        "Formal": [
            "Speak clearly and avoid unnecessary filler words.",
            "Maintain a steady pace for a professional tone.",
            "Use precise language to avoid misunderstandings."
        ],
        "Informal": [
            "Be natural and conversational.",
            "Don’t worry too much about minor pauses, they’re normal in casual chats.",
            "Smile and keep your tone friendly."
        ],
        "Persuasive": [
            "Use strong, persuasive language and avoid hesitation.",
            "Pause strategically to emphasize key points.",
            "Practice speaking confidently to convey authority."
        ],
        "General": [
            "Practice varying your pitch to maintain listener interest.",
            "Use pauses effectively to let your words sink in.",
            "Be mindful of your pacing—neither too fast nor too slow."
        ]
    }
    tips = advice.get(context, advice["General"])

    if pace == "slow":
        tips.append("You may want to speed up slightly for better engagement.")
    elif pace == "fast":
        tips.append("Try slowing down to make your message more comprehensible.")

    return tips

@app.post("/analyze")
async def analyze_text(user: str, text: str):
    context = detect_context(text)
    tone, score = analyze_tone(text)
    filler_feedback = detect_filler_words(text, user)
    return {"context": context, "tone": tone, "tone_score": score, "filler_feedback": filler_feedback}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            user, text = data.split(":", 1)
            context = detect_context(text)
            tone, score = analyze_tone(text)
            filler_feedback = detect_filler_words(text, user)
            await websocket.send_json({
                "context": context, "tone": tone,
                "tone_score": score, "filler_feedback": filler_feedback
            })
    except WebSocketDisconnect:
        print("WebSocket connection closed")
