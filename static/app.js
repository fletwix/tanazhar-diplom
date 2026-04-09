/**
 * TrailWeaver - Frontend MVP
 * Vanilla JS + Yandex Maps API + Fetch API
 */

const API_BASE = "http://localhost:8000"; // Assuming local dev

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

// ── State ────────────────────────────────────────────────────────
let map;
let layers = {
  routes: null,
  draftMarkers: null,
  draftLine: null,
  searchMarkers: null
};

let state = {
  token: localStorage.getItem("tw_token"),
  user: null,
  draftWaypoints: [],
  selectedRouteId: null,
  theme: localStorage.getItem("tw_theme") || "dark",
  exploreRoutes: []
};


// ── DOM Elements ─────────────────────────────────────────────────
const DOM = {
  // Auth
  loginForm: document.getElementById('login-form'),
  registerForm: document.getElementById('register-form'),
  emailInput: document.getElementById('email'),
  passInput: document.getElementById('password'),
  
  regUsername: document.getElementById('reg-username'),
  regEmail: document.getElementById('reg-email'),
  regPass: document.getElementById('reg-password'),
  regWeight: document.getElementById('reg-weight'),
  
  loggedOutView: document.getElementById('logged-out-view'),
  loggedInView: document.getElementById('logged-in-view'), // fixed ID
  userNameDisplay: document.getElementById('user-name-display'),
  logoutBtn: document.getElementById('logout-btn'),
  showRegBtn: document.getElementById('show-register'),
  showLoginBtn: document.getElementById('show-login'),

  // Theme
  themeToggle: document.getElementById('theme-toggle'),

  // Tabs
  tabContentExplore: document.getElementById('tab-explore'),
  tabContentCreate: document.getElementById('tab-create'),
  tabs: document.querySelectorAll('.tab-btn'),

  // Map Controls
  btnGeo: document.getElementById('btn-geolocation'),
  categoryFilters: document.querySelectorAll('.category-filter'),
  mapSearchInput: document.getElementById('map-search-input'),
  btnMapSearch: document.getElementById('btn-map-search'),

  // Explore
  btnSearchArea: document.getElementById('btn-search-area'),
  btnClearMap: document.getElementById('btn-clear-map'),
  routeList: document.getElementById('route-list'),
  ratingFilter: document.getElementById('rating-filter'),

  // Create
  createForm: document.getElementById('route-create-form'),
  routeTitle: document.getElementById('route-title'),
  routeDesc: document.getElementById('route-desc'),
  routeDiff: document.getElementById('route-difficulty'),
  wpCount: document.getElementById('wp-count'),
  btnClearWp: document.getElementById('btn-clear-wp'),
  btnSaveRoute: document.getElementById('btn-save-route'),

  // Details
  detailsPanel: document.getElementById('route-details'),
  btnBack: document.getElementById('btn-back'),
  detailTitle: document.getElementById('detail-title'),
  detailRating: document.getElementById('detail-rating'),
  detailDiff: document.getElementById('detail-diff'),
  detailDist: document.getElementById('detail-dist'),
  detailElev: document.getElementById('detail-elev'),
  detailDesc: document.getElementById('detail-desc'),
  
  weatherContainer: document.getElementById('weather-container'),
  
  energyForm: document.getElementById('energy-form'),
  energyPack: document.getElementById('backpack-weight'),
  energyResult: document.getElementById('energy-result'),
  calcKcal: document.getElementById('calc-kcal'),
  calcHrs: document.getElementById('calc-hours'),
  
  btnDownloadGPX: document.getElementById('btn-download-gpx'),
  
  reviewsList: document.getElementById('reviews-list'),
  reviewForm: document.getElementById('review-form'),
  starRatingContainer: document.getElementById('star-rating-container'),
  reviewRatingInput: document.getElementById('review-rating'),
  reviewComment: document.getElementById('review-comment'),
};

// Allow fixing IDs dynamically - removed since fixed above

