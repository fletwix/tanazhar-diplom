import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 405 to 848 (0-indexed: 404 to 847) contain all the old dead code
# We will replace them with a clean block
before = lines[:404]  # lines 1-404
after = lines[847:]    # lines 849+

new_block = r'''
// ── Geolocation ──────────────────────────────────────────────────

function locateUser() {
  if (!navigator.geolocation) {
    alert("Ваш браузер не поддерживает геолокацию.");
    return;
  }

  DOM.btnGeo.classList.add('loading');

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const coords = [pos.coords.latitude, pos.coords.longitude];
      map.setCenter(coords, 15, { duration: 1000 });

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
      alert("Не удалось определить местоположение. Проверьте разрешения браузера.");
      DOM.btnGeo.classList.remove('loading');
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
    
    renderRouteList(routes);
    DOM.btnSearchArea.textContent = "Искать в этой области";
  } catch(e) {
    console.error(e);
    DOM.btnSearchArea.textContent = "Ошибка!";
    setTimeout(()=> DOM.btnSearchArea.textContent = "Искать в этой области", 2000);
  }
}

function renderRouteList(routes) {
  layers.routes.removeAll();
  DOM.routeList.innerHTML = '';
  
  if (!routes || routes.length === 0) {
    DOM.routeList.innerHTML = '<div class="empty-state">Здесь маршрутов не найдено.</div>';
    return;
  }
  
  routes.forEach(route => {
    const card = document.createElement('div');
    card.className = 'route-card';
    card.innerHTML = `
      <h3>${route.title}</h3>
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
    const r = await res.json();
    
    DOM.detailTitle.textContent = r.title;
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
    
    const latlngs = r.coordinates.map(c => [c.lat, c.lon]);
    
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
    alert("Маршрут не найден.");
    hideDetails();
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
      alert("Маршрут удален");
      hideDetails();
      clearMap();
    } else {
      alert("Нет прав на удаление.");
    }
  } catch(e) {
    alert("Ошибка удаления.");
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
    alert("Ошибка скачивания GPX.");
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
  if (!state.token) return alert("Войдите в аккаунт для расчета");
  
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
    alert(e.message);
  }
}

// ── Map Click ────────────────────────────────────────────────────

async function onMapClick(e) {
  const coords = e.get('coords');

  if (!DOM.tabContentCreate.classList.contains('hidden')) {
    // --- Create Route mode: add waypoint ---
    if (!state.user) return alert("Пожалуйста, войдите, чтобы создавать маршруты!");
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

function addWaypoint(coords) {
  state.draftWaypoints.push(coords);
  updateDraftMap();
}

function removeWaypoint(index) {
  state.draftWaypoints.splice(index, 1);
  updateDraftMap();
}

function updateDraftMap() {
  layers.draftMarkers.removeAll();
  layers.draftLine = null;

  // Draw numbered markers
  state.draftWaypoints.forEach((pt, idx) => {
    const num = idx + 1;
    const isFirst = idx === 0;
    const isLast = idx === state.draftWaypoints.length - 1;

    let color = '#3b82f6';  // blue default
    if (isFirst) color = '#22c55e';  // green start
    if (isLast && !isFirst) color = '#ef4444';  // red end

    const marker = new ymaps.Placemark(pt, {
      iconContent: String(num),
      balloonContent: `<b>Точка ${num}</b><br><small>ПКМ чтобы удалить</small>`
    }, {
      preset: 'islands#circleIcon',
      iconColor: color,
      draggable: true
    });

    // Drag to reposition
    marker.events.add('dragend', () => {
      state.draftWaypoints[idx] = marker.geometry.getCoordinates();
      updateDraftLine();
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
    layers.draftLine = new ymaps.Polyline(state.draftWaypoints, {}, {
      strokeColor: '#3b82f6',
      strokeWidth: 4,
      strokeStyle: '5 5'
    });
    layers.draftMarkers.add(layers.draftLine);
  }
}

'''

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.writelines(before)
    f.write(new_block)
    f.writelines(after)

print("Done! Rewrote lines 405-848.")
