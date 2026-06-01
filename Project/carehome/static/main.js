// ── Caregiver dashboard helpers ───────────────────────────────────────────────

function refreshAlerts() {
  fetch('/alerts')
    .then(r => r.json())
    .then(alerts => {
      const list  = document.getElementById('alert-list');
      const badge = document.getElementById('alert-count');
      if (!list) return;

      if (alerts.length === 0) {
        list.innerHTML = '<li class="empty">No active alerts</li>';
        if (badge) badge.textContent = '';
        return;
      }

      if (badge) badge.textContent = alerts.length;
      list.innerHTML = alerts.map(a => `
        <li class="alert-item ${a.severity}">
          <div class="alert-msg">
            <strong>[${a.severity.toUpperCase()}]</strong> ${a.message}
          </div>
          <span class="alert-time">${fmtTime(a.created_at)}</span>
          <button class="ack-btn" onclick="ackAlert(${a.id}, this)">Dismiss</button>
        </li>
      `).join('');
    });
}

function ackAlert(id, btn) {
  fetch(`/alerts/${id}/ack`, { method: 'POST' })
    .then(() => {
      btn.closest('li').remove();
      const list  = document.getElementById('alert-list');
      const badge = document.getElementById('alert-count');
      if (list && list.children.length === 0) {
        list.innerHTML = '<li class="empty">No active alerts</li>';
        if (badge) badge.textContent = '';
      } else if (badge) {
        badge.textContent = parseInt(badge.textContent || 0) - 1 || '';
      }
    });
}

function refreshDevices() {
  fetch('/devices')
    .then(r => r.json())
    .then(devices => {
      const list = document.getElementById('device-list');
      if (!list) return;
      list.innerHTML = devices.map(d => {
        const online = d.last_seen && minutesAgo(d.last_seen) < 30;
        return `
          <li class="device-item">
            <span class="dot ${online ? 'online' : 'offline'}"></span>
            <span>${d.name}</span>
            <span class="device-loc">${d.location}</span>
          </li>
        `;
      }).join('');
    });
}

function refreshEvents() {
  fetch('/events?limit=20')
    .then(r => r.json())
    .then(events => {
      const tbody = document.querySelector('#event-table tbody');
      if (!tbody) return;
      if (events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty">No events yet</td></tr>';
        return;
      }
      tbody.innerHTML = events.map(e => `
        <tr>
          <td>${fmtTime(e.timestamp)}</td>
          <td>${e.device_name}</td>
          <td>${e.location}</td>
          <td>${e.event_type}</td>
          <td>${e.value ?? '—'}</td>
        </tr>
      `).join('');
    });
}

function refreshTranscripts() {
  fetch('/transcripts?limit=20')
    .then(r => r.json())
    .then(items => {
      const list = document.getElementById('transcript-list');
      if (!list) return;
      if (items.length === 0) {
        list.innerHTML = '<li class="empty">No transcripts yet</li>';
        return;
      }
      list.innerHTML = items.map(t => `
        <li class="transcript-item">
          <span class="transcript-text">${escapeHtml(t.text)}</span>
          <span class="transcript-time">${fmtTime(t.created_at)}</span>
        </li>
      `).join('');
    });
}

// ── Voice recognition helpers ─────────────────────────────────────────────────

let voiceRecognitionSupported = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
let voiceRecognition = null;
let voiceActive = false;
let voiceTranscript = '';

function initVoiceRecognition() {
  if (!voiceRecognitionSupported) {
    updateVoiceStatus('Voice recognition is not supported in this browser.');
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  voiceRecognition = new SpeechRecognition();
  voiceRecognition.lang = 'en-US';
  voiceRecognition.interimResults = true;
  voiceRecognition.maxAlternatives = 1;
  voiceRecognition.continuous = true;

  voiceRecognition.addEventListener('result', event => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript)
      .join('');
    voiceTranscript = transcript;
    updateVoiceTranscript(transcript);
  });

  voiceRecognition.addEventListener('start', () => {
    voiceActive = true;
    voiceTranscript = '';
    updateMicButton(true);
    updateVoiceStatus('Listening… tap again when you are done.');
    updateVoiceTranscript('');
  });

  voiceRecognition.addEventListener('end', () => {
    voiceActive = false;
    updateMicButton(false);
    const finalText = voiceTranscript.trim();
    if (finalText) {
      sendTranscript(finalText);
      updateVoiceStatus('Sent to your caregiver.');
    } else {
      updateVoiceStatus('Tap the microphone to speak.');
    }
    voiceTranscript = '';
  });

  voiceRecognition.addEventListener('error', event => {
    updateMicButton(false);
    updateVoiceStatus(`Sorry, something went wrong (${event.error}).`);
  });
}

function toggleVoiceRecognition() {
  if (!voiceRecognitionSupported) {
    updateVoiceStatus('Voice recognition is not supported in this browser.');
    return;
  }
  if (!voiceRecognition) initVoiceRecognition();
  if (voiceActive) {
    stopVoiceRecognition();
  } else {
    startVoiceRecognition();
  }
}

function updateMicButton(listening) {
  const btn = document.getElementById('mic-btn');
  if (!btn) return;
  btn.classList.toggle('listening', listening);
  const label = document.getElementById('mic-label');
  if (label) label.textContent = listening ? 'Listening… Tap to Stop' : 'Tap to Speak';
}

function sendTranscript(text) {
  fetch('/transcript', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: 'tablet_mic', text }),
  }).catch(() => updateVoiceStatus('Could not reach caregiver — please try again.'));
}

function startVoiceRecognition() {
  if (!voiceRecognitionSupported || !voiceRecognition) return;
  if (!voiceActive) {
    voiceRecognition.start();
  }
}

function stopVoiceRecognition() {
  if (!voiceRecognitionSupported || !voiceRecognition) return;
  if (voiceActive) {
    voiceRecognition.stop();
  }
}

function updateVoiceStatus(message) {
  const status = document.getElementById('voice-status');
  if (status) status.textContent = message;
}

function updateVoiceTranscript(text) {
  const transcript = document.getElementById('voice-transcript');
  if (transcript) transcript.textContent = text;
}

// ── Tablet helpers ────────────────────────────────────────────────────────────

function updateClock() {
  const now = new Date();
  const clockEl = document.getElementById('clock');
  const dateEl  = document.getElementById('date-display');
  if (clockEl) {
    clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (dateEl) {
    dateEl.textContent = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
  }

  // Update greeting based on time of day
  const statusEl = document.getElementById('status-msg');
  if (statusEl) {
    const h = now.getHours();
    if      (h < 12) statusEl.textContent = 'Good morning! Have a wonderful day.';
    else if (h < 17) statusEl.textContent = 'Good afternoon! Hope you are feeling well.';
    else             statusEl.textContent = 'Good evening! Time to wind down.';
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function fmtTime(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr.includes('Z') ? isoStr : isoStr + 'Z');
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function minutesAgo(isoStr) {
  if (!isoStr) return Infinity;
  const d = new Date(isoStr.includes('Z') ? isoStr : isoStr + 'Z');
  return (Date.now() - d.getTime()) / 60000;
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]));
}
