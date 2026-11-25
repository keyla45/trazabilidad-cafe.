(() => {
  'use strict';
  const chat = document.getElementById('ct-chat');
  const form = document.getElementById('ct-form');
  const input = document.getElementById('ct-input');
  const mic = document.getElementById('ct-mic');
  const sendButton = document.getElementById('ct-send');
  const clearButton = document.getElementById('ct-clear');
  const promptBox = document.getElementById('ct-prompts');
  const voiceNote = document.getElementById('ct-voice-note');
  if (!chat || !form || !input) return;
  let busy = false;
  const endpoint = '/api/asistente/';
  const hello = chat.innerHTML;

  function addMessage(text, kind, url, label, source) {
    const message = document.createElement('div');
    message.className = 'ct-msg ' + kind;
    const para = document.createElement('div');
    para.textContent = text;
    message.appendChild(para);
    if (url && url.startsWith('/') && !url.startsWith('//')) {
      const link = document.createElement('a');
      link.href = url;
      link.className = 'ct-chat-action';
      link.textContent = (label || 'Abrir información') + ' ↗';
      message.appendChild(link);
    }
    if (kind === 'bot' && source) {
      const meta = document.createElement('small');
      meta.className = 'ct-message-source';
      meta.textContent = 'Fuente: ' + source;
      message.appendChild(meta);
    }
    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;
    return message;
  }
  function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    input.disabled = value;
    sendButton.textContent = value ? 'Consultando…' : 'Enviar ↗';
  }
  function updatePrompts(items) {
    if (!Array.isArray(items) || !items.length) return;
    promptBox.querySelectorAll('button[data-dynamic="1"]').forEach(node => node.remove());
    for (const label of items.slice(0, 3)) {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.dynamic = '1';
      button.textContent = '↗ ' + label;
      button.addEventListener('click', () => send(label));
      promptBox.appendChild(button);
    }
  }
  async function send(query) {
    const q = query.trim();
    if (!q || busy) return;
    addMessage(q, 'user');
    input.value = '';
    setBusy(true);
    try {
      const response = await fetch(endpoint + '?q=' + encodeURIComponent(q), {
        method: 'GET', credentials: 'same-origin', headers: {'Accept': 'application/json'},
      });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const result = await response.json();
      addMessage(result.respuesta || 'No hay datos para responder esa consulta.',
        'bot', result.url, result.etiqueta, result.fuente);
      updatePrompts(result.sugerencias);
    } catch (error) {
      addMessage('No pude conectar con CaféTrace. Confirma que Django esté ejecutándose y que tu sesión no haya expirado.', 'bot');
    } finally {
      setBusy(false);
      input.disabled = false;
      input.focus();
    }
  }
  form.addEventListener('submit', e => { e.preventDefault(); send(input.value); });
  promptBox.querySelectorAll('[data-query]').forEach(b => b.addEventListener('click', () => send(b.dataset.query)));
  clearButton?.addEventListener('click', () => { chat.innerHTML = hello; input.focus(); });

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!mic) return;
  if (!Recognition) {
    mic.disabled = true;
    mic.title = 'El navegador no admite reconocimiento de voz';
    voiceNote.textContent = 'Reconocimiento de voz no disponible. Puedes escribir tus preguntas. Prueba con Chrome o Edge y una página HTTPS o localhost.';
    return;
  }
  let recognition;
  mic.addEventListener('click', () => {
    if (recognition) { recognition.stop(); return; }
    recognition = new Recognition();
    recognition.lang = 'es-EC';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    mic.textContent = '●';
    mic.setAttribute('aria-pressed', 'true');
    voiceNote.textContent = 'Escuchando… di una pregunta de inventario, lotes, pedidos, MRP o QR.';
    recognition.onresult = event => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      voiceNote.textContent = 'Dictado reconocido. Se ha escrito la pregunta; presiona Enviar para consultar.';
      input.focus();
    };
    recognition.onerror = () => { voiceNote.textContent = 'No se pudo usar el micrófono. Comprueba los permisos del navegador o utiliza el teclado.'; };
    recognition.onend = () => {
      recognition = null;
      mic.textContent = '🎙';
      mic.setAttribute('aria-pressed', 'false');
    };
    try { recognition.start(); } catch (_) { recognition = null; mic.textContent = '🎙'; }
  });
})();
