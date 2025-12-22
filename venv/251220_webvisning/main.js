import { trackIndex } from "./tracks/trackIndex.js";

// ---- MAP ----
const map = L.map("map").setView([61.21234, 5.7123], 16);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

// Active layers cache
const activeLayers = {};

const controls = document.getElementById("controls");

// ---- UI ----
Object.entries(trackIndex).forEach(([date, tracks]) => {
  const folder = document.createElement("div");
  folder.className = "folder";

  // Title + Check All
  const headerRow = document.createElement("div");
  const checkAll = document.createElement("input");
  checkAll.type = "checkbox";
  checkAll.id = `checkall-${date}`;

  const headerLabel = document.createElement("label");
  headerLabel.textContent = ` ${date} (Check All)`;
  headerLabel.htmlFor = checkAll.id;

  headerRow.appendChild(checkAll);
  headerRow.appendChild(headerLabel);
  folder.appendChild(headerRow);

  // Track rows
  const trackRows = [];

  tracks.forEach(trackInfo => {
    const row = document.createElement("div");
    row.className = "track-row";

    // Checkbox
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";

    // Label
    const label = document.createElement("label");
    label.textContent = trackInfo.label;

    // Color picker
    const colorPicker = document.createElement("input");
    colorPicker.type = "color";
    colorPicker.value = "#ff0000";

    const key = `${date}-${trackInfo.id}`;

    // ---- CHECKBOX HANDLER ----
    checkbox.addEventListener("change", async () => {
      if (checkbox.checked) {
        if (!activeLayers[key]) {
          const module = await import(trackInfo.path);
          const geojson = module.track.geojson;

          const layer = L.geoJSON(geojson, {
            renderer: L.canvas(),
            style: { color: colorPicker.value, weight: 3 }
          }).addTo(map);

          activeLayers[key] = layer;
          map.fitBounds(layer.getBounds());
        }
      } else {
        if (activeLayers[key]) {
          map.removeLayer(activeLayers[key]);
          delete activeLayers[key];
        }
      }

      // Update "check all" state
      checkAll.checked = trackRows.every(r => r.checkbox.checked);
    });

    // ---- COLOR CHANGE HANDLER ----
    colorPicker.addEventListener("input", () => {
      if (activeLayers[key]) {
        activeLayers[key].setStyle({ color: colorPicker.value });
      }
    });

    row.appendChild(checkbox);
    row.appendChild(label);
    row.appendChild(colorPicker);
    folder.appendChild(row);

    // Keep reference for "check all"
    row.checkbox = checkbox;
    trackRows.push(row);
  });

  // ---- CHECK ALL HANDLER ----
  checkAll.addEventListener("change", () => {
    const check = checkAll.checked;
    trackRows.forEach(r => {
      if (r.checkbox.checked !== check) {
        r.checkbox.checked = check;
        r.checkbox.dispatchEvent(new Event("change"));
      }
    });
  });

  controls.appendChild(folder);
});
