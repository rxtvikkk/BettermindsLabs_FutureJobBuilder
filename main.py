"""
Future Job Builder - Backend Engine (main.py)
Integrates Groq (llama-3.3-70b-versatile) for career analysis and 
Adzuna API for real-time salary, live job openings, and market demand trends.
"""

import os
import json
import logging
import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "f7b_secure_dev_fallback_key_2026")

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def fetch_adzuna_live_data(job_title, country="us"):
    """
    Fetches real-time job openings count, salary stats, and historical demand trends from Adzuna.
    Falls back to safe default metrics if API credentials are missing or call fails.
    """
    fallback_data = {
        "live_openings": 1240,
        "salary_min": 85000,
        "salary_max": 145000,
        "salary_formatted": "$85,000 - $145,000",
        "trend_labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "trend_data": [1050, 1100, 1180, 1150, 1210, 1240]
    }

    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna credentials not configured. Returning estimated market data.")
        return fallback_data

    try:
        # 1. Fetch live openings count & current average salary
        search_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": job_title,
            "results_per_page": 1
        }
        res = requests.get(search_url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            total_openings = data.get("count", 1000)
            
            # Calculate salary bounds from job results or mean
            results = data.get("results", [])
            if results and "salary_min" in results[0]:
                sal_min = int(results[0].get("salary_min", 75000))
                sal_max = int(results[0].get("salary_max", 130000))
            else:
                sal_min, sal_max = 80000, 140000

            # 2. Fetch historical vacancy count trends (Historical API)
            history_url = f"https://api.adzuna.com/v1/api/jobs/{country}/history"
            hist_params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "what": job_title,
                "months": 6
            }
            hist_res = requests.get(history_url, params=hist_params, timeout=5)
            
            trend_labels = ["M-5", "M-4", "M-3", "M-2", "M-1", "Current"]
            trend_values = [int(total_openings * x) for x in [0.85, 0.88, 0.92, 0.90, 0.96, 1.0]]

            if hist_res.status_code == 200:
                hist_data = hist_res.json().get("month", {})
                if hist_data:
                    sorted_months = sorted(hist_data.keys())[-6:]
                    trend_labels = [m[-2:] for m in sorted_months]
                    trend_values = [hist_data[m] for m in sorted_months]

            return {
                "live_openings": total_openings,
                "salary_min": sal_min,
                "salary_max": sal_max,
                "salary_formatted": f"${sal_min:,} - ${sal_max:,}",
                "trend_labels": trend_labels,
                "trend_data": trend_values
            }

    except Exception as e:
        logger.error(f"Error fetching Adzuna data for '{job_title}': {e}")

    return fallback_data


# Template Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/assessment")
def assessment():
    return render_template("assessment.html")

@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/results")
def results_page():
    return render_template("results.html")


# Dynamic AI + Live Data Evaluation API
@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    try:
        user_data = request.json or {}
        
        interests = user_data.get("interests", {})
        strengths = user_data.get("strengths", {})
        preferences = user_data.get("preferences", {})
        priorities = user_data.get("priorities", {})
        text_inputs = user_data.get("text_inputs", {})
        user_likes = text_inputs.get("likes", "None")
        user_dislikes = text_inputs.get("dislikes", "None")

        if not groq_client:
            logger.warning("Groq client not initialized. Ensure GROQ_API_KEY is set.")
            return jsonify({"status": "error", "message": "Groq API key not set"}), 500

        system_prompt = (
            "You are an expert career counselor and AI workforce strategist. "
            "Analyze student inputs and return EXACTLY 3 tailored career recommendations in structured JSON format. "
            "You MUST respond ONLY with valid JSON. Do not include markdown blocks or extra text."
        )

        user_prompt = f"""
Student Profile Ratings (Scale 1-5):
- Interests: {json.dumps(interests)}
- Strengths: {json.dumps(strengths)}
- Preferences: {json.dumps(preferences)}
- Priorities: {json.dumps(priorities)}

Specific Qualitative Feedback:
- What the student ENJOYS/LIKES: "f{user_likes}"
- What the student DISLIKES/AVOIDS: "f{user_dislikes}"

Return a JSON object containing a "careers" array with 3 career objects matching this exact structure:
{{
  "careers": [
    {{
      "title": "Exact Official Job Title",
      "category": "Industry Field",
      "match_score": 94,
      "ai_resistance_score": 88,
      "growth_outlook": "High Demand",
      "explanation": "2 concise sentences explaining why this job fits their exact strengths and avoids their dislikes.",
      "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
      "roadmap": {{
        "phase_1_immediate": ["Actionable step 1", "Actionable step 2", "Actionable step 3"],
        "phase_2_experience": ["Project 1", "Club/Internship 2", "Certification 3"],
        "phase_3_future": ["Degree/Major choice", "Specialized portfolio", "Industry networking"]
      }}
    }}
  ]
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        raw_data = json.loads(completion.choices[0].message.content)
        careers_list = raw_data.get("careers", [])

        # Enrich each AI-generated career with Live Real-Time Adzuna Market Data
        for career in careers_list:
            live_market = fetch_adzuna_live_data(career["title"])
            career["live_openings"] = live_market["live_openings"]
            career["salary_potential"] = live_market["salary_formatted"]
            career["trend_labels"] = live_market["trend_labels"]
            career["trend_data"] = live_market["trend_data"]

        return jsonify({
            "status": "success",
            "results": careers_list
        })

    except Exception as e:
        logger.error(f"Error in evaluation route: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
