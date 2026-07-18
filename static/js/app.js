// static/js/app.js

document.addEventListener("DOMContentLoaded", () => {
    
    // --- Assessment Logic (assessment.html) ---
    const assessmentForm = document.getElementById('assessmentForm');
    if (assessmentForm) {
        let currentSection = 0;
        const sections = document.querySelectorAll('.assessment-section');
        const progressBar = document.getElementById('progressBar');
        const nextBtns = document.querySelectorAll('.next-btn');
        const prevBtns = document.querySelectorAll('.prev-btn');

        function updateUI() {
            sections.forEach((sec, index) => {
                sec.classList.toggle('active', index === currentSection);
            });
            const progress = ((currentSection + 1) / sections.length) * 100;
            progressBar.style.width = `${progress}%`;
        }

        nextBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (currentSection < sections.length - 1) {
                    currentSection++;
                    updateUI();
                }
            });
        });

        prevBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (currentSection > 0) {
                    currentSection--;
                    updateUI();
                }
            });
        });

        assessmentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Build structured JSON matching the backend evaluation payload
            const formData = new FormData(assessmentForm);
            const payload = { interests: {}, strengths: {}, preferences: {}, priorities: {} };
            
            for (let [key, value] of formData.entries()) {
                const [category, item] = key.split('.');
                if (payload[category]) {
                    payload[category][item] = parseInt(value, 10);
                }
            }

            // Temporarily store payload and redirect to analysis screen
            sessionStorage.setItem('jobBuilderPayload', JSON.stringify(payload));
            window.location.href = '/analysis';
        });

        updateUI(); // Init
    }

    // --- Analysis Logic (analysis.html) ---
    const tickerText = document.getElementById('tickerText');
    if (tickerText) {
        const messages = [
            "Analyzing your interests...",
            "Comparing career pathways...",
            "Identifying future-ready skills...",
            "Generating recommendations..."
        ];
        
        let msgIndex = 0;
        const interval = setInterval(() => {
            msgIndex++;
            if (msgIndex < messages.length) {
                tickerText.innerText = messages[msgIndex];
            } else {
                clearInterval(interval);
            }
        }, 750); // Transitions complete within 2-3 seconds total

        // Fetch data from backend concurrently
        const payload = JSON.parse(sessionStorage.getItem('jobBuilderPayload'));
        
        fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        })
        .then(res => res.json())
        .then(data => {
            sessionStorage.setItem('jobBuilderResults', JSON.stringify(data.results));
            setTimeout(() => {
                window.location.href = '/results';
            }, 3000); // Ensure ticker finishes before redirecting
        })
        .catch(err => {
            console.error("Error evaluating careers:", err);
            tickerText.innerText = "An error occurred. Please try again.";
        });
    }

    // --- Results Logic (results.html) ---
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        const results = JSON.parse(sessionStorage.getItem('jobBuilderResults') || '[]');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = "<p>No results found. Please retake the assessment.</p>";
            return;
        }

        resultsContainer.innerHTML = results.map(career => `
            <div class="career-card">
                <div class="card-header">
                    <h3>${career.title}</h3>
                    <p class="text-muted">${career.category}</p>
                    <div style="margin-top: 0.5rem;">
                        <span class="score-badge score-match">Match: ${career.match_score}%</span>
                        <span class="score-badge score-ai">AI Resistance: ${career.ai_resistance_score}%</span>
                    </div>
                </div>
                <div>
                    <p><strong>Salary Potential:</strong> ${career.salary_potential}</p>
                    <p><strong>Growth Outlook:</strong> ${career.growth_outlook}</p>
                    <p><em>${career.explanation}</em></p>
                    <p><strong>Core Skills:</strong> ${career.skills.join(', ')}</p>
                </div>
                <div class="roadmap">
                    <h4>Skill Roadmap</h4>
                    <strong>Start Now:</strong>
                    <ul>${career.roadmap.start_now.map(s => `<li>${s}</li>`).join('')}</ul>
                    <strong>Build Experience:</strong>
                    <ul>${career.roadmap.build_experience.map(s => `<li>${s}</li>`).join('')}</ul>
                    <strong>Prepare for the Future:</strong>
                    <ul>${career.roadmap.prepare_future.map(s => `<li>${s}</li>`).join('')}</ul>
                </div>
            </div>
        `).join('');
    }
});