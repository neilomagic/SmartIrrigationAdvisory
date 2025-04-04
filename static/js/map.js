// map.js (Leaflet Logic)
document.addEventListener("DOMContentLoaded", function () {
  // Initialize map centered on Nwoya
  const map = L.map("map").setView([2.6342, 31.9619], 13);

  // Add base map layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
  }).addTo(map);

  // Add field boundary
  function addFieldBoundary(fieldId) {
    fetch(`/api/fields/${fieldId}/`)
      .then((response) => response.json())
      .then((data) => {
        const field = L.geoJSON(data.boundary, {
          style: {
            color: "#4CAF50",
            weight: 2,
            fillOpacity: 0.2,
          },
        }).addTo(map);
        map.fitBounds(field.getBounds());
      });
  }

  // Load field data (assuming field ID is available in template)
  const fieldId = document.getElementById("field-id").dataset.fieldId;
  addFieldBoundary(fieldId);
});
