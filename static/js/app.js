// static/js/app.js

document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // 1. ASSESSMENT LOGIC (assessment.html)
    // ==========================================
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
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
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
            
            // Build structured JSON payload matching backend requirements
            const formData = new FormData(assessmentForm);
            const payload = { 
                interests: {}, 
                strengths: {}, 
                preferences: {}, 
                priorities: {},
                text_inputs: {} 
            };
            
            for (let [key, value] of formData.entries()) {
                const parts = key.split('.');
                const category = parts[0];
                const item = parts[1];
                
                if (payload[category]) {
                    // Check if input is a text input or numerical slider
                    if (category === 'text_inputs') {
                        payload[category][item] = value.trim();
                    } else {
                        payload[category][item] = parseInt(value, 10);
                    }
                }
            }

            // Save payload to sessionStorage and transition to analysis screen
            sessionStorage.setItem('jobBuilderPayload', JSON.stringify(payload));
            window.location.href = '/analysis';
        });

        updateUI(); // Initialize UI state
    }

    // ==========================================
    // 2. ANALYSIS LOGIC (analysis.html)
    // ==========================================
    const tickerText = document.getElementById('tickerText');
    if (tickerText) {
        const messages = [
            "Analyzing your interests & preferences...",
            "Consulting llama-3.3-70b-versatile AI engine...",
            "Fetching real-time market data & job openings...",
            "Generating your personalized career roadmap..."
        ];
        
        let msgIndex = 0;
        const interval = setInterval(() => {
            msgIndex++;
            if (msgIndex < messages.length) {
                tickerText.innerText = messages[msgIndex];
            } else {
                clearInterval(interval);
            }
        }, 800);

        // Fetch AI evaluation and Adzuna market metrics concurrently
        const payload = JSON.parse(sessionStorage.getItem('jobBuilderPayload') || '{}');
        
        fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success" || data.results) {
                sessionStorage.setItem('jobBuilderResults', JSON.stringify(data.results));
                setTimeout(() => {
                    window.location.href = '/results';
                }, 3200); // Allow ticker animations to conclude
            } else {
                throw new Error(data.message || "Failed to evaluate results.");
            }
        })
        .catch(err => {
            console.error("Error evaluating careers:", err);
            if (tickerText) {
                tickerText.innerText = "An error occurred during evaluation. Redirecting...";
            }
            setTimeout(() => {
                window.location.href = '/assessment';
            }, 3000);
        });
    }

    // ==========================================
    // 3. RESULTS LOGIC & CHART.JS (results.html)
    // ==========================================
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        const results = JSON.parse(sessionStorage.getItem('jobBuilderResults') || '[]');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div style="text-align: center; width: 100%; padding: 3rem 1rem;">
                    <p style="font-size: 1.1rem; color: #64748b;">No results found. Please complete the assessment first.</p>
                    <a href="/assessment" class="btn" style="background:#2563eb; color:#fff; padding:0.6rem 1.2rem; text-decoration:none; border-radius:6px; display:inline-block; margin-top:1rem;">Start Assessment</a>
                </div>`;
            return;
        }

        resultsContainer.innerHTML = '';

        results.forEach((career, index) => {
            const canvasId = `demandChart_${index}`;
            
            // Handle roadmap compatibility for legacy arrays or phase objects
            const roadmapPhase1 = career.roadmap?.phase_1_immediate || career.roadmap?.start_now || [];
            const roadmapPhase2 = career.roadmap?.phase_2_experience || career.roadmap?.build_experience || [];
            const roadmapPhase3 = career.roadmap?.phase_3_future || career.roadmap?.prepare_future || [];

            const cardHtml = `
                <div class="career-card">
                    <div class="card-header">
                        <span class="career-category">${career.category || 'General'}</span>
                        <h3 class="career-title" style="margin-top:0.25rem;">${career.title}</h3>
                        <p style="font-size: 0.88rem; color: #475569; margin-top: 0.5rem; font-style: italic;">"${career.explanation}"</p>
                    </div>

                    <div class="metrics-grid">
                        <div class="metric-badge">
                            <div class="metric-value">${career.match_score}%</div>
                            <div class="metric-label">Profile Match</div>
                        </div>
                        <div class="metric-badge">
                            <div class="metric-value" style="color: #16a34a;">${career.ai_resistance_score}%</div>
                            <div class="metric-label">AI Resistance</div>
                        </div>
                        <div class="metric-badge">
                            <div class="metric-value" style="color: #0284c7;">${(career.live_openings || 0).toLocaleString()}</div>
                            <div class="metric-label">Live Openings</div>
                        </div>
                        <div class="metric-badge">
                            <div class="metric-value" style="font-size:0.95rem; color:#d97706;">${career.salary_potential || 'Market Competitive'}</div>
                            <div class="metric-label">Live Salary Range</div>
                        </div>
                    </div>

                    <!-- Market Demand Trend Chart Canvas -->
                    <div class="chart-container" style="position: relative; height:180px; margin: 1.25rem 0;">
                        <canvas id="${canvasId}"></canvas>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <strong style="font-size: 0.85rem; color: #1e293b;">Core Skills Required:</strong>
                        <div class="skills-list" style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.4rem;">
                            ${(career.skills || []).map(s => `<span class="skill-tag" style="background:#e0e7ff; color:#3730a3; font-size:0.75rem; padding:0.2rem 0.6rem; border-radius:20px;">${s}</span>`).join('')}
                        </div>
                    </div>

                    <div class="roadmap-section" style="background: #f8fafc; border-radius: 8px; padding: 1rem;">
                        <h4 style="margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #0f172a;">Actionable Career Roadmap</h4>
                        
                        <div class="roadmap-phase" style="margin-bottom:0.6rem;">
                            <strong style="font-size:0.8rem; color:#1e293b;">Phase 1: Immediate Foundations</strong>
                            <ul style="margin:0.2rem 0 0 1.2rem; padding:0; font-size:0.8rem; color:#475569;">${roadmapPhase1.map(i => `<li>${i}</li>`).join('')}</ul>
                        </div>

                        <div class="roadmap-phase" style="margin-bottom:0.6rem;">
                            <strong style="font-size:0.8rem; color:#1e293b;">Phase 2: Projects & Internships</strong>
                            <ul style="margin:0.2rem 0 0 1.2rem; padding:0; font-size:0.8rem; color:#475569;">${roadmapPhase2.map(i => `<li>${i}</li>`).join('')}</ul>
                        </div>

                        <div class="roadmap-phase">
                            <strong style="font-size:0.8rem; color:#1e293b;">Phase 3: Higher Ed & Future Specialization</strong>
                            <ul style="margin:0.2rem 0 0 1.2rem; padding:0; font-size:0.8rem; color:#475569;">${roadmapPhase3.map(i => `<li>${i}</li>`).join('')}</ul>
                        </div>
                    </div>
                </div>
            `;

            resultsContainer.insertAdjacentHTML("beforeend", cardHtml);

            // Render Chart.js line graph asynchronously for each card
            setTimeout(() => {
                const canvasElement = document.getElementById(canvasId);
                if (canvasElement && typeof Chart !== 'undefined') {
                    const ctx = canvasElement.getContext("2d");
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: career.trend_labels || ["M-5", "M-4", "M-3", "M-2", "M-1", "Current"],
                            datasets: [{
                                label: 'Active Market Listings',
                                data: career.trend_data || [800, 850, 910, 890, 940, 1000],
                                borderColor: '#2563eb',
                                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                                fill: true,
                                tension: 0.3,
                                borderWidth: 2,
                                pointRadius: 3
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                title: {
                                    display: true,
                                    text: 'Demand / Active Listings Trend',
                                    font: { size: 11, weight: 'bold' }
                                }
                            },
                            scales: {
                                y: {
                                    ticks: { font: { size: 9 } },
                                    grid: { color: '#f1f5f9' }
                                },
                                x: {
                                    ticks: { font: { size: 9 } },
                                    grid: { display: false }
                                }
                            }
                        }
                    });
                }
            }, 50);
        });
    }
});
