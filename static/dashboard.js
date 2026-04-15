const dashboardLabels = globalThis.dashboardLabels || {};

function formatScenarioName(rawName) {
    if (!rawName) {
        return '';
    }

    const map = {
        email: dashboardLabels.email || 'Email',
        internet: dashboardLabels.internet || 'Internet',
        sms: dashboardLabels.sms || 'SMS',
        call: dashboardLabels.call || 'Call',
        web: dashboardLabels.web || 'Web',
        desktop: dashboardLabels.desktop || 'Desktop',
        mobile: dashboardLabels.mobile || 'Mobile'
    };

    return rawName
        .split('_')
        .map(part => map[part] || part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

function formatSeconds(totalSeconds) {
    const seconds = Number(totalSeconds || 0);
    if (seconds < 60) {
        return `${seconds} ${dashboardLabels.seconds || 'seconds'}`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainder = seconds % 60;
    const minuteLabel = minutes === 1
        ? (dashboardLabels.minute || 'minute')
        : (dashboardLabels.minutes || 'minutes');

    if (!remainder) {
        return `${minutes} ${minuteLabel}`;
    }

    return `${minutes} ${minuteLabel} ${remainder}s`;
}

function escapeHtml(value) {
    return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function fetchJson(url) {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) {
        throw new Error(`Request failed for ${url}`);
    }
    return response.json();
}

function renderOverview(metrics) {
    document.getElementById('totalAttempts').textContent = metrics.total_attempts ?? 0;
    document.getElementById('successRate').textContent = `${metrics.overall_success_rate ?? 0}%`;
    document.getElementById('timeSpent').textContent = formatSeconds(metrics.total_time_spent_seconds);
    document.getElementById('indicatorsFound').textContent = metrics.total_indicators_identified ?? 0;
}

function renderPerformance(items) {
    const container = document.getElementById('performanceList');
    if (!items?.length) {
        container.className = 'stackList emptyState';
        container.textContent = dashboardLabels.noPerformance || 'No performance data yet.';
        return;
    }

    container.className = 'stackList';
    container.innerHTML = items.map(item => `
        <article class="performanceItem">
            <div class="performanceTop">
                <strong>${escapeHtml(formatScenarioName(item.scenario_type))}</strong>
                <span class="pillTag">${escapeHtml(item.success_rate)}%</span>
            </div>
            <div class="performanceMeta">
                <span>${escapeHtml(item.total_attempts)} ${escapeHtml(dashboardLabels.attempts || 'attempts')}</span>
                <span>${escapeHtml(item.correct_attempts)} ${escapeHtml(dashboardLabels.correct || 'correct')}</span>
                <span>${escapeHtml(dashboardLabels.avgTime || 'Avg. time')}: ${escapeHtml(formatSeconds(item.avg_duration_seconds))}</span>
                <span>${escapeHtml(item.critical_indicators_found)} ${escapeHtml(dashboardLabels.indicatorsFound || 'Indicators Found')}</span>
            </div>
        </article>
    `).join('');
}

function renderProgress(modules) {
    const container = document.getElementById('moduleProgressList');
    if (!modules?.length) {
        container.className = 'stackList emptyState';
        container.textContent = dashboardLabels.noProgress || 'No module progress yet.';
        return;
    }

    container.className = 'stackList';
    container.innerHTML = modules.map(module => {
        const percentage = Number(module.completion_percentage || 0);
        return `
            <article class="progressItem">
                <div class="progressTop">
                    <strong>${escapeHtml(formatScenarioName(module.module_name))}</strong>
                    <span class="pillTag">${percentage}%</span>
                </div>
                <div class="performanceMeta">
                    <span>${escapeHtml(module.completed)} / ${escapeHtml(module.total)} ${escapeHtml(dashboardLabels.completed || 'completed')}</span>
                </div>
                <div class="progressBar"><span style="width:${Math.min(percentage, 100)}%"></span></div>
            </article>
        `;
    }).join('');
}

function renderAttempts(attempts) {
    const container = document.getElementById('attemptHistoryList');
    if (!attempts?.length) {
        container.className = 'stackList emptyState';
        container.textContent = dashboardLabels.noAttempts || 'No attempts recorded yet.';
        container.style.maxHeight = '';
        container.style.overflowY = '';
        return;
    }

    container.className = 'stackList';
    container.innerHTML = attempts.map(attempt => `
        <article class="attemptItem">
            <div class="attemptTop">
                <strong>${escapeHtml(formatScenarioName(attempt.scenario_type))}</strong>
                <span class="pillTag">${escapeHtml(dashboardLabels.difficultyLevel || 'Level')} ${escapeHtml(attempt.difficulty)}</span>
            </div>
            <div class="attemptMeta">
                <span>${attempt.correct ? 'Correct' : 'Incorrect'}</span>
                <span>${escapeHtml(formatSeconds(attempt.duration_seconds))}</span>
                <span>${escapeHtml(attempt.timestamp || dashboardLabels.justNow || 'just now')}</span>
            </div>
        </article>
    `).join('');

    const attemptCards = Array.from(container.querySelectorAll('.attemptItem'));
    if (attemptCards.length > 5) {
        const styles = getComputedStyle(container);
        const gap = Number.parseFloat(styles.rowGap || styles.gap || '0') || 0;
        const visibleCards = attemptCards.slice(0, 5);
        const visibleHeight = visibleCards.reduce((sum, card) => sum + card.offsetHeight, 0) + gap * 4;

        container.style.maxHeight = `${Math.ceil(visibleHeight)}px`;
        container.style.overflowY = 'auto';
    } else {
        container.style.maxHeight = '';
        container.style.overflowY = '';
    }
}

function renderDifficulty(items) {
    const container = document.getElementById('difficultyList');
    if (!items?.length) {
        container.className = 'difficultyGrid emptyState';
        container.textContent = dashboardLabels.noDifficulty || 'Difficulty data unavailable.';
        return;
    }

    container.className = 'difficultyGrid';
    container.innerHTML = items.map(item => `
        <article class="difficultyItem">
            <strong>${escapeHtml(formatScenarioName(item.scenario))}</strong>
            <div class="performanceMeta">
                <span>${escapeHtml(dashboardLabels.difficultyLevel || 'Level')} ${escapeHtml(item.current_difficulty)}</span>
            </div>
        </article>
    `).join('');
}

async function loadDashboardAnalytics() {
    try {
        const [performance, progress, attempts, learning] = await Promise.all([
            fetchJson('/api/user_performance'),
            fetchJson('/api/module_progress'),
            fetchJson('/api/attempt_history?limit=50'),
            fetchJson('/api/learning_metrics')
        ]);

        renderOverview(learning.metrics || {});
        renderPerformance(performance.data || []);
        renderProgress(progress.modules || []);
        renderAttempts(attempts.attempts || []);
        renderDifficulty(learning.metrics?.difficulty_progression || []);
    } catch (error) {
        console.error('Dashboard analytics failed to load:', error);
        const fallbackMessage = dashboardLabels.loadingAnalytics || 'Analytics are unavailable right now.';
        ['performanceList', 'moduleProgressList', 'attemptHistoryList', 'difficultyList'].forEach(id => {
            const node = document.getElementById(id);
            if (node) {
                node.className = node.id === 'difficultyList' ? 'difficultyGrid emptyState' : 'stackList emptyState';
                node.textContent = fallbackMessage;
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', loadDashboardAnalytics);