// ── Initialization ───────────────────────────────────────────────
function initMap() {
  ymaps.ready(() => {
    map = new ymaps.Map('map', {
        center: [43.238, 76.889],
        zoom: 13,
        controls: ['zoomControl']
    });
    
    // Add margin for sidebar and search bar so centers are perfectly calculated
    map.margin.addArea({
        top: 0,
        left: 0, 
        width: 520, // 440px + bigger margin to move it a bit left
        height: '100%'
    });
    // Add bottom margin to push the center point higher
    map.margin.addArea({
        top: '70%',
        left: 0,
        width: '100%',
        height: '30%'
    });

    layers.routes = new ymaps.GeoObjectCollection();
    layers.draftMarkers = new ymaps.GeoObjectCollection();
    layers.searchMarkers = new ymaps.GeoObjectCollection();

    map.geoObjects.add(layers.routes);
    map.geoObjects.add(layers.draftMarkers);
    map.geoObjects.add(layers.searchMarkers);

    map.events.add('click', onMapClick);
  });
  initStarRating();
}

function applyTheme(theme) {
  if (theme === 'light') {
    document.body.classList.add('light-theme');
  } else {
    document.body.classList.remove('light-theme');
  }
}

function toggleTheme() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('tw_theme', state.theme);
  applyTheme(state.theme);
}

async function init() {
  initMap();
  applyTheme(state.theme);
  setupEventListeners();
  if (state.token) {
    await fetchCurrentUser();
  } else {
    updateAuthUI();
  }
}

document.addEventListener("DOMContentLoaded", init);

// ── Event Listeners ──────────────────────────────────────────────
function setupEventListeners() {
  // Theme
  DOM.themeToggle.addEventListener('click', toggleTheme);

  // Tabs
  DOM.tabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Map Controls (Geolocation)
  DOM.btnGeo.addEventListener('click', locateUser);
  
  // Map Search
  DOM.btnMapSearch.addEventListener('click', performMapSearch);
  DOM.mapSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      performMapSearch();
    }
  });
  
  // Quick Search Chips
  document.querySelectorAll('.quick-search-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      DOM.mapSearchInput.value = e.target.dataset.query;
      performMapSearch();
    });
  });

  // Auth Toggles
  DOM.showRegBtn.addEventListener('click', (e) => {
    e.preventDefault();
    DOM.loginForm.classList.add('hidden');
    DOM.registerForm.classList.remove('hidden');
  });
  
  DOM.showLoginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    DOM.registerForm.classList.add('hidden');
    DOM.loginForm.classList.remove('hidden');
  });

  // Auth Submits
  DOM.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = DOM.loginForm.querySelector('button[type="submit"]');
    const ogText = btn.textContent;
    btn.textContent = "Вход...";
    btn.disabled = true;
    await handleAuth(DOM.emailInput.value, DOM.passInput.value, 'login');
    btn.textContent = ogText;
    btn.disabled = false;
  });

  DOM.registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = DOM.registerForm.querySelector('button[type="submit"]');
    const ogText = btn.textContent;
    btn.textContent = "Регистрация...";
    btn.disabled = true;
    
    await handleAuth(
      DOM.regEmail.value, 
      DOM.regPass.value, 
      'register', 
      DOM.regUsername.value, 
      parseFloat(DOM.regWeight.value)
    );
    
    btn.textContent = ogText;
    btn.disabled = false;
  });

  DOM.logoutBtn.addEventListener('click', () => {
    state.token = null;
    state.user = null;
    localStorage.removeItem("tw_token");
    updateAuthUI();
  });

  // Explore
  DOM.btnSearchArea.addEventListener('click', searchArea);
  DOM.btnClearMap.addEventListener('click', clearMap);
  if (DOM.ratingFilter) {
    DOM.ratingFilter.addEventListener('change', applyRouteFilter);
  }
  
  // Create
  DOM.btnClearWp.addEventListener('click', clearDraft);
  DOM.createForm.addEventListener('submit', saveDraftRoute);

  // Details
  DOM.btnBack.addEventListener('click', closeDetails);
  
  DOM.btnDownloadGPX.addEventListener('click', () => {
    if(!state.selectedRouteId) return;
    window.open(`${API_BASE}/routes/${state.selectedRouteId}/gpx`, '_blank');
  });
  
  DOM.energyForm.addEventListener('submit', calculateEnergy);
  DOM.reviewForm.addEventListener('submit', submitReview);
}


// ── Authentication ───────────────────────────────────────────────

