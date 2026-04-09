import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. replace initMap to include search control
init_map_old = """function initMap() {
  ymaps.ready(() => {
    map = new ymaps.Map('map', {
        center: [43.238, 76.889],
        zoom: 13,
        controls: ['zoomControl']
    });"""

init_map_new = """function initMap() {
  ymaps.ready(() => {
    map = new ymaps.Map('map', {
        center: [43.238, 76.889],
        zoom: 13,
        controls: ['zoomControl', 'searchControl']
    });
    
    // Intercept clicks on search results
    map.controls.get('searchControl').events.add('resultselect', (e) => {
        if (!DOM.tabContentCreate.classList.contains('hidden')) {
            if (!state.user) {
                alert("Пожалуйста, войдите, чтобы создавать маршруты!");
                return;
            }
            const index = e.get('index');
            map.controls.get('searchControl').getResult(index).then((res) => {
                const coords = res.geometry.getCoordinates();
                state.draftWaypoints.push(coords);
                updateDraftMap();
            });
        }
    });"""
js = js.replace(init_map_old, init_map_new)

# 2. Category Quick Filters logic
cat_filter_old = """  // Category Quick Filters
  DOM.categoryFilters.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const query = btn.dataset.query;
      DOM.searchInput.value = query;
      fetchCategoryResults(query);
    });
  });"""
cat_filter_new = """  // Category Quick Filters
  DOM.categoryFilters.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const query = btn.dataset.query;
      map.controls.get('searchControl').search(query);
    });
  });"""
js = js.replace(cat_filter_old, cat_filter_new)

# 3. remove handleSearchSubmit, handleAutocompleteInput, fetchCategoryResults
# Since it's large and multi-line, we'll use regex to chop it out.
# Basically from `// ── Create Route ─────────────────────────────────────────────────` to `async function onMapClick(e)`
pattern_to_remove = re.compile(r'// ── Create Route ─────────────────────────────────────────────────.*?async function onMapClick\(e\)', re.DOTALL)
js = re.sub(pattern_to_remove, '// ── Map Click & Drawing ──────────────────────────────────────────\n\nasync function onMapClick(e)', js)

# 4. Also remove listeners for custom search
search_listeners_old = """  // Map Controls (Geolocation and Address Search)
  DOM.btnGeo.addEventListener('click', locateUser);
  DOM.searchInput.addEventListener('input', handleAutocompleteInput);
  DOM.searchInput.addEventListener('focus', () => {
    if(DOM.searchInput.value.length > 2) document.getElementById('map-search-results').classList.remove('hidden');
  });
  document.addEventListener('click', (e) => {
    if(!DOM.searchForm.contains(e.target)) {
      document.getElementById('map-search-results').classList.add('hidden');
    }
  });
  DOM.searchForm.addEventListener('submit', handleSearchSubmit);"""
search_listeners_new = """  // Map Controls (Geolocation)
  DOM.btnGeo.addEventListener('click', locateUser);"""
js = js.replace(search_listeners_old, search_listeners_new)

# 5. Geolocation rewrite
geo_old = """async function locateUser() {
  if (!navigator.geolocation) {
    alert("Ваш браузер не поддерживает геолокацию");
    return;
  }
  
  DOM.btnGeo.classList.add('loading');
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      map.setCenter([lat, lon], 14, { duration: 1000 });
      
      const userMarker = new ymaps.Placemark([lat, lon], {
          balloonContent: `<b>Вы здесь</b>`
      });
      map.geoObjects.add(userMarker);
      userMarker.balloon.open();
        
      map.events.once('click', () => {
        map.geoObjects.remove(userMarker);
      });
        
      DOM.btnGeo.classList.remove('loading');
    },
    (err) => {
      alert("Не удалось определить местоположение. Проверьте разрешения браузера.");
      DOM.btnGeo.classList.remove('loading');
    }
  );
}"""
# In Yandex, geolocation works best with ymaps.geolocation, but navigator is fine. I'll leave it as is if it matches. Let's just remove the replace or keep it. It's already fine.

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
