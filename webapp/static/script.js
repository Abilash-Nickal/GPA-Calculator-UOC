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
    // Automatically close mobile drawer when navigating
    document.getElementById('appSidebar')?.classList.remove('open');
    document.getElementById('sidebarBackdrop')?.classList.remove('open');
    document.body.classList.remove('drawer-open');

    navItems.forEach(i => i.classList.remove('active'));
    document.querySelector(`[data-page="${pageId}"]`)?.classList.add('active');
    
    pages.forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageId}`).classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });

    if(pageId === 'home') {
        updateHomeDashboard();
        setTimeout(triggerChartsResize, 60);
    }
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

function updateStickySummary(cgpa = "0.00", credits = "0 Cr", standing = "Awaiting Data") {
    const stickyCGPA = document.getElementById('stickyCGPA');
    const stickyCredits = document.getElementById('stickyCredits');
    const stickyStanding = document.getElementById('stickyStanding');
    if (stickyCGPA) stickyCGPA.innerText = cgpa;
    if (stickyCredits) stickyCredits.innerText = credits;
    if (stickyStanding) stickyStanding.innerText = standing;
}

async function updateHomeDashboard() {
    if (appData.length === 0) {
        document.getElementById('homeEmptyState').style.display = 'flex';
        document.getElementById('homeMetrics').style.display = 'none';
        document.getElementById('homeTargets').style.display = 'none';
        document.getElementById('pieChartContainer').style.display = 'none';
        document.getElementById('lineChartContainer').style.display = 'none';
        document.getElementById('homeSubjectsCard').style.display = 'none';
        document.getElementById('standingBadge').innerText = "AWAITING DATA";
        updateStickySummary("0.00", "0 Cr", "Awaiting Data");
        return;
    }

    document.getElementById('homeEmptyState').style.display = 'none';
    document.getElementById('homeMetrics').style.display = 'grid';
    document.getElementById('homeTargets').style.display = 'grid';
    document.getElementById('pieChartContainer').style.display = 'block';
    document.getElementById('lineChartContainer').style.display = 'block';
    document.getElementById('gradeBarContainer').style.display = 'block';
    document.getElementById('semBarContainer').style.display = 'block';
    document.getElementById('homeSubjectsCard').style.display = 'block';

    const metrics = await recalculateMetrics();
    if(metrics) {
        document.getElementById('valCGPA').innerText = metrics.final_gpa.toFixed(4);
        document.getElementById('valCredits').innerText = metrics.total_credits;
        document.getElementById('valSubjects').innerText = metrics.subjects_passed;
        
        let perf = (metrics.final_gpa / 4.0) * 100;
        document.getElementById('valPerformance').innerText = perf.toFixed(1) + "%";
        document.getElementById('standingBadge').innerText = metrics.classification;
        document.getElementById('snapStanding').innerText = metrics.classification;
        updateStickySummary(metrics.final_gpa.toFixed(2), `${metrics.total_credits} Cr`, metrics.classification);
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

    // Build Charts & Subjects Table
    buildCharts();
    buildSubjectsTable();
}

function buildSubjectsTable() {
    let included = appData.filter(d => d.Include === true);
    const tbody = document.getElementById('homeSubjectsTbody');
    const badge = document.getElementById('homeSubjectsCount');
    tbody.innerHTML = '';
    badge.innerText = included.length + ' SUBJECTS';

    // Sort by level, then semester, then course title
    let sorted = [...included].sort((a, b) => {
        if (a.academic_level !== b.academic_level) return a.academic_level - b.academic_level;
        if (a.semester !== b.semester) return a.semester - b.semester;
        return (a.course_title || '').localeCompare(b.course_title || '');
    });

    let lastSem = null;
    sorted.forEach(d => {
        let semKey = `L${d.academic_level}-S${d.semester}`;
        if (semKey !== lastSem) {
            // Separator row for each new semester
            const sepRow = document.createElement('tr');
            sepRow.innerHTML = `<td colspan="5" class="sem-separator">Level ${d.academic_level} &nbsp;&mdash;&nbsp; Semester ${d.semester}</td>`;
            tbody.appendChild(sepRow);
            lastSem = semKey;
        }
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${d.course_title || '-'}</td>
            <td><span class="sem-label">L${d.academic_level}&thinsp;·&thinsp;S${d.semester}</span></td>
            <td>${d.credits}</td>
            <td><span class="grade-chip">${d.grade || '-'}</span></td>
            <td><span class="gpv-pill">${d.gpv}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function buildCharts() {
    let included = appData.filter(d => d.Include === true);
    
    // Shared responsive config for Plotly
    const chartConfig = {
        responsive: true,
        displayModeBar: false
    };

    // 1. Pie Chart (Grade Distribution)
    let grades = {};
    included.forEach(d => {
        let g = d.grade || 'Other';
        grades[g] = (grades[g] || 0) + 1;
    });
    
    let pieData = [{
        values: Object.values(grades),
        labels: Object.keys(grades),
        type: 'pie',
        hole: 0.42,
        textinfo: 'label+percent',
        textposition: 'inside',
        automargin: true,
        marker: { colors: ['#d96c34', '#e2875b', '#eba181', '#f3bcad', '#fbe7dc', '#8c8f9c', '#1a1c29', '#d1d4db'] }
    }];
    Plotly.newPlot('pieChart', pieData, {
        autosize: true,
        margin: {t: 15, b: 15, l: 15, r: 15},
        showlegend: false
    }, chartConfig);

    // 2. Line Chart (SGPA Trend)
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
        line: {color: '#d96c34', width: 2.5},
        marker: {size: 8, color: '#d96c34'}
    }];
    Plotly.newPlot('lineChart', lineData, {
        autosize: true,
        margin: {t: 30, b: 40, l: 35, r: 35}, 
        yaxis: {range: [0, 4.3], automargin: true},
        xaxis: {showgrid: false, automargin: true}
    }, chartConfig);

    // 3. Grade Bar Chart
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
        autosize: true,
        margin: {t: 20, b: 35, l: 35, r: 20},
        xaxis: {showgrid: false, automargin: true},
        yaxis: {title: 'Count', showgrid: true, gridcolor: 'rgba(235,128,68,0.1)', automargin: true}
    }, chartConfig);

    // 4. Sem Bar Chart
    let sXVals = Object.keys(semMap).sort();
    let sCreds = sXVals.map(k => semMap[k].cred);
    let sSubjs = sXVals.map(k => included.filter(d => `L${d.academic_level} - S${d.semester}` === k).length);

    let semBarData = [
        {x: sXVals, y: sCreds, type: 'bar', name: 'Credits', marker: {color: '#1a1c29'}, text: sCreds.map(String), textposition: 'auto'},
        {x: sXVals, y: sSubjs, type: 'bar', name: 'Subjects', marker: {color: '#d96c34'}, text: sSubjs.map(String), textposition: 'auto'}
    ];
    Plotly.newPlot('semBarChart', semBarData, {
        barmode: 'group',
        autosize: true,
        margin: {t: 20, b: 35, l: 35, r: 20},
        legend: {orientation: 'h', y: 1.15, x: 1, xanchor: 'right', yanchor: 'bottom'},
        xaxis: {showgrid: false, automargin: true},
        yaxis: {title: 'Count', showgrid: true, gridcolor: 'rgba(235,128,68,0.1)', automargin: true}
    }, chartConfig);

    // Initial resize pass after layout paints
    requestAnimationFrame(() => {
        triggerChartsResize();
    });
}

// Window resize & ResizeObserver listeners to keep charts 100% fluid & responsive
function triggerChartsResize() {
    ['pieChart', 'lineChart', 'gradeBarChart', 'semBarChart'].forEach(id => {
        const el = document.getElementById(id);
        if (el && el.data && window.Plotly) {
            Plotly.Plots.resize(el);
        }
    });
}

let chartResizeDebounce;
window.addEventListener('resize', () => {
    clearTimeout(chartResizeDebounce);
    chartResizeDebounce = setTimeout(triggerChartsResize, 100);
});

if (typeof ResizeObserver !== 'undefined') {
    const chartObserver = new ResizeObserver(() => {
        clearTimeout(chartResizeDebounce);
        chartResizeDebounce = setTimeout(triggerChartsResize, 100);
    });
    window.addEventListener('DOMContentLoaded', () => {
        const homePage = document.getElementById('page-home');
        if (homePage) chartObserver.observe(homePage);
        ['pieChart', 'lineChart', 'gradeBarChart', 'semBarChart'].forEach(id => {
            const el = document.getElementById(id);
            if (el) chartObserver.observe(el);
        });
    });
}

function renderDataTable() {
    document.getElementById('editEmptyState').style.display = 'none';
    document.getElementById('dataTableContainer').style.display = 'block';

    const tbody = document.querySelector('#masterDataTable tbody');
    tbody.innerHTML = '';

    if(appData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;">No courses available. Click "+ Add Course" to add one manually.</td></tr>';
        return;
    }

    appData.forEach((row, idx) => {
        let tr = document.createElement('tr');
        tr.className = 'course-tr-card';
        tr.innerHTML = `
            <td data-label="Include" class="col-chk">
                <label class="chk-container">
                    <input type="checkbox" data-idx="${idx}" class="chk-include" ${row.Include !== false ? 'checked' : ''}>
                    <span class="chk-label-text">Include</span>
                </label>
            </td>
            <td data-label="Lvl" class="col-lvl">
                <span class="mobile-cell-label">Level</span>
                <input type="text" data-idx="${idx}" class="edit-lvl" value="${escapeHtml(row.academic_level || '')}" placeholder="Lvl" aria-label="Level">
            </td>
            <td data-label="Sem" class="col-sem">
                <span class="mobile-cell-label">Sem</span>
                <input type="text" data-idx="${idx}" class="edit-sem" value="${escapeHtml(row.semester || '')}" placeholder="Sem" aria-label="Semester">
            </td>
            <td data-label="Code" class="col-code">
                <span class="mobile-cell-label">Course Code</span>
                <input type="text" data-idx="${idx}" class="edit-code" value="${escapeHtml(row.course_code || '')}" placeholder="e.g. IA 1201" aria-label="Course Code">
            </td>
            <td data-label="Title" class="col-title">
                <span class="mobile-cell-label">Course Title</span>
                <input type="text" data-idx="${idx}" class="edit-title" value="${escapeHtml(row.course_title || '')}" placeholder="Course Title" aria-label="Course Title">
            </td>
            <td data-label="Credits" class="col-crd">
                <span class="mobile-cell-label">Credits</span>
                <input type="number" data-idx="${idx}" class="edit-crd" value="${row.credits !== undefined ? row.credits : 0}" placeholder="Credits" aria-label="Credits">
            </td>
            <td data-label="GPV" class="col-gpv">
                <span class="mobile-cell-label">GPV</span>
                <input type="number" step="0.01" data-idx="${idx}" class="edit-gpv" value="${row.gpv !== undefined ? row.gpv : 0}" placeholder="GPV" aria-label="GPV">
            </td>
            <td data-label="Grade" class="col-grade">
                <span class="mobile-cell-label">Grade</span>
                <input type="text" data-idx="${idx}" class="edit-grade" value="${escapeHtml(row.grade || '')}" placeholder="Grade" aria-label="Grade">
            </td>
            <td data-label="Action" class="col-action">
                <button type="button" onclick="deleteCourse(${idx})" class="btn-delete-course" aria-label="Delete course ${idx + 1}">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                    <span>Delete</span>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.addNewCourse = function() {
    appData.push({
        Include: true,
        academic_level: "1",
        semester: "1",
        course_code: "NEW 1000",
        course_title: "New Subject",
        credits: 2,
        gpv: 0.0,
        grade: "--"
    });
    renderDataTable();
}