async function handleAuth(email, password, mode, username=null, weight=70) {
  try {
    if (mode === 'register') {
      const regRes = await fetch(`${API_BASE}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username, weight_kg: weight })
      });
      if (!regRes.ok) throw new Error(await regRes.text());
    }

    // Login for token
    const loginRes = await fetch(`${API_BASE}/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!loginRes.ok) throw new Error("Неверные учетные данные");
    
    const data = await loginRes.json();
    state.token = data.access_token;
    localStorage.setItem("tw_token", state.token);
    
    await fetchCurrentUser();
  } catch(e) {
    showNotification("Ошибка авторизации: " + e.message, "error");
  }
}

async function fetchCurrentUser() {
  if (!state.token) return;
  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error("Срок действия токена истек");
    state.user = await res.json();
    updateAuthUI();
  } catch(e) {
    state.token = null;
    localStorage.removeItem("tw_token");
    updateAuthUI();
  }
}

function updateAuthUI() {
  if (state.user) {
    DOM.loggedOutView.classList.add('hidden');
    DOM.loggedInView.classList.remove('hidden');
    DOM.userNameDisplay.textContent = state.user.username;
    
    // Enable features that need auth
  } else {
    DOM.loggedOutView.classList.remove('hidden');
    DOM.loggedInView.classList.add('hidden');
  }
}

// ── UI Control & Star Rating ───────────────────────────────────────

function initStarRating() {
  DOM.starRatingContainer.innerHTML = '';
  // SVG pattern for a star
  const starSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
  
  for (let i = 1; i <= 5; i++) {
    const starElement = document.createElement('div');
    starElement.innerHTML = starSVG;
    const svg = starElement.firstChild;
    svg.dataset.value = i;
    
    // Hover interactions
    svg.addEventListener('mouseenter', () => {
      const stars = DOM.starRatingContainer.querySelectorAll('svg');
      stars.forEach((s, idx) => {
        if (idx < i) s.classList.add('hovered');
        else s.classList.remove('hovered');
      });
    });
    
    // Click interactions
    svg.addEventListener('click', () => {
      DOM.reviewRatingInput.value = i;
      const stars = DOM.starRatingContainer.querySelectorAll('svg');
      stars.forEach((s, idx) => {
        if (idx < i) s.classList.add('selected');
        else s.classList.remove('selected');
      });
    });
    
    DOM.starRatingContainer.appendChild(svg);
  }
  
  // Clear hover state when mouse leaves container (revert to selected)
  DOM.starRatingContainer.addEventListener('mouseleave', () => {
    const stars = DOM.starRatingContainer.querySelectorAll('svg');
    const selectedVal = parseInt(DOM.reviewRatingInput.value) || 0;
    stars.forEach((s, idx) => {
      s.classList.remove('hovered');
      if (idx < selectedVal) s.classList.add('selected');
      else s.classList.remove('selected');
    });
  });
}

function resetStarRating() {
  DOM.reviewRatingInput.value = "0";
  const stars = DOM.starRatingContainer.querySelectorAll('svg');
  stars.forEach(s => {
    s.classList.remove('selected');
    s.classList.remove('hovered');
  });
}

function switchTab(tabId) {
  DOM.tabs.forEach(t => t.classList.remove('active'));
  document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
  
  DOM.tabContentExplore.classList.add('hidden');
  DOM.tabContentCreate.classList.add('hidden');
  
  if(tabId === 'explore') DOM.tabContentExplore.classList.remove('hidden');
  if(tabId === 'create') {
    if(!state.user) showNotification("Пожалуйста, войдите, чтобы создавать маршруты!", "info");
    DOM.tabContentCreate.classList.remove('hidden');
  }
  
  closeDetails();
}

function showDetails() {
  DOM.detailsPanel.classList.remove('hidden');
}

function closeDetails() {
  DOM.detailsPanel.classList.add('hidden');
  state.selectedRouteId = null;
}

// ── Geolocation ──────────────────────────────────────────────────

