function copyTextFallback(text) {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  const copied = document.execCommand('copy');
  area.remove();
  return copied;
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  return copyTextFallback(text);
}

function installFeedbackCopyButton() {
  const feedback = document.querySelector('#shell-feedback');
  if (!feedback || feedback.querySelector('.shell-feedback-copy')) return false;

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'shell-feedback-copy';
  button.textContent = 'Copier';
  button.setAttribute('aria-label', 'Copier ce message');
  button.style.cssText = 'float:right;margin:-4px -6px 0 8px;padding:3px 7px;min-height:0;border:1px solid rgba(255,255,255,.45);border-radius:999px;background:rgba(255,255,255,.14);color:#fff;font:700 10px/1.2 system-ui;cursor:pointer';

  button.addEventListener('click', async event => {
    event.stopPropagation();
    const text = [...feedback.childNodes]
      .filter(node => node !== button)
      .map(node => node.textContent || '')
      .join('')
      .trim();
    if (!text) return;
    const previous = button.textContent;
    try {
      await copyText(text);
      button.textContent = 'Copié ✓';
    } catch {
      button.textContent = 'Échec';
    }
    window.setTimeout(() => { button.textContent = previous; }, 1300);
  });

  feedback.prepend(button);
  return true;
}

function observeFeedback() {
  if (installFeedbackCopyButton()) return;
  const observer = new MutationObserver(() => {
    if (installFeedbackCopyButton()) observer.disconnect();
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', observeFeedback, { once: true });
} else {
  observeFeedback();
}

export { installFeedbackCopyButton };
