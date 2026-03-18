// ── GPS location (Option 1) ───────────────────────────────────────────────────
function fetchGPSLocation() {
  if (!navigator.geolocation) {
    showAlert('Geolocation is not supported by your browser', 'error');
    return;
  }
  showAlert('Acquiring your location…', 'info');
  navigator.geolocation.getCurrentPosition(
    function (pos) {
      var lat = pos.coords.latitude;
      var lng = pos.coords.longitude;
      var csrf = document.cookie.match(/csrftoken=([^;]+)/);
      fetch('/dashboard/api/location/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf ? csrf[1] : '',
        },
        body: JSON.stringify({ lat: lat, lng: lng }),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          _setAddress(d.address || (lat.toFixed(6) + ', ' + lng.toFixed(6)), lat, lng, 'gps');
        })
        .catch(function () {
          _setAddress(lat.toFixed(6) + ', ' + lng.toFixed(6), lat, lng, 'gps');
        });
    },
    function () {
      showAlert('Location permission denied or unavailable', 'error');
    },
    { enableHighAccuracy: true }
  );
}

// ── Map modal (Option 2) ──────────────────────────────────────────────────────
var _map, _marker, _mapGeocoder;
var _pickedLat = null, _pickedLng = null, _pickedAddress = '';

function openMapModal() {
  var modal = document.getElementById('map-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  if (!_map) {
    setTimeout(_initMap, 120);
  }
}

function closeMapModal() {
  var modal = document.getElementById('map-modal');
  if (modal) modal.style.display = 'none';
}

function _initMap() {
  var mapEl = document.getElementById('google-map');
  if (!mapEl || typeof google === 'undefined') {
    var msg = document.getElementById('map-no-key-msg');
    if (msg) msg.classList.remove('hidden');
    var mapWrap = document.getElementById('google-map');
    if (mapWrap) mapWrap.classList.add('hidden');
    return;
  }

  var defaultCenter = { lat: -6.7924, lng: 39.2083 }; // Dar es Salaam
  _map = new google.maps.Map(mapEl, {
    center: defaultCenter,
    zoom: 13,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false,
  });

  _marker = new google.maps.Marker({
    position: defaultCenter,
    map: _map,
    draggable: true,
    title: 'Drag to your property',
  });

  _mapGeocoder = new google.maps.Geocoder();

  if (google.maps.places) {
    var searchInput = document.getElementById('map-search-input');
    if (searchInput) {
      var searchBox = new google.maps.places.SearchBox(searchInput);
      searchBox.addListener('places_changed', function () {
        var places = searchBox.getPlaces();
        if (!places || !places.length) return;
        var place = places[0];
        if (!place.geometry) return;
        _map.setCenter(place.geometry.location);
        _map.setZoom(17);
        _marker.setPosition(place.geometry.location);
        _updateMapPick(
          place.geometry.location.lat(),
          place.geometry.location.lng(),
          place.formatted_address || place.name
        );
      });
    }
  }

  _marker.addListener('dragend', function () {
    var pos = _marker.getPosition();
    _geocodeMapPos(pos.lat(), pos.lng());
  });

  _map.addListener('click', function (e) {
    _marker.setPosition(e.latLng);
    _geocodeMapPos(e.latLng.lat(), e.latLng.lng());
  });
}

function _geocodeMapPos(lat, lng) {
  if (_mapGeocoder) {
    _mapGeocoder.geocode({ location: { lat: lat, lng: lng } }, function (results, status) {
      var name = (status === 'OK' && results && results[0])
        ? results[0].formatted_address
        : lat.toFixed(6) + ', ' + lng.toFixed(6);
      _updateMapPick(lat, lng, name);
    });
  } else {
    _updateMapPick(lat, lng, lat.toFixed(6) + ', ' + lng.toFixed(6));
  }
}

function _updateMapPick(lat, lng, address) {
  _pickedLat = lat;
  _pickedLng = lng;
  _pickedAddress = address;
  var preview = document.getElementById('map-address-preview');
  if (preview) {
    preview.textContent = address;
    preview.classList.remove('hidden');
  }
}

function confirmMapLocation() {
  if (_pickedLat === null) {
    showAlert('Click on the map or search to pin a location first', 'warning');
    return;
  }
  _setAddress(_pickedAddress, _pickedLat, _pickedLng, 'map_pin');
  closeMapModal();
}

// ── Shared helpers ────────────────────────────────────────────────────────────
function _setAddress(name, lat, lng, source) {
  document.getElementById('id_address_name').value = name;
  document.getElementById('id_address_lat').value = lat;
  document.getElementById('id_address_lng').value = lng;
  document.getElementById('id_address_source').value = source;

  var textEl = document.getElementById('address-display-text');
  var wrapEl = document.getElementById('address-display');
  var sourceEl = document.getElementById('address-source-badge');
  if (textEl) textEl.textContent = name;
  if (wrapEl) wrapEl.classList.remove('hidden');
  if (sourceEl) {
    sourceEl.textContent = source === 'gps' ? 'GPS tracked' : 'Map pin';
    sourceEl.classList.remove('hidden');
  }
  showAlert('Location set: ' + name, 'success');
}

function clearAddress() {
  ['id_address_name', 'id_address_lat', 'id_address_lng', 'id_address_source'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.value = '';
  });
  var wrapEl = document.getElementById('address-display');
  if (wrapEl) wrapEl.classList.add('hidden');
}

// ── Delete confirmation ───────────────────────────────────────────────────────
function confirmDelete() {
  var url = window.PROPERTY_DELETE_URL
    || (document.querySelector('[data-delete-url]') || {}).dataset.deleteUrl
    || '#';
  showConfirm('Are you sure you want to delete this property? This action cannot be undone.', function () {
    window.location.href = url;
  });
}

// ── Image preview (new uploads) ───────────────────────────────────────────────
(function () {
  var inp = document.getElementById('id_new_images');
  if (!inp) return;
  inp.addEventListener('change', function () {
    var wrap = document.getElementById('new-img-previews');
    wrap.innerHTML = '';
    var files = Array.from(this.files).slice(0, 5);
    if (!files.length) { wrap.classList.add('hidden'); return; }
    wrap.classList.remove('hidden');
    files.forEach(function (f) {
      var r = new FileReader();
      r.onload = function (e) {
        var d = document.createElement('div');
        d.className = 'h-24 overflow-hidden border border-gray-200 border-l-4 border-l-brown-300';
        d.innerHTML = '<img src="' + e.target.result + '" class="w-full h-full object-cover">';
        wrap.appendChild(d);
      };
      r.readAsDataURL(f);
    });
  });
})();

// ── Delete existing property image ────────────────────────────────────────────
function deletePropertyImage(id, url) {
  if (!confirm('Remove this image?')) return;
  var csrf = document.cookie.match(/csrftoken=([^;]+)/);
  fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf ? csrf[1] : '', 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) {
        var el = document.getElementById('img-wrap-' + id);
        if (el) el.remove();
      }
    });
}