function locateUser() {
  if (!navigator.geolocation) {
    showNotification("Ваш браузер не поддерживает геолокацию.", "error");
    return;
  }

  DOM.btnGeo.classList.add('loading');

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const coords = [pos.coords.latitude, pos.coords.longitude];
      const zoom = map.getZoom();
      
      // Native Yandex map margin handles the offset automatically
      map.setCenter(coords, zoom, { duration: 1000 });

      const userMarker = new ymaps.Placemark(coords, {
        balloonContent: '<b>Вы здесь</b>'
      }, {
        preset: 'islands#geolocationIcon'
      });
      map.geoObjects.add(userMarker);
      userMarker.balloon.open();

      DOM.btnGeo.classList.remove('loading');
    },
    (err) => {
      console.error("Geolocation error:", err);
      showNotification("Не удалось определить местоположение. Проверьте разрешения браузера.", "error");
      DOM.btnGeo.classList.remove('loading');
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

// ── Map Search ───────────────────────────────────────────────────

async function performMapSearch() {
  const query = DOM.mapSearchInput.value.trim();
  if (!query) return;

  if (!navigator.geolocation) {
    showNotification("Ваш браузер не поддерживает геолокацию", "error");
    return;
  }

  layers.searchMarkers.removeAll();
  DOM.btnMapSearch.classList.add('loading');

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      
      const bounds = map.getBounds();
      const spnLat = Math.abs(bounds[1][0] - bounds[0][0]) / 2;
      const spnLon = Math.abs(bounds[1][1] - bounds[0][1]) / 2;

      try {
        const res = await fetch(
          `${API_BASE}/routes/search?text=${encodeURIComponent(query)}&lat=${lat}&lon=${lon}&spn_lat=${spnLat}&spn_lon=${spnLon}`
        );
        
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Ошибка ${res.status}`);
        }
        
        const places = await res.json();

        if (!places || places.length === 0) {
          showNotification("Ничего не найдено по запросу: " + query, "info");
          return;
        }

        // Fly to the first result
        map.setCenter([places[0].lat, places[0].lon], 15, { duration: 800 });

        // Add markers for each place
        places.forEach(function(place) {
          const coords = [place.lat, place.lon];

          let categoryHtml = '';
          if (place.category) {
            categoryHtml = `<span class="category">${place.category}</span>`;
          }

          let hoursHtml = '';
          if (place.hours) {
            hoursHtml = `<div class="hours">🕒 ${place.hours}</div>`;
          }

          let phoneHtml = '';
          if (place.phone) {
            phoneHtml = `<div class="phone">📞 <a href="tel:${place.phone}">${place.phone}</a></div>`;
          }

          let urlHtml = '';
          if (place.url) {
            urlHtml = `<div style="margin-top:6px;"><a href="${place.url}" target="_blank" style="color:#059669;font-size:13px;text-decoration:none;font-weight:500;">🌐 Сайт</a></div>`;
          }

          const balloonHtml = `
            <div class="custom-place-balloon">
              ${categoryHtml}
              <h3>${place.name}</h3>
              <div class="address" style="margin-top:4px;">📍 ${place.address || place.description || ''}</div>
              ${hoursHtml}
              ${phoneHtml}
              ${urlHtml}
            </div>
          `;

          const marker = new ymaps.Placemark(coords, {
            balloonContentBody: balloonHtml,
            hintContent: place.name
          }, {
            preset: place.category ? 'islands#violetDotIcon' : 'islands#blueCircleDotIcon'
          });

          // In create mode, clicking a search result adds it as waypoint
          marker.events.add('click', function() {
            if (!DOM.tabContentCreate.classList.contains('hidden') && state.user) {
              addWaypoint(coords, place.name || query);
            }
          });

          layers.searchMarkers.add(marker);
        });

        // Open balloon of first result
        const firstMarker = layers.searchMarkers.get(0);
        if (firstMarker && firstMarker.balloon) {
          firstMarker.balloon.open();
        }

      } catch (err) {
        console.error("Map search error:", err);
        showNotification("Ошибка поиска: " + (err.message || err), "error");
      } finally {
        DOM.btnMapSearch.classList.remove('loading');
      }
    },
    (err) => {
      showNotification("Необходимо разрешение на геолокацию для поиска ближайших мест.", "error");
      DOM.btnMapSearch.classList.remove('loading');
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

// ── Explore (Map) ────────────────────────────────────────────────

function clearMap() {
  layers.routes.removeAll();
  DOM.routeList.innerHTML = '<div class="empty-state">Переместите карту и нажмите поиск</div>';
}

async function searchArea() {
  const bounds = map.getBounds();
  // Yandex bounds: [[latMin, lonMin], [latMax, lonMax]]
  const min_lat = bounds[0][0];
  const min_lon = bounds[0][1];
  const max_lat = bounds[1][0];
  const max_lon = bounds[1][1];
  
  try {
    DOM.btnSearchArea.textContent = "Поиск...";
    const res = await fetch(`${API_BASE}/routes/explore?min_lon=${min_lon}&min_lat=${min_lat}&max_lon=${max_lon}&max_lat=${max_lat}`);
    const routes = await res.json();
    
    state.exploreRoutes = routes || [];
    applyRouteFilter();
    
    DOM.btnSearchArea.textContent = "Искать в этой области";
  } catch(e) {
    console.error(e);
    DOM.btnSearchArea.textContent = "Ошибка!";
    setTimeout(()=> DOM.btnSearchArea.textContent = "Искать в этой области", 2000);
  }
}

function applyRouteFilter() {
  if (!DOM.ratingFilter) {
    renderRouteList(state.exploreRoutes);
    return;
  }
  
  const filterVal = DOM.ratingFilter.value;
  let filtered = state.exploreRoutes;
  
  if (filterVal === 'high') {
    filtered = filtered.filter(r => r.rating !== null && r.rating >= 4.0);
  } else if (filterVal === 'low') {
    filtered = filtered.filter(r => r.rating !== null && r.rating < 4.0);
  } else if (['1', '2', '3', '4', '5'].includes(filterVal)) {
    const target = parseInt(filterVal);
    filtered = filtered.filter(r => r.rating !== null && Math.round(r.rating) === target);
  }
  
  renderRouteList(filtered);
}

function renderRouteList(routes) {
  layers.routes.removeAll();
  DOM.routeList.innerHTML = '';
  
  if (!routes || routes.length === 0) {
    DOM.routeList.innerHTML = '<div class="empty-state">Здесь маршрутов не найдено.</div>';
    return;
  }
  
  const starSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
  
  routes.forEach(route => {
    const card = document.createElement('div');
    card.className = 'route-card';
    
    let ratingHtml = '';
    if (route.rating !== null) {
      const r = Math.round(route.rating);
      let starsHtml = '';
      for (let i = 1; i <= 5; i++) {
        starsHtml += `<span class="review-star ${i <= r ? 'filled' : ''}" style="width:14px;height:14px;display:inline-block;">${starSVG}</span>`;
      }
      ratingHtml = `<div style="display:flex; align-items:center; gap:4px; margin-bottom:8px; font-size:13px; color:var(--text-secondary);">${starsHtml} <span style="margin-left:4px">${Number(route.rating).toFixed(1)} (${route.reviews_count})</span></div>`;
    } else {
      ratingHtml = `<div style="margin-bottom:8px; font-size:13px; color:var(--text-secondary);">Нет оценок</div>`;
    }

    card.innerHTML = `
      <h3>${route.title}</h3>
      ${ratingHtml}
      <div class="tags">
        <span class="tag diff">${route.difficulty}</span>
        <span class="tag">${Number(route.distance_km).toFixed(2)} км</span>
        <span class="tag">↑ ${Number(route.elevation_gain_m).toFixed(0)} м</span>
      </div>
    `;
    card.addEventListener('click', () => loadRouteDetails(route.id));
    DOM.routeList.appendChild(card);
  });
}

// ── Route Details & Dependencies ─────────────────────────────────

async function loadRouteDetails(id) {
  state.selectedRouteId = id;
  showDetails();
  
  try {
    const res = await fetch(`${API_BASE}/routes/${id}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Ошибка ${res.status}`);
    }
    const r = await res.json();
    
    DOM.detailTitle.textContent = r.title;
    
    const starSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
    if (r.rating !== null) {
      const rv = Math.round(r.rating);
      let starsHtml = '';
      for (let i = 1; i <= 5; i++) {
        starsHtml += `<span class="review-star ${i <= rv ? 'filled' : ''}" style="width:16px;height:16px;display:inline-block;">${starSVG}</span>`;
      }
      if (DOM.detailRating) DOM.detailRating.innerHTML = `${starsHtml} <span style="margin-left:6px">${Number(r.rating).toFixed(1)} (${r.reviews_count} отзывов)</span>`;
    } else {
      if (DOM.detailRating) DOM.detailRating.innerHTML = `Нет оценок`;
    }
    
    DOM.detailDesc.textContent = r.description || "Нет описания.";

    let diffRu = r.difficulty;
    if (diffRu === 'EASY') diffRu = 'Лёгкий';
    if (diffRu === 'MEDIUM') diffRu = 'Средний';
    if (diffRu === 'HARD') diffRu = 'Сложный';
    DOM.detailDiff.textContent = diffRu;
    
    DOM.detailDist.textContent = Number(r.distance_km).toFixed(2);
    DOM.detailElev.textContent = Number(r.elevation_gain_m).toFixed(0);
    
    // Draw on map
    layers.routes.removeAll();
    
    const latlngs = (r.coordinates || []).map(c => [c.lat, c.lon]);
    
    if (latlngs.length > 0) {
      const polyline = new ymaps.Polyline(latlngs, {}, {
          strokeColor: '#3b82f6',
          strokeWidth: 4
      });
      layers.routes.add(polyline);
      map.setCenter(latlngs[0], 14, { duration: 1500 });
    }
    
    // Weather
    fetchWeather(r.coordinates);
    
    // Reviews
    loadReviews(id);
    
  } catch(e) {
    console.error("Failed to load route", e);
    showNotification("Ошибка загрузки маршрута: " + e.message, "error");
    closeDetails();
  }
}

async function deleteRoute(id) {
  if (!confirm("Действительно удалить маршрут?")) return;
  try {
    const res = await fetch(`${API_BASE}/routes/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    if(res.ok) {
      showNotification("Маршрут удален", "success");
      closeDetails();
      clearMap();
    } else {
      showNotification("Нет прав на удаление.", "error");
    }
  } catch(e) {
    showNotification("Ошибка удаления.", "error");
  }
}

async function downloadGPX() {
  if(!state.selectedRouteId) return;
  try {
    const res = await fetch(`${API_BASE}/routes/${state.selectedRouteId}/gpx`);
    if(!res.ok) throw new Error();
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `route_${state.selectedRouteId}.gpx`;
    a.click();
    URL.revokeObjectURL(url);
  } catch(e) {
    showNotification("Ошибка скачивания GPX.", "error");
  }
}

async function fetchWeather(coordinates) {
  if (!coordinates || coordinates.length === 0) {
    DOM.weatherContainer.innerHTML = '<p style="color: var(--text-secondary);">Нет данных о погоде.</p>';
    return;
  }
  
  const midpoint = coordinates[Math.floor(coordinates.length / 2)];
  
  try {
    const res = await fetch(`${API_BASE}/routes/weather?lat=${midpoint.lat}&lon=${midpoint.lon}`);
    const w = await res.json();
    
    DOM.weatherContainer.innerHTML = `
      <div class="weather-info">
        <div class="weather-row">
          <span class="weather-label">🌡 Температура</span>
          <span class="weather-value">${w.temperature}°C</span>
        </div>
        <div class="weather-row">
          <span class="weather-label">💨 Ветер</span>
          <span class="weather-value">${w.wind_speed} км/ч</span>
        </div>
      </div>
    `;
  } catch(e) {
    DOM.weatherContainer.innerHTML = '<p style="color: var(--text-secondary);">Не удалось загрузить погоду.</p>';
  }
}

async function calculateEnergy(e) {
  e.preventDefault();
  if (!state.selectedRouteId) return;
  if (!state.token) return showNotification("Войдите в аккаунт для расчета", "info");
  
  const backpackWeight = parseFloat(DOM.energyPack.value) || 0;
  
  try {
    const res = await fetch(`${API_BASE}/routes/${state.selectedRouteId}/energy?backpack_weight_kg=${backpackWeight}`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    
    if(!res.ok) throw new Error("Ошибка расчета");
    
    const data = await res.json();
    DOM.calcKcal.textContent = data.total_calories_kcal;
    DOM.calcHrs.textContent = data.walking_time_hours;
    DOM.energyResult.classList.remove('hidden');
    
  } catch(e) {
    showNotification(e.message, "error");
  }
}

// ── Reviews ──────────────────────────────────────────────────────

async function loadReviews(routeId) {
  DOM.reviewsList.innerHTML = '<p style="color: var(--text-secondary); font-size:13px;">Загрузка отзывов...</p>';
  try {
    const res = await fetch(`${API_BASE}/routes/${routeId}/reviews`);
    if (!res.ok) throw new Error();
    const reviews = await res.json();
    
    if (!reviews || reviews.length === 0) {
      DOM.reviewsList.innerHTML = '<p style="color: var(--text-secondary); font-size:13px;">Отзывов пока нет. Будьте первым!</p>';
      return;
    }
    
    const starSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
    
    DOM.reviewsList.innerHTML = reviews.map(rv => {
      let starsHtml = '';
      for (let i = 1; i <= 5; i++) {
        starsHtml += `<span class="review-star ${i <= rv.rating ? 'filled' : ''}" style="width:18px;height:18px;display:inline-block;">${starSVG}</span>`;
      }
      const date = new Date(rv.created_at).toLocaleDateString('ru-RU');
      return `
        <div class="review-item">
          <div class="review-stars">${starsHtml}</div>
          <p class="review-comment">${rv.comment || ''}</p>
          <small style="color: var(--text-secondary);">${date}</small>
        </div>
      `;
    }).join('');
  } catch(e) {
    DOM.reviewsList.innerHTML = '<p style="color: var(--text-secondary); font-size:13px;">Не удалось загрузить отзывы.</p>';
  }
}

async function submitReview(e) {
  e.preventDefault();
  if (!state.selectedRouteId) return;
  if (!state.token) return showNotification("Войдите в аккаунт, чтобы оставить отзыв", "info");
  
  const rating = parseInt(DOM.reviewRatingInput.value);
  if (!rating || rating < 1 || rating > 5) return showNotification("Выберите рейтинг от 1 до 5 звёзд", "info");
  
  const comment = DOM.reviewComment.value.trim();
  
  try {
    const res = await fetch(`${API_BASE}/routes/${state.selectedRouteId}/reviews`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ rating, comment: comment || null })
    });
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Ошибка отправки');
    }
    
    // Clear form and reload reviews
    DOM.reviewComment.value = '';
    resetStarRating();
    await loadReviews(state.selectedRouteId);
  } catch(e) {
    showNotification("Ошибка: " + e.message, "error");
  }
}

