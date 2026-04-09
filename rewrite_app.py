import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

def repl(old, new):
    global js
    js = js.replace(old, new)


# Routes clearing
repl("layers.routes.clearLayers();", "layers.routes.removeAll();")
repl("layers.searchMarkers.clearLayers();", "layers.searchMarkers.removeAll();")
repl("layers.draftMarkers.clearLayers();", "layers.draftMarkers.removeAll();")

# addPointToDraft
repl("""  state.draftWaypoints.push([lat, lon]);
  updateDraftMap();
  map.flyTo([lat, lon], 14, { duration: 1.0 });""", """  state.draftWaypoints.push([lat, lon]);
  updateDraftMap();
  map.setCenter([lat, lon], 14, { duration: 1000 });""")

# handleLocationSelection
repl("""  // If we are in "Create Route" tab, add as a waypoint
  if (!DOM.tabContentCreate.classList.contains('hidden')) {
    if (!state.user) {
      alert("Пожалуйста, войдите, чтобы создавать маршруты!");
      return;
    }
    state.draftWaypoints.push([lat, lon]);
    updateDraftMap();
    map.flyTo([lat, lon], 14, { duration: 1.0 });
  } else {
    // Otherwise just fly to it and show a temporary popup
    map.flyTo([lat, lon], 14, { duration: 1.5 });
    const searchMarker = L.marker([lat, lon]).addTo(map)
      .bindPopup(`<b>${name}</b>`).openPopup();
      
    map.once('click', () => {
      if(map.hasLayer(searchMarker)) map.removeLayer(searchMarker);
    });
  }""", """  // If we are in "Create Route" tab, add as a waypoint
  if (!DOM.tabContentCreate.classList.contains('hidden')) {
    if (!state.user) {
      alert("Пожалуйста, войдите, чтобы создавать маршруты!");
      return;
    }
    state.draftWaypoints.push([lat, lon]);
    updateDraftMap();
    map.setCenter([lat, lon], 14, { duration: 1000 });
  } else {
    // Otherwise just fly to it and show a temporary popup
    map.setCenter([lat, lon], 14, { duration: 1500 });
    const searchMarker = new ymaps.Placemark([lat, lon], {
        balloonContent: `<b>${name}</b>`
    });
    map.geoObjects.add(searchMarker);
    searchMarker.balloon.open();
      
    map.events.once('click', () => {
      map.geoObjects.remove(searchMarker);
    });
  }""")

# displayRoute polyline
repl("""    if (latlngs.length > 0) {
      const polyline = L.polyline(latlngs, {color: 'var(--accent-color)', weight: 4}).addTo(layers.routes);
      map.flyTo(latlngs[0], 14, { duration: 1.5 });
    }""", """    if (latlngs.length > 0) {
      const polyline = new ymaps.Polyline(latlngs, {}, {
          strokeColor: '#3b82f6',
          strokeWidth: 4
      });
      layers.routes.add(polyline);
      map.setCenter(latlngs[0], 14, { duration: 1500 });
    }""")

# map.fitBounds
repl("map.fitBounds(layers.searchMarkers.getBounds(), { padding: [50, 50], maxZoom: 15 });", "map.setBounds(layers.searchMarkers.getBounds(), { checkZoomRange: true });")

# bounds nominatim
repl("""      const bounds = map.getBounds();
      const viewbox = `${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()},${bounds.getSouth()}`;""", """      const bounds = map.getBounds();
      const viewbox = `${bounds[0][1]},${bounds[1][0]},${bounds[1][1]},${bounds[0][0]}`;""")

# bounds photon
repl("""    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;""", """    const bounds = map.getBounds();
    const bbox = `${bounds[0][1]},${bounds[0][0]},${bounds[1][1]},${bounds[1][0]}`;""")

# draw draft polylines
repl("""    layers.draftLine = L.polyline(state.draftWaypoints, {
      color: '#3b82f6',
      weight: 4,
      dashArray: '10, 10'
    }).addTo(layers.draftMarkers);""", """    layers.draftLine = new ymaps.Polyline(state.draftWaypoints, {}, {
      strokeColor: '#3b82f6',
      strokeWidth: 4,
      strokeStyle: '10 10'
    });
    layers.draftMarkers.add(layers.draftLine);""")

# draw draft markers
repl("""    const pt = state.draftWaypoints[i];
    L.circleMarker(pt, {
      radius: 6,
      color: '#2563eb',
      fillColor: '#eff6ff',
      fillOpacity: 1,
      weight: 2
    }).addTo(layers.draftMarkers);""", """    const pt = state.draftWaypoints[i];
    const point = new ymaps.Placemark(pt, {}, {
      preset: "islands#circleIcon",
      iconColor: '#3b82f6'
    });
    layers.draftMarkers.add(point);""")


# photon markers
repl("""        // Add marker for this result
        const marker = L.circleMarker([coords[1], coords[0]], {
          radius: 8,
          color: '#3b82f6',
          fillColor: '#60a5fa',
          fillOpacity: 0.8
        }).bindPopup(`<b>${title}</b><br>${desc}`).addTo(layers.searchMarkers);
        
        marker.on('click', () => {""", """        // Add marker for this result
        const marker = new ymaps.Placemark([coords[1], coords[0]], {
            balloonContent: `<b>${title}</b><br>${desc}`
        }, {
            preset: 'islands#blueIcon'
        });
        layers.searchMarkers.add(marker);
        
        marker.events.add('click', () => {""")


# map click event reverse geocoding
repl("""async function onMapClick(e) {
  const lat = e.latlng.lat;
  const lon = e.latlng.lng;""", """async function onMapClick(e) {
  const coords = e.get('coords');
  const lat = coords[0];
  const lon = coords[1];""")

repl("""      L.popup()
        .setLatLng([lat, lon])
        .setContent(`<div style="max-width:250px;"><b>${title}</b><p style="font-size:12px;margin-top:4px;">${desc}</p></div>`)
        .openOn(map);""", """      const popupMarker = new ymaps.Placemark([lat, lon], {
          balloonContent: `<div style="max-width:250px;"><b>${title}</b><p style="font-size:12px;margin-top:4px;">${desc}</p></div>`
      });
      map.geoObjects.add(popupMarker);
      popupMarker.balloon.open();
      
      map.events.once('click', () => {
         map.geoObjects.remove(popupMarker);
      });""")

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
