// State
let appData = [];
let targetClass = "2ND UPPER (3.30)";
let totalDegCredits = 120.0;
let currentUser = null;

// DOM Elements
const pages = document.querySelectorAll('.page');
const navItems = document.querySelectorAll('.nav-item');

// Navigation
navItems.forEach(item => {
    item.addEventListener('click', () => {
        navigateTo(item.getAttribute('data-page'));
    });
});

function navigateTo(pageId) {
    navItems.forEach(i => i.classList.remove('active'));
    document.querySelector(`[data-page="${pageId}"]`)?.classList.add('active');
    
    pages.forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageId}`).classList.add('active');

    if(pageId === 'home') updateHomeDashboard();
    if(pageId === 'edit-data') renderDataTable();
    if(pageId === 'semester-overview') renderSemesterOverview();
    if(pageId === 'target-tracker') updateTargetTracker();
}

// Fetch APIs
async function processRawData() {
    const rawText = document.getElementById('rawResultsInput').value;
    if (!rawText.trim()) return alert("Please paste results first.");

    try {
        const response = await fetch('/api/process_data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ raw_text: rawText, existing_data: appData })
        });
        const result = await response.json();
        if (result.success) {
            appData = result.data;
            document.getElementById('rawResultsInput').value = '';
            if(!currentUser) saveLocal();
            else saveCloud();
            navigateTo('home');
        } else {
            alert("Error processing data: " + result.error);
        }
    } catch (e) {
        alert("Network error: " + e);
    }
}
document.getElementById('btnProcessResults').addEventListener('click', processRawData);

async function recalculateMetrics() {
    if (appData.length === 0) return null;
    try {
        const response = await fetch('/api/recalculate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ data: appData })
        });
        const result = await response.json();
        if(result.success) return result.metrics;
        return null;
    } catch(e) { return null; }
}

async function updateHomeDashboard() {
    if (appData.length === 0) {
        document.getElementById('homeEmptyState').style.display = 'flex';
        document.getElementById('homeMetrics').style.display = 'none';
        document.getElementById('homeTargets').style.display = 'none';
        document.getElementById('pieChartContainer').style.display = 'none';
        document.getElementById('lineChartContainer').style.display = 'none';
        document.getElementById('standingBadge').innerText = "AWAITING DATA";
        return;
    }

    document.getElementById('homeEmptyState').style.display = 'none';
    document.getElementById('homeMetrics').style.display = 'grid';
    document.getElementById('homeTargets').style.display = 'grid';
    document.getElementById('pieChartContainer').style.display = 'block';
    document.getElementById('lineChartContainer').style.display = 'block';
    document.getElementById('gradeBarContainer').style.display = 'block';
    document.getElementById('semBarContainer').style.display = 'block';

    const metrics = await recalculateMetrics();
    if(metrics) {
        document.getElementById('valCGPA').innerText = metrics.final_gpa.toFixed(4);
        document.getElementById('valCredits').innerText = metrics.total_credits;
        document.getElementById('valSubjects').innerText = metrics.subjects_passed;
        
        let perf = (metrics.final_gpa / 4.0) * 100;
        document.getElementById('valPerformance').innerText = perf.toFixed(1) + "%";
        document.getElementById('standingBadge').innerText = metrics.classification;
        document.getElementById('snapStanding').innerText = metrics.classification;
    }

    // Targets Snapshot
    let targetMap = {"FIRST CLASS (3.70)": 3.70, "2ND UPPER (3.30)": 3.30, "2ND LOWER (3.00)": 3.00};
    let tGpa = targetMap[targetClass];
    let titleCls = targetClass.split(" (")[0];
    document.getElementById('snapTargetTitle').innerText = "TARGET: " + titleCls;
    
    let currentCredits = metrics ? metrics.total_credits : 0;
    let currentGpa = metrics ? metrics.final_gpa : 0;
    let remaining = totalDegCredits - currentCredits;
    let requiredAvg = 0;
    if(remaining > 0) {
        requiredAvg = ((tGpa * totalDegCredits) - (currentGpa * currentCredits)) / remaining;
    }
    
    if (remaining <= 0) document.getElementById('snapTargetValue').innerText = "Completed";
    else if(requiredAvg < 0) document.getElementById('snapTargetValue').innerText = "Already Reached!";
    else if(requiredAvg > 4) document.getElementById('snapTargetValue').innerText = "Not Achievable";
    else document.getElementById('snapTargetValue').innerText = requiredAvg.toFixed(2) + " avg needed";

    let pctDone = Math.min((currentCredits / totalDegCredits)*100, 100);
    document.getElementById('snapProgress').innerText = pctDone.toFixed(1) + "% done";
    document.getElementById('snapRemaining').innerText = Math.max(remaining, 0) + " / " + totalDegCredits;

    // Build Charts
    buildCharts();
}

function buildCharts() {
    let included = appData.filter(d => d.Include === true);
    
    // Pie Chart
    let grades = {};
    included.forEach(d => {
        let g = d.grade || 'Other';
        grades[g] = (grades[g] || 0) + 1;
    });
    
    let pieData = [{
        values: Object.values(grades),
        labels: Object.keys(grades),
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent',
        textposition: 'inside',
        marker: { colors: ['#d96c34', '#e2875b', '#eba181', '#f3bcad', '#fbe7dc', '#8c8f9c', '#1a1c29', '#d1d4db'] }
    }];
    Plotly.newPlot('pieChart', pieData, {margin: {t:10, b:10, l:10, r:10}, showlegend: false}, {displayModeBar: false});

    // Line Chart
    let semMap = {};
    included.forEach(d => {
        let key = `L${d.academic_level} - S${d.semester}`;
        if(!semMap[key]) semMap[key] = { cred: 0, pts: 0 };
        semMap[key].cred += d.credits;
        semMap[key].pts += (d.credits * d.gpv);
    });

    let xVals = [], yVals = [];
    Object.keys(semMap).sort().forEach(k => {
        xVals.push(k);
        let sCred = semMap[k].cred;
        yVals.push(sCred > 0 ? (semMap[k].pts / sCred) : 0);
    });

    let lineData = [{
        x: xVals,
        y: yVals,
        type: 'scatter',
        mode: 'lines+markers+text',
        text: yVals.map(v => v.toFixed(2)),
        textposition: 'top center',
        line: {color: '#d96c34', width: 2},
        marker: {size: 8, color: '#d96c34'}
    }];
    Plotly.newPlot('lineChart', lineData, {
        margin: {t:25, b:20, l:30, r:20}, 
        yaxis: {range: [0, 4.3]},
        xaxis: {showgrid: false}
    }, {displayModeBar: false});

    // Grade Bar Chart
    let gradeOrder = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "E", "F"];
    let gradeCounts = {};
    gradeOrder.forEach(g => gradeCounts[g] = 0);
    included.forEach(d => {
        if(gradeCounts[d.grade] !== undefined) gradeCounts[d.grade]++;
    });
    
    let gXVals = [], gYVals = [];
    let started = false;
    gradeOrder.forEach(g => {
        if(gradeCounts[g] > 0) started = true;
        if(started) {
            gXVals.push(g);
            gYVals.push(gradeCounts[g]);
        }
    });

    let gradeBarData = [{
        x: gXVals,
        y: gYVals,
        type: 'bar',
        marker: {color: '#d96c34'},
        text: gYVals.map(String),
        textposition: 'auto'
    }];
    Plotly.newPlot('gradeBarChart', gradeBarData, {
        margin: {t:20, b:30, l:40, r:20},
        xaxis: {showgrid: false},
        yaxis: {title: 'Count', showgrid: true, gridcolor: 'rgba(235,128,68,0.1)'}
    }, {displayModeBar: false});

    // Sem Bar Chart
    let sXVals = Object.keys(semMap).sort();
    let sCreds = sXVals.map(k => semMap[k].cred);
    let sSubjs = sXVals.map(k => included.filter(d => `L${d.academic_level} - S${d.semester}` === k).length);

    let semBarData = [
        {x: sXVals, y: sCreds, type: 'bar', name: 'Credits', marker: {color: '#1a1c29'}, text: sCreds.map(String), textposition: 'auto'},
        {x: sXVals, y: sSubjs, type: 'bar', name: 'Subjects', marker: {color: '#d96c34'}, text: sSubjs.map(String), textposition: 'auto'}
    ];
    Plotly.newPlot('semBarChart', semBarData, {
        barmode: 'group',
        margin: {t:20, b:30, l:40, r:20},
        legend: {orientation: 'h', y: 1.1, x: 1, xanchor: 'right', yanchor: 'bottom'},
        xaxis: {showgrid: false},
        yaxis: {title: 'Count', showgrid: true, gridcolor: 'rgba(235,128,68,0.1)'}
    }, {displayModeBar: false});
}

function renderDataTable() {
    if(appData.length === 0) {
        document.getElementById('editEmptyState').style.display = 'flex';
        document.getElementById('dataTableContainer').style.display = 'none';
        return;
    }
    document.getElementById('editEmptyState').style.display = 'none';
    document.getElementById('dataTableContainer').style.display = 'block';

    const tbody = document.querySelector('#masterDataTable tbody');
    tbody.innerHTML = '';

    appData.forEach((row, idx) => {
        let tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" data-idx="${idx}" class="chk-include" ${row.Include ? 'checked' : ''}></td>
            <td>${row.academic_level}</td>
            <td>${row.semester}</td>
            <td>${row.course_code}</td>
            <td>${row.course_title}</td>
            <td>${row.credits}</td>
            <td>${row.gpv}</td>
            <td>${row.grade}</td>
        `;
        tbody.appendChild(tr);
    });
}