// ── Map Click ────────────────────────────────────────────────────

async function onMapClick(e) {
  const coords = e.get('coords');

  if (!DOM.tabContentCreate.classList.contains('hidden')) {
    // --- Create Route mode: add waypoint ---
    if (!state.user) return showNotification("Пожалуйста, войдите, чтобы создавать маршруты!", "info");
    addWaypoint(coords);
  } else {
    // --- Explore mode: reverse geocode via Yandex ---
    try {
      const result = await ymaps.geocode(coords, { results: 1 });
      const firstGeoObject = result.geoObjects.get(0);

      let title = "Неизвестное место";
      let desc = "";

      if (firstGeoObject) {
        title = firstGeoObject.properties.get('name') || firstGeoObject.getAddressLine() || "Локация";
        desc = firstGeoObject.getAddressLine() || '';
      }

      const popupMarker = new ymaps.Placemark(coords, {
        balloonContent: `<div style="max-width:250px;"><b>${title}</b><p style="font-size:12px;margin-top:4px;">${desc}</p></div>`
      });
      map.geoObjects.add(popupMarker);
      popupMarker.balloon.open();

      map.events.once('click', () => {
        map.geoObjects.remove(popupMarker);
      });
    } catch (err) {
      console.error("Reverse geocoding error:", err);
    }
  }
}

