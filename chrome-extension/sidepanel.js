/**
 * Meeting Assistant — Side Panel
 * Shows live transcript, allows Q&A, and controls recording.
 */

const BACKEND_URL = 'http://localhost:5000';

let isRecording = false;
let meetingId = null;
let timerInterval = null;
let startTime = null;
let segmentCount = 0;
let screenshotCountNum = 0;
let pollingInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check current recording status
    chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
        if (response && response.isRecording) {
            isRecording = true;
            meetingId = response.meetingId;
            startTime = Date.now() - (response.elapsed * 1000);
            showRecordingUI();
            startTimer();
            startTranscriptPolling();
        }
    });
});

// Listen for messages from background
chrome.runtime.onMessage.addListener((message) => {
    switch (message.type) {
        case 'RECORDING_STARTED':
            meetingId = message.meetingId;
            isRecording = true;
            showRecordingUI();
            break;

        case 'RECORDING_STOPPED':
            isRecording = false;
            showSetupUI();
            if (message.meetingId) {
                showCompletionMessage(message.meetingId);
            }
            break;

        case 'TRANSCRIPT_UPDATE':
            addTranscriptSegment(message.text, message.timestamp_sec);
            break;

        case 'SCREENSHOT_TAKEN':
            screenshotCountNum++;
            document.getElementById('screenshotCount').textContent = `${screenshotCountNum} screenshots`;
            break;
    }
});


async function startRecording() {
    const title = document.getElementById('meetingTitle').value || 'Untitled Meeting';
    const type = document.getElementById('meetingType').value;

    const startBtn = document.getElementById('startBtn');
    startBtn.textContent = 'Starting...';
    startBtn.disabled = true;

    chrome.runtime.sendMessage({
        type: 'START_RECORDING',
        title,
        meetingType: type
    }, (response) => {
        startBtn.textContent = 'Start Recording';
        startBtn.disabled = false;

        if (response && response.error) {
            alert('Failed to start: ' + response.error);
            return;
        }

        if (response && response.success) {
            meetingId = response.meetingId;
            isRecording = true;
            startTime = Date.now();
            showRecordingUI();
            startTimer();
            startTranscriptPolling();
        }
    });
}


async function stopRecording() {
    const stopBtn = document.getElementById('stopBtn');
    stopBtn.textContent = 'Stopping...';
    stopBtn.disabled = true;

    chrome.runtime.sendMessage({ type: 'STOP_RECORDING' }, (response) => {
        stopBtn.textContent = 'Stop Recording';
        stopBtn.disabled = false;

        isRecording = false;
        stopTimer();
        stopTranscriptPolling();
        showSetupUI();

        if (response && response.meetingId) {
            showCompletionMessage(response.meetingId);
        }
    });
}


function showRecordingUI() {
    document.getElementById('setupSection').style.display = 'none';
    document.getElementById('recordingSection').style.display = 'block';
    document.getElementById('recordingIndicator').style.display = 'flex';
}


function showSetupUI() {
    document.getElementById('setupSection').style.display = 'block';
    document.getElementById('recordingSection').style.display = 'none';
    document.getElementById('recordingIndicator').style.display = 'none';
    segmentCount = 0;
    screenshotCountNum = 0;
}


function showCompletionMessage(mid) {
    const area = document.getElementById('transcriptArea');
    area.innerHTML = `
        <div class="completion-message">
            <p><strong>Meeting ended!</strong></p>
            <p>Notes are being generated...</p>
            <a href="${BACKEND_URL}/meetings/${mid}" target="_blank" class="view-link">
                View Meeting Notes
            </a>
        </div>`;
}


// Timer
function startTimer() {
    if (!startTime) startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimer() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const h = Math.floor(elapsed / 3600);
    const m = Math.floor((elapsed % 3600) / 60);
    const s = elapsed % 60;
    document.getElementById('timer').textContent =
        `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}


// Transcript polling (fallback for when SocketIO isn't available in extension)
function startTranscriptPolling() {
    pollingInterval = setInterval(fetchLatestTranscript, 3000);
}

function stopTranscriptPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

async function fetchLatestTranscript() {
    if (!meetingId) return;
    try {
        const resp = await fetch(`${BACKEND_URL}/api/meetings/${meetingId}`);
        const data = await resp.json();
        const transcripts = data.transcripts || [];

        if (transcripts.length > segmentCount) {
            const newSegments = transcripts.slice(segmentCount);
            newSegments.forEach(s => addTranscriptSegment(s.text, s.timestamp_sec));
            segmentCount = transcripts.length;
        }

        // Update screenshot count
        screenshotCountNum = data.screenshot_count || 0;
        document.getElementById('screenshotCount').textContent = `${screenshotCountNum} screenshots`;

    } catch (err) {
        console.error('Polling failed:', err);
    }
}


function addTranscriptSegment(text, timestampSec) {
    const area = document.getElementById('transcriptArea');

    // Remove placeholder
    const placeholder = area.querySelector('.placeholder');
    if (placeholder) placeholder.remove();

    const seg = document.createElement('div');
    seg.className = 'transcript-segment';

    const time = document.createElement('span');
    time.className = 'seg-time';
    time.textContent = formatTime(timestampSec);

    const txt = document.createElement('span');
    txt.className = 'seg-text';
    txt.textContent = text;

    seg.appendChild(time);
    seg.appendChild(txt);
    area.appendChild(seg);

    // Auto-scroll
    area.scrollTop = area.scrollHeight;

    segmentCount++;
    document.getElementById('segmentCount').textContent = `${segmentCount} segments`;
}


// Q&A Chat
async function sendQuestion() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    if (!question || !meetingId) return;

    const chatArea = document.getElementById('chatArea');

    const qBubble = document.createElement('div');
    qBubble.className = 'chat-bubble question';
    qBubble.textContent = question;
    chatArea.appendChild(qBubble);

    input.value = '';

    const aBubble = document.createElement('div');
    aBubble.className = 'chat-bubble answer';
    aBubble.textContent = 'Thinking...';
    chatArea.appendChild(aBubble);
    chatArea.scrollTop = chatArea.scrollHeight;

    try {
        const resp = await fetch(`${BACKEND_URL}/api/meetings/${meetingId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await resp.json();
        aBubble.textContent = data.answer || 'No answer available.';
    } catch {
        aBubble.textContent = 'Failed to get answer. Is the backend running?';
    }
    chatArea.scrollTop = chatArea.scrollHeight;
}


// Manual screenshot trigger
async function takeScreenshot() {
    if (!meetingId) return;
    // The background handles the actual capture
    chrome.runtime.sendMessage({ type: 'TAKE_SCREENSHOT' });
}


function formatTime(seconds) {
    if (!seconds && seconds !== 0) return '00:00';
    const s = Math.round(seconds);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}