window.saveTableChanges = function() {
    const checkboxes = document.querySelectorAll('.chk-include');
    checkboxes.forEach(chk => {
        let idx = parseInt(chk.getAttribute('data-idx'));
        appData[idx].Include = chk.checked;
    });
    if(!currentUser) saveLocal();
    else saveCloud();
    alert("Changes saved locally. Dashboard metrics updated.");
}

function renderSemesterOverview() {
    let container = document.getElementById('semOverviewContent');
    container.innerHTML = '';
    
    if(appData.length === 0) {
        container.innerHTML = '<div class="ui-notice"><div>No data available. Please input results first.</div></div>';
        return;
    }

    let included = appData.filter(d => d.Include === true);
    let levels = [...new Set(included.map(d => d.academic_level))].sort();

    levels.forEach(lvl => {
        let lvlHtml = `<h3 style="color:#d96c34; margin-top:30px; text-transform:uppercase;">Academic Level ${lvl}</h3>`;
        let sems = [...new Set(included.filter(d => d.academic_level == lvl).map(d => d.semester))].sort();
        
        let gridHtml = `<div class="grid-${sems.length}">`;
        sems.forEach(sem => {
            let group = included.filter(d => d.academic_level == lvl && d.semester == sem);
            let sCred = group.reduce((sum, d) => sum + d.credits, 0);
            let sPts = group.reduce((sum, d) => sum + (d.credits * d.gpv), 0);
            let sGpa = sCred > 0 ? (sPts / sCred) : 0;
            
            gridHtml += `
            <div class="ui-card" style="margin-bottom:0;">
                <div class="ui-card-header">Sem ${sem}</div>
                <div class="ui-card-body">
                    <div class="ui-card-value" style="color:#d96c34; font-size:1.8rem;">${sGpa.toFixed(4)}</div>
                </div>
                <div class="ui-card-subtext">CREDITS: ${sCred} &nbsp;·&nbsp; SUBJECTS: ${group.length}</div>
            </div>`;
        });
        gridHtml += `</div><div class="grid-${sems.length}" style="margin-top:20px;">`;
        
        sems.forEach(sem => {
            let group = included.filter(d => d.academic_level == lvl && d.semester == sem);
            let tblHtml = `<table><tr><th>Course</th><th>GPV</th></tr>`;
            group.forEach(g => {
                tblHtml += `<tr><td>${g.course_title}</td><td>${g.gpv}</td></tr>`;
            });
            tblHtml += `</table>`;
            gridHtml += `<div>${tblHtml}</div>`;
        });
        gridHtml += `</div>`;
        
        container.innerHTML += lvlHtml + gridHtml;
    });
}