// ── Waypoint / Draft Route Logic ─────────────────────────────────

async function addWaypoint(coords, name = null) {
  const wp = { coords, name: name || `Точка ${state.draftWaypoints.length + 1}` };
  state.draftWaypoints.push(wp);
  updateDraftMap();

  if (!name) {
    try {
      const result = await ymaps.geocode(coords, { results: 1 });
      const firstGeoObject = result.geoObjects.get(0);
      if (firstGeoObject) {
        // Only update if it hasn't been removed
        const index = state.draftWaypoints.indexOf(wp);
        if (index !== -1) {
          wp.name = firstGeoObject.properties.get('name') || firstGeoObject.getAddressLine() || wp.name;
          updateDraftMap();
        }
      }
    } catch (err) {}
  }
}

function removeWaypoint(index) {
  state.draftWaypoints.splice(index, 1);
  updateDraftMap();
}

function updateDraftMap() {
  layers.draftMarkers.removeAll();
  layers.draftLine = null;

  // Draw numbered markers
  state.draftWaypoints.forEach((wp, idx) => {
    const num = idx + 1;
    const isFirst = idx === 0;
    const isLast = idx === state.draftWaypoints.length - 1;

    let color = '#3b82f6';  // blue default
    if (isFirst) color = '#22c55e';  // green start
    if (isLast && !isFirst) color = '#ef4444';  // red end

    const marker = new ymaps.Placemark(wp.coords, {
      iconContent: String(num),
      balloonContent: `<b>${wp.name || 'Точка ' + num}</b><br><small>Кликните по маркеру чтобы удалить</small>`
    }, {
      preset: 'islands#circleIcon',
      iconColor: color,
      draggable: true
    });

    // Drag to reposition
    marker.events.add('dragend', async () => {
      const newCoords = marker.geometry.getCoordinates();
      state.draftWaypoints[idx].coords = newCoords;
      // Also update the name on drag end by reverse geocoding
      try {
        const result = await ymaps.geocode(newCoords, { results: 1 });
        const firstGeoObject = result.geoObjects.get(0);
        if (firstGeoObject) {
          state.draftWaypoints[idx].name = firstGeoObject.properties.get('name') || firstGeoObject.getAddressLine() || `Точка ${idx + 1}`;
        }
      } catch (err) {}
      updateDraftMap();
    });

    // Left-click to remove
    marker.events.add('click', (e) => {
      e.preventDefault();
      removeWaypoint(idx);
    });

    // Right-click to remove
    marker.events.add('contextmenu', (e) => {
      e.preventDefault();
      removeWaypoint(idx);
    });

    layers.draftMarkers.add(marker);
  });

  updateDraftLine();

  DOM.wpCount.textContent = state.draftWaypoints.length;
  DOM.btnSaveRoute.disabled = state.draftWaypoints.length < 2;
}

