"""
Future Job Builder - Backend Engine (main.py)
A production-ready Flask server serving the landing page, multi-step assessment,
loading/analysis sequences, and calculating multi-dimensional career matches 
complete with an educational "AI Resistance Score" and skill roadmap.
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Secure secret key assignment with fallback for local development
app.secret_key = os.environ.get("SECRET_KEY", "f7b_secure_dev_fallback_key_2026")

# Hardcoded fallback data in case JSON configuration files are missing during initial setup
DEFAULT_CAREERS = [
    {
        "id": "prod_mgr",
        "title": "AI Product Manager",
        "category": "Technology & Business",
        "salary_potential": "High",
        "growth_outlook": "Rapidly Growing",
        "ai_resistance_score": 85,
        "interests": {"tech": 5, "business": 5, "design": 4, "communication": 5},
        "strengths": {"leadership": 5, "problem_solving": 5, "analytical": 4, "teamwork": 5},
        "preferences": {"independent": 2, "collaborative": 5, "creative": 4, "stable": 2, "strategic": 5},
        "priorities": {"salary": 5, "innovation": 5, "leadership": 5, "flexibility": 4},
        "explanation": "You enjoy solving business problems while working with technology and collaborating with teams, making Product Management a strong fit.",
        "skills": ["Communication", "Leadership", "Data Analysis", "Project Management", "Critical Thinking"],
        "roadmap": {
            "start_now": ["Learn spreadsheet fundamentals", "Improve public speaking", "Practice basic wireframing"],
            "build_experience": ["Complete personal project specs", "Join school entrepreneurship clubs", "Participate in local hackathons"],
            "prepare_future": ["Earn introductory Agile/Scrum certifications", "Explore Business or Computer Science majors", "Build a product case study portfolio"]
        }
    },
    {
        "id": "ai_ethicist",
        "title": "AI Ethics Consultant",
        "category": "Technology & Humanities",
        "salary_potential": "High",
        "growth_outlook": "Rapidly Growing",
        "ai_resistance_score": 92,
        "interests": {"tech": 4, "science": 3, "communication": 5, "creativity": 4},
        "strengths": {"analytical": 5, "problem_solving": 5, "curiosity": 5, "communication": 5},
        "preferences": {"independent": 3, "collaborative": 4, "creative": 5, "stable": 1, "strategic": 5},
        "priorities": {"innovation": 5, "helping_others": 5, "flexibility": 4},
        "explanation": "Your deep curiosity, analytical mindset, and focus on helping others align perfectly with defining safe and ethical guidelines for future technologies.",
        "skills": ["Ethical Reasoning", "Critical Thinking", "Tech Policy", "Written Communication", "Analytical Thinking"],
        "roadmap": {
            "start_now": ["Read introductory articles on tech ethics", "Participate in debate or philosophy clubs", "Write analytical essays on current technology"],
            "build_experience": ["Start a tech ethics newsletter", "Join public speaking or policy forums", "Analyze real-world AI bias case studies"],
            "prepare_future": ["Explore interdisciplinary majors (e.g., Cognitive Science, Tech Policy)", "Build a portfolio of published opinion pieces", "Earn certified course badges in ethics in AI"]
        }
    },
    {
        "id": "bioinfo_spec",
        "title": "Bioinformatics Specialist",
        "category": "Science & Technology",
        "salary_potential": "High",
        "growth_outlook": "Growing",
        "ai_resistance_score": 78,
        "interests": {"tech": 5, "science": 5, "healthcare": 4},
        "strengths": {"analytical": 5, "problem_solving": 4, "curiosity": 5},
        "preferences": {"independent": 4, "collaborative": 3, "creative": 3, "stable": 4, "strategic": 4},
        "priorities": {"innovation": 5, "salary": 4, "job_security": 4},
        "explanation": "By combining your strong passion for science and healthcare with computing and analytical thinking, you can pioneer healthcare discoveries.",
        "skills": ["Data Analysis", "Programming", "Biology", "Research Methodologies", "Critical Thinking"],
        "roadmap": {
            "start_now": ["Practice basic programming (Python)", "Learn foundational biology concepts", "Learn spreadsheet data manipulation"],
            "build_experience": ["Create a small script to parse genetic sequences", "Join school science clubs", "Participate in science fair competitions"],
            "prepare_future": ["Explore Biotechnology, Bioinformatics, or CS majors", "Seek research assistant internships", "Earn basic Python data science certifications"]
        }
    }
]

def load_careers_database():
    """Loads career configuration from career_data directory, falling back safely if not found."""
    filepath = os.path.join("career_data", "careers.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse careers.json: {e}. Falling back to defaults.")
    return DEFAULT_CAREERS

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
    """Renders Step 3: Interactive Dynamic Loading Screen."""
    return render_template("analysis.html")

@app.route("/results")
def results_page():
    """Renders Step 4: Full Career Results Dashboard."""
    return render_template("results.html")

# Evaluation API
@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Processes incoming multidimensional user responses from the questionnaire,
    calculates match scores based on cosine similarity heuristics, normalizes
    metrics, and returns a sorted recommendations array.
    """
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "No input payload received"}), 400

        # Retrieve structured evaluation properties
        user_interests = user_data.get("interests", {})
        user_strengths = user_data.get("strengths", {})
        user_preferences = user_data.get("preferences", {})
        user_priorities = user_data.get("priorities", {})

        careers = load_careers_database()
        scored_results = []

        for career in careers:
            score_acc = 0.0
            total_elements = 0

            # 1. Compare Interests
            for interest, value in career.get("interests", {}).items():
                user_val = float(user_interests.get(interest, 0))
                # Normalized distance calculation
                diff = abs(value - user_val)
                score_acc += max(0.0, 1.0 - (diff / 5.0))
                total_elements += 1

            # 2. Compare Strengths
            for strength, value in career.get("strengths", {}).items():
                user_val = float(user_strengths.get(strength, 0))
                diff = abs(value - user_val)
                score_acc += max(0.0, 1.0 - (diff / 5.0))
                total_elements += 1

            # 3. Compare Preferences
            for preference, value in career.get("preferences", {}).items():
                user_val = float(user_preferences.get(preference, 0))
                diff = abs(value - user_val)
                score_acc += max(0.0, 1.0 - (diff / 5.0))
                total_elements += 1

            # 4. Compare Priorities
            for priority, value in career.get("priorities", {}).items():
                user_val = float(user_priorities.get(priority, 0))
                diff = abs(value - user_val)
                score_acc += max(0.0, 1.0 - (diff / 5.0))
                total_elements += 1

            # Prevent divide-by-zero, fallback safely
            match_score_pct = int((score_acc / total_elements) * 100) if total_elements > 0 else 50
            # Ensure score remains capped logically between 0% and 100%
            match_score_pct = min(100, max(0, match_score_pct))

            scored_results.append({
                "title": career["title"],
                "category": career.get("category", "General"),
                "match_score": match_score_pct,
                "ai_resistance_score": career["ai_resistance_score"],
                "salary_potential": career["salary_potential"],
                "growth_outlook": career["growth_outlook"],
                "explanation": career["explanation"],
                "skills": career["skills"],
                "roadmap": career["roadmap"]
            })

        # Sort recommendations descending by match percentage score
        scored_results = sorted(scored_results, key=lambda x: x["match_score"], reverse=True)

        return jsonify({
            "status": "success",
            "results": scored_results
        })

    except Exception as e:
        logger.error(f"Exception encountered during recommendation evaluation: {e}")
        return jsonify({"error": "An internal scoring error occurred", "details": str(e)}), 500

if __name__ == "__main__":
    # Render binds the active PORT environment variable dynamically
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
