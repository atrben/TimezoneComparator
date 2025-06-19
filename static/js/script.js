document.addEventListener('DOMContentLoaded', function() {
    // No drag and drop functionality needed anymore
    // Initialize checkbox label states on page load
    document.querySelectorAll('.checkbox-container input[type="checkbox"]').forEach(checkbox => {
        const label = checkbox.parentElement.querySelector('label');
        if (checkbox.checked) {
            label.classList.remove('checkbox-unchecked');
            label.classList.add('checkbox-checked');
        } else {
            label.classList.remove('checkbox-checked');
            label.classList.add('checkbox-unchecked');
        }
    });

    // Toggle checkbox label color based on checkbox state
    document.querySelectorAll('.checkbox-container input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const label = this.parentElement.querySelector('label');
            if (this.checked) {
                label.classList.remove('checkbox-unchecked');
                label.classList.add('checkbox-checked');
            } else {
                label.classList.remove('checkbox-checked');
                label.classList.add('checkbox-unchecked');
            }
        });
    });

    // Set default time for Compare Timezones to 9:00 AM if not already set
    if (!document.getElementById('base_time').value) {
        document.getElementById('base_time').value = '09:00';
    }

    // Load theme from localStorage on page load, default to dark if not set
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || !savedTheme) {
        toggleTheme();
    }
});

function compareTimezones() {
    const baseTimezone = document.getElementById('base_timezone').value;
    const manualTimezone = document.getElementById('manual_timezone').value.trim();
    const baseTime = document.getElementById('base_time').value;
    const customTimezones = document.getElementById('custom_timezones').value.trim();

    const tzToUse = manualTimezone || baseTimezone;

    fetch('/compare', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `base_timezone=${encodeURIComponent(tzToUse)}&base_time=${encodeURIComponent(baseTime)}&timezones=${encodeURIComponent(customTimezones)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        const tbody = document.querySelector('#results_table tbody');
        tbody.innerHTML = '';
        data.results.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.abbr}</td>
                <td>${result.timezone}</td>
                <td>${result.difference !== 'N/A' ? result.difference.toFixed(1) : 'N/A'}</td>
                <td>${result.current_time || 'N/A'}</td>
                <td>${result.count}</td>
                <td>${result.error || ''}</td>
            `;
            tbody.appendChild(row);
        });
        // Enable export button if there are results
        document.getElementById('export_comparison_btn').disabled = data.results.length === 0;
    })
    .catch(error => console.error('Error:', error));
}

function setLocalTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('base_time').value = `${hours}:${minutes}`;
}

function calculateShiftHours() {
    const baseTimezone = document.getElementById('base_timezone').value;
    const manualTimezone = document.getElementById('manual_timezone').value.trim();
    const baseTime = document.getElementById('base_time').value;
    const customTimezones = document.getElementById('custom_timezones').value.trim();

    const tzToUse = manualTimezone || baseTimezone;

    fetch('/calculate_shift', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `base_timezone=${encodeURIComponent(tzToUse)}&base_time=${encodeURIComponent(baseTime)}&timezones=${encodeURIComponent(customTimezones)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        const tbody = document.querySelector('#shift_table tbody');
        tbody.innerHTML = '';
        data.results.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.abbr}</td>
                <td>${result.timezone}</td>
                <td class="time-left" data-hours="${result.hours_left}" data-minutes="${result.minutes_left}" data-count="${result.count}">${typeof result.hours_left === 'string' ? result.hours_left : result.hours_left.toFixed(1)}</td>
                <td>${result.shift_end_time || 'N/A'}</td>
                <td>${result.count}</td>
            `;
            tbody.appendChild(row);
        });
        // Enable export button if there are results
        document.getElementById('export_shift_btn').disabled = data.results.length === 0;
        // Apply hiding of ended shifts if checkbox is checked
        toggleHideShiftEnded();
    })
    .catch(error => console.error('Error:', error));
}

function exportComparisonResults() {
    const tbody = document.querySelector('#results_table tbody');
    let csvContent = 'Abbreviation,Timezone,Time Difference (hrs),Current Time,Count\n';
    for (const row of tbody.rows) {
        csvContent += Array.from(row.cells).map(cell => cell.textContent).join(',') + '\n';
    }
    downloadCSV(csvContent, 'comparison_results.csv');
}

function exportShiftResults() {
    const tbody = document.querySelector('#shift_table tbody');
    const isMinutes = document.querySelector('#toggle_time_unit')?.checked || false;
    let csvContent = 'Abbreviation,Timezone,' + (isMinutes ? 'Minutes Left in Shift' : 'Hours Left in Shift') + ',Shift End Time,Count\n';
    for (const row of tbody.rows) {
        csvContent += Array.from(row.cells).map(cell => cell.textContent).join(',') + '\n';
    }
    downloadCSV(csvContent, 'shift_hours_results.csv');
}

