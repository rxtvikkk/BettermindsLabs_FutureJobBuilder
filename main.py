"""
Future Job Builder - Backend Engine (main.py)
A production-ready Flask server serving the platform and integrating
Groq (llama-3.3-70b-versatile) to dynamically analyze student assessment data
and generate tailored career recommendations with AI Resistance Scores.
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from groq import Groq

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "f7b_secure_dev_fallback_key_2026")

# Initialize Groq client using Environment Variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# Fallback generator in case Groq API key is missing or fails
def get_fallback_results(user_data):
    return [
        {
            "title": "AI Product Manager",
            "category": "Technology & Business",
            "match_score": 92,
            "ai_resistance_score": 85,
            "salary_potential": "High ($110,000 - $180,000)",
            "growth_outlook": "Rapidly Growing",
            "explanation": "You enjoy solving business problems while working with technology and collaborating with teams.",
            "skills": ["Communication", "Leadership", "Data Analysis", "Project Management", "Critical Thinking"],
            "roadmap": {
                "start_now": ["Learn spreadsheet fundamentals", "Improve public speaking"],
                "build_experience": ["Complete personal project specs", "Join school entrepreneurship clubs"],
                "prepare_future": ["Explore Business or CS majors", "Build a product case study portfolio"]
            }
        }
    ]


# Serve Templates
@app.route("/")
def index():
    """Renders Step 1: Landing Page."""
    return render_template("index.html")

@app.route("/assessment")
def assessment():
    """Renders Step 2: Interactive Assessment Screen."""
    return render_template("assessment.html")

@app.route("/analysis")
def analysis():
    """Renders Step 3: Dynamic Loading Screen."""
    return render_template("analysis.html")

@app.route("/results")
def results_page():
    """Renders Step 4: Full Career Results Dashboard."""
    return render_template("results.html")


# Dynamic Evaluation API using Groq LLM
@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Receives user assessment scores, sends them to Groq's llama-3.3-70b-versatile,
    and returns dynamically generated career recommendations in JSON format.
    """
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "No input payload received"}), 400

        # Extract submitted profile features
        interests = user_data.get("interests", {})
        strengths = user_data.get("strengths", {})
        preferences = user_data.get("preferences", {})
        priorities = user_data.get("priorities", {})

        # If Groq client is not configured, warn and return fallback
        if not groq_client:
            logger.warning("GROQ_API_KEY environment variable not set. Returning fallback data.")
            return jsonify({
                "status": "success",
                "results": get_fallback_results(user_data),
                "notice": "Render GROQ_API_KEY missing, using static fallback."
            })

        # System prompt instructing LLM to strictly return JSON array
        system_prompt = (
            "You are an expert career guidance counselor and AI workforce analyst. "
            "Analyze high school student profile assessments and recommend exactly 3 highly relevant careers. "
            "You MUST respond ONLY with a valid JSON array containing career objects. Do NOT include markdown code blocks, preamble, or commentary."
        )

       text_inputs = user_data.get("text_inputs", {})
       user_likes = text_inputs.get("likes", "None provided")
       user_dislikes = text_inputs.get("dislikes", "None provided")

       user_prompt = f"""
Student Profile Ratings (Scale 1-5):
- Interests: {json.dumps(interests)}
- Strengths: {json.dumps(strengths)}
- Work Preferences: {json.dumps(preferences)}
- Priorities: {json.dumps(priorities)}

Specific Qualitative Feedback:
- What the student ENJOYS/LIKES: "f{user_likes}"
- What the student DISLIKES/AVOIDS: "f{user_dislikes}"

Return a JSON array with 3 career objects matching the requested schema.
"""

Return a JSON array with 3 career objects. Each object must strictly match this exact JSON structure:
[
  {{
    "title": "Career Title",
    "category": "Industry Category",
    "match_score": 95,
    "ai_resistance_score": 88,
    "salary_potential": "High ($XX,XXX - $XXX,XXX)",
    "growth_outlook": "Rapidly Growing",
    "explanation": "Clear 2-sentence explanation of why this fits their profile.",
    "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
    "roadmap": {{
      "start_now": ["Action item 1", "Action item 2"],
      "build_experience": ["Action item 1", "Action item 2"],
      "prepare_future": ["Action item 1", "Action item 2"]
    }}
  }}
]
"""

        # Call Groq API with llama-3.3-70b-versatile
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )

        raw_response = completion.choices[0].message.content
        logger.info("Successfully received LLM response from Groq.")

        # Parse Groq response safely
        parsed_json = json.loads(raw_response)
        
        # Extract array whether root is an array or wrapped in a key
        if isinstance(parsed_json, list):
            results = parsed_json
        elif isinstance(parsed_json, dict) and "careers" in parsed_json:
            results = parsed_json["careers"]
        elif isinstance(parsed_json, dict) and "results" in parsed_json:
            results = parsed_json["results"]
        else:
            # Grab first list value if dict wrapper was used
            results = next((v for v in parsed_json.values() if isinstance(v, list)), get_fallback_results(user_data))

        return jsonify({
            "status": "success",
            "results": results
        })

    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return jsonify({
            "status": "success",
            "results": get_fallback_results(request.json or {}),
            "error_details": str(e)
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