function updateTargetTracker() {
    document.getElementById('targetClassSelect').value = targetClass;
    document.getElementById('totalDegCreditsInput').value = totalDegCredits;
    calculateTarget();
}

window.calculateTarget = async function() {
    targetClass = document.getElementById('targetClassSelect').value;
    totalDegCredits = parseFloat(document.getElementById('totalDegCreditsInput').value);
    
    if(!currentUser) saveLocal();
    else saveCloud();
    
    if(appData.length === 0) return;
    
    let metrics = await recalculateMetrics();
    if(!metrics) return;
    
    let targetMap = {"FIRST CLASS (3.70)": 3.70, "2ND UPPER (3.30)": 3.30, "2ND LOWER (3.00)": 3.00};
    let tGpa = targetMap[targetClass];
    let currentCredits = metrics.total_credits;
    let currentGpa = metrics.final_gpa;
    let remaining = totalDegCredits - currentCredits;
    
    let reqEl = document.getElementById('targetRequiredValue');
    let remEl = document.getElementById('targetRemainingText');
    
    if (remaining <= 0) {
        reqEl.innerText = "-";
        remEl.innerText = "Degree already completed.";
    } else {
        let requiredAvg = ((tGpa * totalDegCredits) - (currentGpa * currentCredits)) / remaining;
        if(requiredAvg > 4) {
            reqEl.innerText = "N/A";
            reqEl.style.color = "red";
            remEl.innerText = "Mathematically impossible.";
        } else if(requiredAvg < 0) {
            reqEl.innerText = "Done";
            reqEl.style.color = "green";
            remEl.innerText = "Already reached the requirement!";
        } else {
            reqEl.innerText = requiredAvg.toFixed(2);
            reqEl.style.color = "#d96c34";
            remEl.innerText = `Based on ${remaining} remaining credits.`;
        }
    }
}

