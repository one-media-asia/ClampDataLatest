// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/service-worker.js').then(reg => {
    console.log('Service worker registered.', reg);
  }).catch(err => console.warn('SW registration failed:', err));
}

// Simple multi-display helper: try Presentation API then fallback to window.open + postMessage
window.PresentationHelper = (function(){
  let presentationWindow = null;

  function openPresentation(url) {
    // Prefer Presentation API if available
    const presentationUrl = url || (window.location.href + (window.location.search ? '&' : '?') + 'presentation=1');

    // Experimental API (browser support limited)
    if (navigator.presentation && navigator.presentation.requestSession) {
      try {
        navigator.presentation.requestSession(presentationUrl).then(session => {
          console.log('Presentation session started', session);
        }).catch(err => {
          console.warn('Presentation API failed, falling back to window.open', err);
          presentationWindow = window.open(presentationUrl, '_blank');
        });
        return;
      } catch (e) {
        console.warn('Presentation API error, falling back', e);
      }
    }

    // Fallback: open a new window and keep reference
    presentationWindow = window.open(presentationUrl, '_blank');
    return presentationWindow;
  }

  function sendMessage(obj) {
    try {
      if (presentationWindow && !presentationWindow.closed) {
        presentationWindow.postMessage(obj, '*');
        return true;
      }
      // If session API used, more implementation would be required
    } catch (e) {
      console.warn('Send message failed:', e);
    }
    return false;
  }

  // Listen for messages from the presentation window
  window.addEventListener('message', (ev) => {
    console.log('Received message from presentation window:', ev.data);
  });

  return { openPresentation, sendMessage };
})();

// If this window is opened as a presentation, listen for postMessage to update content
(function setupPresentationReceiver(){
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('presentation')) {
    window.addEventListener('message', ev => {
      // user-defined message format: { type: 'render', payload: { html: '<div>...</div>' }}
      try {
        const msg = ev.data;
        if (msg && msg.type === 'render' && msg.payload && msg.payload.html) {
          document.body.innerHTML = msg.payload.html;
          document.title = msg.payload.title || document.title;
        }
      } catch (e) {
        console.warn('Error processing presentation message', e);
      }
    });
  }
})();

// Present a specific invoice by opening the presentation URL
function presentInvoice(id) {
  const url = `/presentation/invoice/${id}`;
  // Use PresentationHelper to open on secondary display or fallback
  PresentationHelper.openPresentation(url);
}
