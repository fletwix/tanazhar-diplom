import re

with open(r'c:\Users\Fletwix\Desktop\tanazhar\static\style.css', 'r', encoding='utf-8') as f:
    css = f.read()

if '#toast-container' not in css:
    css_to_add = """

/* ── Toast Notifications ──────────────────────────────── */
#toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast {
  background: var(--surface-color);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--surface-border);
  color: var(--text-primary);
  padding: 12px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 250px;
  max-width: 350px;
  transform: translateX(120%);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast.show {
  transform: translateX(0);
  opacity: 1;
}

.toast.error {
  border-left: 4px solid var(--danger-color);
}
.toast.success {
  border-left: 4px solid var(--accent-color);
}
.toast.info {
  border-left: 4px solid #3b82f6;
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
}
"""
    css += css_to_add
    with open(r'c:\Users\Fletwix\Desktop\tanazhar\static\style.css', 'w', encoding='utf-8') as f:
        f.write(css)

with open(r'c:\Users\Fletwix\Desktop\tanazhar\static\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

if 'showNotification(' not in js:
    js_to_add = """
// ── Toast Notifications ──────────────────────────────────────────
function showNotification(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let icon = 'ℹ️';
  if (type === 'error') icon = '⚠️';
  if (type === 'success') icon = '✅';

  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div style="line-height: 1.4;">${message}</div>
  `;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
  });

  // Remove after 3.5 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 400); // Wait for transition
  }, 3500);
}

"""
    js = js.replace('const API_BASE = "http://localhost:8000"; // Assuming local dev', 'const API_BASE = "http://localhost:8000"; // Assuming local dev\n' + js_to_add)

# Now manually replace each known alert to be 100% safe from regex brackets issue
replacements = [
    ('alert("Пожалуйста, войдите, чтобы создавать маршруты!");', 'showNotification("Пожалуйста, войдите, чтобы создавать маршруты!", "info");'),
    ('alert("Ошибка авторизации: " + e.message);', 'showNotification("Ошибка авторизации: " + e.message, "error");'),
    ('alert("Ваш браузер не поддерживает геолокацию.");', 'showNotification("Ваш браузер не поддерживает геолокацию.", "error");'),
    ('alert("Ваш браузер не поддерживает геолокацию");', 'showNotification("Ваш браузер не поддерживает геолокацию", "error");'),
    ('alert("Не удалось определить местоположение. Проверьте разрешения браузера.");', 'showNotification("Не удалось определить местоположение. Проверьте разрешения браузера.", "error");'),
    ('alert("Ничего не найдено по запросу: " + query);', 'showNotification("Ничего не найдено по запросу: " + query, "info");'),
    ('alert("Ошибка поиска: " + (err.message || err));', 'showNotification("Ошибка поиска: " + (err.message || err), "error");'),
    ('alert("Необходимо разрешение на геолокацию для поиска ближайших мест.");', 'showNotification("Необходимо разрешение на геолокацию для поиска ближайших мест.", "error");'),
    ('alert("Ошибка загрузки маршрута: " + e.message);', 'showNotification("Ошибка загрузки маршрута: " + e.message, "error");'),
    ('alert("Маршрут удален");', 'showNotification("Маршрут удален", "success");'),
    ('alert("Нет прав на удаление.");', 'showNotification("Нет прав на удаление.", "error");'),
    ('alert("Ошибка удаления.");', 'showNotification("Ошибка удаления.", "error");'),
    ('alert("Ошибка скачивания GPX.");', 'showNotification("Ошибка скачивания GPX.", "error");'),
    ('if(!state.user) alert("Пожалуйста, войдите, чтобы создавать маршруты!");', 'if(!state.user) showNotification("Пожалуйста, войдите, чтобы создавать маршруты!", "info");'),
    ('alert("Войдите в аккаунт для расчета");', 'showNotification("Войдите в аккаунт для расчета", "info");')
]

for old, new in replacements:
    js = js.replace(old, new)


with open(r'c:\Users\Fletwix\Desktop\tanazhar\static\app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Patch applied.")