window.deleteCourse = function(idx) {
    if(confirm("Are you sure you want to delete this course?")) {
        appData.splice(idx, 1);
        renderDataTable();
        saveTableChanges(false); // background save
    }
}

window.saveTableChanges = function(showAlert = true) {
    const rows = document.querySelectorAll('#masterDataTable tbody tr');
    if (appData.length > 0 && rows.length === appData.length) {
        rows.forEach((tr, idx) => {
            appData[idx].Include = tr.querySelector('.chk-include').checked;
            appData[idx].academic_level = tr.querySelector('.edit-lvl').value;
            appData[idx].semester = tr.querySelector('.edit-sem').value;
            appData[idx].course_code = tr.querySelector('.edit-code').value;
            appData[idx].course_title = tr.querySelector('.edit-title').value;
            appData[idx].credits = parseFloat(tr.querySelector('.edit-crd').value) || 0;
            appData[idx].gpv = parseFloat(tr.querySelector('.edit-gpv').value) || 0;
            appData[idx].grade = tr.querySelector('.edit-grade').value;
        });
    }

    if(!currentUser) saveLocal();
    else saveCloud();
    
    if (showAlert) {
        alert("Changes saved locally. Dashboard metrics updated.");
    }
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
        let sems = [...new Set(included.filter(d => d.academic_level == lvl).map(d => d.semester))].sort();

        // Level heading
        let lvlEl = document.createElement('div');
        lvlEl.innerHTML = `<h3 class="sem-overview-level-title">Academic Level ${lvl}</h3>`;
        container.appendChild(lvlEl);

        // GPA summary cards row
        let cardsGrid = document.createElement('div');
        cardsGrid.className = `grid-${Math.min(sems.length, 4)}`;
        sems.forEach(sem => {
            let group = included.filter(d => d.academic_level == lvl && d.semester == sem);
            let sCred = group.reduce((sum, d) => sum + d.credits, 0);
            let sPts  = group.reduce((sum, d) => sum + (d.credits * d.gpv), 0);
            let sGpa  = sCred > 0 ? (sPts / sCred) : 0;
            let card  = document.createElement('div');
            card.className = 'ui-card';
            card.style.marginBottom = '0';
            card.innerHTML = `
                <div class="ui-card-header">SEM ${sem}</div>
                <div class="ui-card-body">
                    <div class="ui-card-value" style="color:#d96c34; font-size:1.8rem;">${sGpa.toFixed(4)}</div>
                </div>
                <div class="ui-card-subtext">CREDITS: ${sCred} &nbsp;·&nbsp; SUBJECTS: ${group.length}</div>`;
            cardsGrid.appendChild(card);
        });
        container.appendChild(cardsGrid);

        // Unified styled table for all sems in this level
        let tableWrap = document.createElement('div');
        tableWrap.className = 'ui-card home-subjects-card';
        tableWrap.style.cssText = 'margin-top:20px; padding:0;';

        // Count subjects in this level
        let lvlSubjects = included.filter(d => d.academic_level == lvl);

        tableWrap.innerHTML = `
            <div class="home-subjects-header">
                <span class="chart-card-title" style="padding:0; display:inline-block;">LEVEL ${lvl} — SUBJECTS</span>
                <span class="subjects-count-badge">${lvlSubjects.length} SUBJECTS</span>
            </div>
            <div class="table-responsive-container" style="margin-top:0; border-radius:0 0 1.5rem 1.5rem;">
                <table class="home-summary-table">
                    <thead>
                        <tr>
                            <th>Course</th>
                            <th>Sem</th>
                            <th>Cr</th>
                            <th>Grade</th>
                            <th>GPV</th>
                        </tr>
                    </thead>
                    <tbody id="semTbody-L${lvl}"></tbody>
                </table>
            </div>`;
        container.appendChild(tableWrap);

        let tbody = tableWrap.querySelector(`#semTbody-L${lvl}`);
        sems.forEach(sem => {
            let group = included.filter(d => d.academic_level == lvl && d.semester == sem);
            // Semester separator row
            let sepRow = document.createElement('tr');
            sepRow.innerHTML = `<td colspan="5" class="sem-separator">Semester ${sem}</td>`;
            tbody.appendChild(sepRow);
            // Subject rows
            group.forEach(d => {
                let tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${d.course_title || '-'}</td>
                    <td><span class="sem-label">L${d.academic_level}&thinsp;·&thinsp;S${d.semester}</span></td>
                    <td>${d.credits}</td>
                    <td><span class="grade-chip">${d.grade || '-'}</span></td>
                    <td><span class="gpv-pill">${d.gpv}</span></td>`;
                tbody.appendChild(tr);
            });
        });
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

// Helper: Escape HTML string
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Mobile Drawer Navigation
function initMobileDrawer() {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const backdrop = document.getElementById('sidebarBackdrop');
    const sidebar = document.getElementById('appSidebar');

    function openDrawer() {
        sidebar?.classList.add('open');
        backdrop?.classList.add('open');
        document.body.classList.add('drawer-open');
    }

    function closeDrawer() {
        sidebar?.classList.remove('open');
        backdrop?.classList.remove('open');
        document.body.classList.remove('drawer-open');
    }

    toggleBtn?.addEventListener('click', openDrawer);
    closeBtn?.addEventListener('click', closeDrawer);
    backdrop?.addEventListener('click', closeDrawer);
}

// Init
window.onload = () => {
    initMobileDrawer();
    loadLocal();
    navigateTo('home');
};