// Data Persistence
function saveLocal() {
    const payload = {
        data: appData,
        target_class: targetClass,
        total_deg_credits: totalDegCredits
    };
    localStorage.setItem("guest_gpa_data", JSON.stringify(payload));
}

function loadLocal() {
    const stored = localStorage.getItem("guest_gpa_data");
    if(stored) {
        try {
            let parsed = JSON.parse(stored);
            if(parsed.data) {
                appData = parsed.data;
                targetClass = parsed.target_class || "2ND UPPER (3.30)";
                totalDegCredits = parsed.total_deg_credits || 120.0;
            } else {
                appData = parsed;
            }
        } catch(e) {}
    }
}

async function saveCloud() {
    if(!currentUser) return;
    const payload = {
        data: appData,
        target_class: targetClass,
        total_deg_credits: totalDegCredits
    };
    try {
        await fetch('/api/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_id: currentUser, payload: payload })
        });
    } catch(e) {}
}

async function loadCloud(userId) {
    try {
        const response = await fetch(`/api/load?user_id=${userId}`);
        const result = await response.json();
        if(result.success && result.payload) {
            appData = result.payload.data || [];
            targetClass = result.payload.target_class || "2ND UPPER (3.30)";
            totalDegCredits = result.payload.total_deg_credits || 120.0;
            return true;
        }
    } catch(e) {}
    return false;
}

// Auth Handlers
document.getElementById('btnSave').addEventListener('click', () => {
    saveLocal();
    alert("Saved Locally");
});

document.getElementById('btnLogin').addEventListener('click', () => {
    if(currentUser) {
        currentUser = null;
        appData = [];
        document.getElementById('authStatus').innerHTML = "Status: <strong>Guest Mode</strong> (Local Save)";
        document.getElementById('btnLogin').innerText = "Login / Sync";
        document.getElementById('btnSave').style.display = "block";
        navigateTo('home');
    } else {
        document.getElementById('loginModal').style.display = 'flex';
    }
});

document.getElementById('btnConfirmLogin').addEventListener('click', async () => {
    let uid = document.getElementById('loginUserId').value.trim();
    if(uid) {
        currentUser = uid;
        document.getElementById('loginModal').style.display = 'none';
        document.getElementById('authStatus').innerHTML = `Status: <strong>Logged In</strong> (${uid})`;
        document.getElementById('btnLogin').innerText = "Logout";
        document.getElementById('btnSave').style.display = "none";
        appData = [];
        await loadCloud(uid);
        navigateTo('home');
    } else {
        alert("Enter a valid Student ID");
    }
});

// Feedback Form Handler
document.getElementById('feedbackForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btnSubmitFeedback');
    const originalText = btn.innerText;
    btn.innerText = "SENDING...";
    btn.disabled = true;

    const fName = document.getElementById('feedbackName').value || "Anonymous";
    const fType = document.getElementById('feedbackType').value;
    const fMsg = document.getElementById('feedbackMsg').value;

    try {
        const response = await fetch("https://formsubmit.co/ajax/abilash0asp@gmail.com", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                name: fName,
                type: fType,
                message: fMsg,
                _subject: `New Academic Tracker Feedback: ${fType}`,
                _captcha: "false"
            })
        });

        const data = await response.json();
        
        if (response.ok && String(data.success).toLowerCase() === "true") {
            alert("Thank you! Your feedback has been sent directly to the developer.");
            document.getElementById('feedbackForm').reset();
        } else if (data.message && (data.message.includes("Activation") || data.message.includes("actived"))) {
            alert("⚠️ One-Time Activation Required! FormSubmit has sent an email to your address. Please click 'Activate Form' in that email.");
        } else {
            alert("Error sending feedback: " + (data.message || "Unknown error"));
        }
    } catch (error) {
        alert("Network error. Please try again later.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// Init
window.onload = () => {
    loadLocal();
    navigateTo('home');
};
