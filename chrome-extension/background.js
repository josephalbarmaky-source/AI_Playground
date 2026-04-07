/**
 * Meeting Assistant - Background Service Worker
 * Manages tab audio capture, screenshots, and communication with Flask backend.
 */

const BACKEND_URL = 'http://localhost:5000';

let isRecording = false;
let meetingId = null;
let mediaRecorder = null;
let captureStream = null;
let screenshotInterval = null;
let startTime = null;
let audioChunkInterval = 5000; // 5 seconds per audio chunk
let screenshotIntervalMs = 30000; // 30 seconds per screenshot

// Open side panel when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
    chrome.sidePanel.open({ tabId: tab.id });
});

// Enable side panel on Teams tabs
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (tab.url && tab.url.includes('teams.microsoft.com')) {
        chrome.sidePanel.setOptions({
            tabId,
            path: 'sidepanel.html',
            enabled: true
        });
    }
});

// Handle messages from the side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
        case 'START_RECORDING':
            startRecording(message.title, message.meetingType)
                .then(result => sendResponse(result))
                .catch(err => sendResponse({ error: err.message }));
            return true; // async response

        case 'STOP_RECORDING':
            stopRecording()
                .then(result => sendResponse(result))
                .catch(err => sendResponse({ error: err.message }));
            return true;

        case 'GET_STATUS':
            sendResponse({
                isRecording,
                meetingId,
                elapsed: startTime ? (Date.now() - startTime) / 1000 : 0
            });
            return false;
    }
});


async function startRecording(title, meetingType) {
    if (isRecording) {
        return { error: 'Already recording' };
    }

    // Create meeting on backend
    try {
        const resp = await fetch(`${BACKEND_URL}/api/meetings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title || 'Untitled Meeting',
                meeting_type: meetingType || 'work',
                platform: 'teams'
            })
        });
        const meeting = await resp.json();
        meetingId = meeting.id;
    } catch (err) {
        return { error: `Cannot connect to backend: ${err.message}` };
    }

    // Capture tab audio
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id });

        captureStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                mandatory: {
                    chromeMediaSource: 'tab',
                    chromeMediaSourceId: streamId
                }
            },
            video: false
        });

        // Set up MediaRecorder for chunked audio
        mediaRecorder = new MediaRecorder(captureStream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        startTime = Date.now();
        isRecording = true;

        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0 && meetingId) {
                const elapsed = (Date.now() - startTime) / 1000;
                const reader = new FileReader();
                reader.onloadend = async () => {
                    const base64 = reader.result.split(',')[1];
                    try {
                        await fetch(`${BACKEND_URL}/api/meetings/${meetingId}/audio`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                audio: base64,
                                elapsed_sec: elapsed
                            })
                        });
                    } catch (err) {
                        console.error('Failed to send audio chunk:', err);
                    }
                };
                reader.readAsDataURL(event.data);
            }
        };

        mediaRecorder.start(audioChunkInterval);

        // Start screenshot interval
        screenshotInterval = setInterval(() => captureScreenshot(), screenshotIntervalMs);

        // Notify the side panel
        chrome.runtime.sendMessage({
            type: 'RECORDING_STARTED',
            meetingId,
            title: title
        }).catch(() => {}); // ignore if panel isn't open

        return { success: true, meetingId };

    } catch (err) {
        isRecording = false;
        meetingId = null;
        return { error: `Capture failed: ${err.message}` };
    }
}


async function stopRecording() {
    if (!isRecording) {
        return { error: 'Not recording' };
    }

    // Stop media recorder
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }

    // Stop capture stream
    if (captureStream) {
        captureStream.getTracks().forEach(track => track.stop());
        captureStream = null;
    }

    // Stop screenshot interval
    if (screenshotInterval) {
        clearInterval(screenshotInterval);
        screenshotInterval = null;
    }

    // End meeting on backend
    const endedMeetingId = meetingId;
    if (endedMeetingId) {
        try {
            await fetch(`${BACKEND_URL}/api/meetings/${endedMeetingId}/end`, {
                method: 'PUT'
            });
        } catch (err) {
            console.error('Failed to end meeting on backend:', err);
        }
    }

    isRecording = false;
    meetingId = null;
    startTime = null;
    mediaRecorder = null;

    chrome.runtime.sendMessage({
        type: 'RECORDING_STOPPED',
        meetingId: endedMeetingId
    }).catch(() => {});

    return { success: true, meetingId: endedMeetingId };
}


async function captureScreenshot() {
    if (!isRecording || !meetingId) return;

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
        const base64 = dataUrl.split(',')[1];
        const elapsed = (Date.now() - startTime) / 1000;

        await fetch(`${BACKEND_URL}/api/meetings/${meetingId}/screenshot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: base64,
                elapsed_sec: elapsed
            })
        });

        // Notify side panel
        chrome.runtime.sendMessage({
            type: 'SCREENSHOT_TAKEN',
            elapsed
        }).catch(() => {});

    } catch (err) {
        console.error('Screenshot failed:', err);
    }
}