function updateDraftLine() {
  // Remove old line if it exists
  if (layers.draftLine) {
    try { layers.draftMarkers.remove(layers.draftLine); } catch(e) {}
    layers.draftLine = null;
  }

  if (state.draftWaypoints.length > 1) {
    const coordsList = state.draftWaypoints.map(wp => wp.coords);
    layers.draftLine = new ymaps.Polyline(coordsList, {}, {
      strokeColor: '#3b82f6',
      strokeWidth: 4,
      strokeStyle: '5 5'
    });
    layers.draftMarkers.add(layers.draftLine);
  }
}

function clearDraft() {
  state.draftWaypoints = [];
  updateDraftMap();
}

async function saveDraftRoute(e) {
  e.preventDefault();
  if (!state.token) return showNotification("Пожалуйста, войдите", "info");
  if (state.draftWaypoints.length < 2) return showNotification("Нужно как минимум 2 точки", "info");

  const waypoints = state.draftWaypoints.map(wp => ({
    lon: wp.coords[1],
    lat: wp.coords[0]
  }));

  const payload = {
    title: DOM.routeTitle.value,
    description: DOM.routeDesc.value,
    difficulty: DOM.routeDiff.value,
    is_public: true,
    waypoints: waypoints
  };

  try {
    DOM.btnSaveRoute.textContent = "Сохранение...";
    DOM.btnSaveRoute.disabled = true;

    const res = await fetch(`${API_BASE}/routes/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Не удалось сохранить маршрут. Проверьте API ключ ORS.");

    const r = await res.json();
    showNotification("Маршрут успешно сохранен!", "success");
    
    // resets
    clearDraft();
    DOM.routeTitle.value = '';
    DOM.routeDesc.value = '';
    DOM.btnSaveRoute.textContent = "Сохранить маршрут";
    switchTab('explore');
    
    // Load the created route
    loadRouteDetails(r.id);

  } catch (err) {
    showNotification(err.message, "error");
    DOM.btnSaveRoute.textContent = "Сохранить маршрут";
    DOM.btnSaveRoute.disabled = false;
  }
}