function exportLeadTimeResults() {
    const totalMinutes = document.getElementById('total_minutes').textContent;
    const tasksPerMember = document.getElementById('tasks_per_member').textContent;
    const totalTasks = document.getElementById('total_tasks').textContent;
    const taskDuration = document.getElementById('task_duration').value;
    let csvContent = 'Total Available Minutes,Tasks per Team Member,Total Tasks Team Can Produce,Task Duration (minutes)\n';
    csvContent += `${totalMinutes},${tasksPerMember},${totalTasks},${taskDuration}\n`;
    downloadCSV(csvContent, 'lead_time_results.csv');
    // Enable export button only if there are results
    document.getElementById('export_lead_time_btn').disabled = parseInt(totalMinutes) === 0;
}

function exportTaskProductionToCsv() {
    const totalMinutes = document.querySelector('#task_production_results p:nth-child(2)').textContent.split(': ')[1];
    const averageTasksPerMember = document.querySelector('#task_production_results p:nth-child(3)').textContent.split(': ')[1];
    const totalTasks = document.querySelector('#task_production_results p:nth-child(4)').textContent.split(': ')[1];
    const taskDuration = document.getElementById('task_duration').value;
    const productivityRate = document.getElementById('productivityRate').value;
    let csvContent = 'Total Available Minutes,Average Tasks per Team Member,Total Tasks Team Can Produce,Task Duration (minutes),Productivity Rate (%)\n';
    csvContent += `${totalMinutes},${averageTasksPerMember},${totalTasks},${taskDuration},${productivityRate}\n`;
    downloadCSV(csvContent, 'task_production_results.csv');
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function resetCompare() {
    document.getElementById('base_timezone').selectedIndex = 0;
    document.getElementById('manual_timezone').value = '';
    document.getElementById('base_time').value = '';
    document.getElementById('custom_timezones').value = '';
    const tbody = document.querySelector('#results_table tbody');
    tbody.innerHTML = '';
    document.getElementById('export_comparison_btn').disabled = true;
}

function resetShift() {
    const tbody = document.querySelector('#shift_table tbody');
    tbody.innerHTML = '';
    document.getElementById('export_shift_btn').disabled = true;
}

function resetAll() {
    document.getElementById('base_timezone').selectedIndex = 0;
    document.getElementById('manual_timezone').value = '';
    document.getElementById('base_time').value = '';
    document.getElementById('custom_timezones').value = '';
    document.querySelector('#results_table tbody').innerHTML = '';
    document.querySelector('#shift_table tbody').innerHTML = '';
    document.getElementById('export_comparison_btn').disabled = true;
    document.getElementById('export_shift_btn').disabled = true;
}

function toggleTimeUnit() {
    const isMinutes = document.getElementById('toggle_time_unit').checked;
    const isTotalCount = document.getElementById('toggle_total_count').checked;
    const timeCells = document.querySelectorAll('#shift_table .time-left');
    timeCells.forEach(cell => {
        const hours = cell.getAttribute('data-hours');
        const minutes = cell.getAttribute('data-minutes');
        const count = parseInt(cell.getAttribute('data-count'), 10);
        if (isMinutes) {
            if (minutes === 'Shift Ended' || minutes === 'N/A') {
                cell.textContent = minutes;
            } else {
                const minValue = Math.round(parseFloat(minutes));
                cell.textContent = isTotalCount ? (minValue * count) : minValue;
            }
        } else {
            if (hours === 'Shift Ended' || hours === 'N/A') {
                cell.textContent = hours;
            } else {
                const hrValue = parseFloat(hours);
                cell.textContent = isTotalCount ? (hrValue * count).toFixed(1) : hrValue.toFixed(1);
            }
        }
    });
    // Update the column header
    const header = document.querySelector('#shift_table thead tr th:nth-child(3)');
    header.textContent = isMinutes ? 'Minutes Left in Shift' : 'Hours Left in Shift';
    if (isTotalCount) {
        header.textContent += ' (Total)';
    }
    // Ensure hiding of ended shifts is applied
    toggleHideShiftEnded();
}

function toggleTotalCount() {
    toggleTimeUnit(); // Reuse the same logic to update display
}

function toggleHideShiftEnded() {
    const hideEnded = document.getElementById('hide_shift_ended').checked;
    const rows = document.querySelectorAll('#shift_table tbody tr');
    rows.forEach(row => {
        const timeCell = row.querySelector('.time-left');
        const hours = timeCell.getAttribute('data-hours');
        if (hideEnded && (hours === 'Shift Ended' || hours === 'N/A')) {
            row.style.display = 'none';
        } else {
            row.style.display = '';
        }
    });
}

function calculateTaskProduction() {
    const timeCells = document.querySelectorAll('#shift_table .time-left');
    let totalMinutes = 0;
    let memberMinutes = [];
    timeCells.forEach(cell => {
        const minutes = cell.getAttribute('data-minutes');
        const count = parseInt(cell.getAttribute('data-count'), 10);
        if (minutes !== 'Shift Ended' && minutes !== 'N/A') {
            const mins = parseFloat(minutes);
            totalMinutes += mins * count;
            for (let i = 0; i < count; i++) {
                memberMinutes.push(mins);
            }
        }
    });
    const taskDuration = parseFloat(document.getElementById('task_duration').value);
    const productivityRate = parseFloat(document.getElementById('productivityRate').value) / 100;
    if (!isNaN(totalMinutes) && !isNaN(taskDuration) && taskDuration > 0) {
        const tasksPerMember = memberMinutes.map(mins => Math.floor(mins / taskDuration));
        const totalTasksBeforeProductivity = tasksPerMember.reduce((a, b) => a + b, 0);
        const totalTasks = Math.floor(totalTasksBeforeProductivity * productivityRate);
        const averageTasksPerMember = memberMinutes.length > 0 ? (totalTasks / memberMinutes.length).toFixed(1) : 0;
        let resultHtml = '<h3>Expected Task Production:</h3>';
        resultHtml += `<p>Total Available Minutes: ${Math.round(totalMinutes)}</p>`;
        resultHtml += `<p>Average Tasks per Team Member: ${averageTasksPerMember}</p>`;
        resultHtml += `<p>Total Tasks Team Can Produce: ${totalTasks}</p>`;
        resultHtml += '<h3>Math Breakdown:</h3>';
        resultHtml += '<ul style="list-style-type: none; padding-left: 0;">';
        resultHtml += `<li>Total Available Minutes = ${Math.round(totalMinutes)} (sum of minutes left for each team member)</li>`;
        resultHtml += `<li>Task Duration = ${taskDuration} minutes</li>`;
        resultHtml += `<li>Productivity Rate = ${productivityRate * 100}%</li>`;
        resultHtml += '<li>Tasks per Team Member = Available Minutes for each member / Task Duration</li>';
        resultHtml += `<li>Total Tasks Before Productivity = Sum of tasks per team member = ${totalTasksBeforeProductivity}</li>`;
        resultHtml += `<li>Total Tasks Team Can Produce = Total Tasks Before Productivity * Productivity Rate = ${totalTasks}</li>`;
        resultHtml += `<li>Average Tasks per Member = Total Tasks / Number of Members = ${averageTasksPerMember}</li>`;
        resultHtml += '</ul>';
        resultHtml += '<button onclick="exportTaskProductionToCsv()" style="background-color: darkgreen; color: white;">Export to CSV</button>';
        document.getElementById('task_production_results').innerHTML = resultHtml;
    } else {
        document.getElementById('task_production_results').innerHTML = '<p>Please enter valid numbers for task duration and ensure shift results are calculated.</p>';
    }
}

document.getElementById('compare-btn').addEventListener('click', function(e) {
    e.preventDefault();
    compareTimezones();
    calculateShiftHours();
});

function toggleTheme() {
    const body = document.body;
    const container = document.querySelector('.container');
    const h1 = document.querySelector('h1');
    const h2s = document.querySelectorAll('h2');
    const labels = document.querySelectorAll('label');
    const selects = document.querySelectorAll('select');
    const inputs = document.querySelectorAll('input');
    const textareas = document.querySelectorAll('textarea');
    const buttons = document.querySelectorAll('button');
    const tables = document.querySelectorAll('table');
    const ths = document.querySelectorAll('th');
    const tds = document.querySelectorAll('td');
    const dropZones = document.querySelectorAll('.drop-zone');
    
    body.classList.toggle('dark-theme');
    container.classList.toggle('dark-theme');
    h1.classList.toggle('dark-theme');
    h2s.forEach(h2 => h2.classList.toggle('dark-theme'));
    labels.forEach(label => label.classList.toggle('dark-theme'));
    selects.forEach(select => select.classList.toggle('dark-theme'));
    inputs.forEach(input => input.classList.toggle('dark-theme'));
    textareas.forEach(textarea => textarea.classList.toggle('dark-theme'));
    buttons.forEach(button => button.classList.toggle('dark-theme'));
    tables.forEach(table => table.classList.toggle('dark-theme'));
    ths.forEach(th => th.classList.toggle('dark-theme'));
    tds.forEach(td => td.classList.toggle('dark-theme'));
    dropZones.forEach(zone => zone.classList.toggle('dark-theme'));
    
    // Save the current theme to localStorage
    const isDark = body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function showInstructions() {
    const modal = document.getElementById('instructionsModal');
    modal.style.display = 'block';
}

function closeInstructions() {
    const modal = document.getElementById('instructionsModal');
    modal.style.display = 'none';
}

// Close modal if user clicks outside of it
window.onclick = function(event) {
    const instructionsModal = document.getElementById('instructionsModal');
    const downloadModal = document.getElementById('downloadPasswordModal');
    const codePasswordModal = document.getElementById('codePasswordModal');
    const codeModal = document.getElementById('codeModal');
    if (event.target == instructionsModal) {
        instructionsModal.style.display = 'none';
    }
    if (event.target == downloadModal) {
        downloadModal.style.display = 'none';
    }
    if (event.target == codePasswordModal) {
        codePasswordModal.style.display = 'none';
    }
    if (event.target == codeModal) {
        codeModal.style.display = 'none';
    }
}

function showDownloadPasswordPrompt() {
    const modal = document.getElementById('downloadPasswordModal');
    modal.style.display = 'block';
    document.getElementById('passwordError').style.display = 'none';
    document.getElementById('downloadPassword').value = '';
}

function closeDownloadPasswordPrompt() {
    const modal = document.getElementById('downloadPasswordModal');
    modal.style.display = 'none';
}

function checkDownloadPassword() {
    const password = document.getElementById('downloadPassword').value;
    const correctPassword = 'Grok420.69';
    if (password === correctPassword) {
        closeDownloadPasswordPrompt();
        initiateDownload();
    } else {
        document.getElementById('passwordError').style.display = 'block';
    }
}

function initiateDownload() {
    // Placeholder for actual download logic
    // In a real scenario, this would trigger a server-side script to create and serve a zip file
    alert('Password correct! Initiating download of Timezone & Shift Calculator assets...');
    window.location.href = '/download_assets';
}

function showCodePasswordPrompt() {
    const modal = document.getElementById('codePasswordModal');
    modal.style.display = 'block';
    document.getElementById('codePasswordError').style.display = 'none';
    document.getElementById('codePassword').value = '';
}

function closeCodePasswordPrompt() {
    const modal = document.getElementById('codePasswordModal');
    modal.style.display = 'none';
}

function checkCodePassword() {
    const password = document.getElementById('codePassword').value;
    const correctPassword = 'Grok420.69';
    if (password === correctPassword) {
        closeCodePasswordPrompt();
        fetchCode();
    } else {
        document.getElementById('codePasswordError').style.display = 'block';
    }
}

function fetchCode() {
    const codeContent = document.getElementById('codeContent');
    codeContent.innerHTML = '<p>Loading code...</p>';
    const modal = document.getElementById('codeModal');
    modal.style.display = 'block';
    
    // List of files to fetch
    const files = [
        {path: 'app.py', title: 'app.py'},
        {path: 'templates/index.html', title: 'templates/index.html'},
        {path: 'static/js/script.js', title: 'static/js/script.js'},
        {path: 'static/css/style.css', title: 'static/css/style.css'}
    ];
    
    let contentHtml = '';
    let loaded = 0;
    
    files.forEach(file => {
        fetch(`/get_code/${file.path}`)
            .then(response => {
                if (!response.ok) throw new Error('File not found');
                return response.text();
            })
            .then(data => {
                contentHtml += `<h3>${file.title}</h3>
<pre style="background-color: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; font-family: monospace;">${escapeHtml(data)}</pre>`;
                loaded++;
                if (loaded === files.length) {
                    codeContent.innerHTML = contentHtml;
                }
            })
            .catch(error => {
                contentHtml += `<h3>${file.title}</h3>
<p style="color: red;">Error loading file: ${error.message}</p>`;
                loaded++;
                if (loaded === files.length) {
                    codeContent.innerHTML = contentHtml;
                }
            });
    });
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function closeCodeModal() {
    const modal = document.getElementById('codeModal');
    modal.style.display = 'none';
}

function getAllCode() { return ''; }
function getAppPyCode() { return ''; }
function getIndexHtmlCode() { return ''; }
function getScriptJsCode() { return ''; }
function getStyleCssCode() { return ''; }
