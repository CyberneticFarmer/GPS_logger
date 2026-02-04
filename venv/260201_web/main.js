// ---- MAP ----
const map = L.map("map").setView([68.1, 1.0], 16);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

// ---- STATE ----
const activeLayers = {};
const controls = document.getElementById("controls");

// ---- ROVERS ----
const ROVERS = ["Muli", "Metrac", "Fiat", "Massey", "Tesla"];

// ---- GLOBAL STATE FILTER DATA ----
const stateFilters = {};
const allTrackRows = [];
const allDayContainers = [];

// ---- STATE FILTER UI ----
const stateFilterBox = document.createElement("div");
stateFilterBox.className = "state-filter";
stateFilterBox.innerHTML = "<strong>Filtrer type arbeid</strong><br>";
controls.appendChild(stateFilterBox);

// ---- LOAD ALL ROVERS ----
(async function loadAllRovers() {
  for (const rover of ROVERS) {
    const { trackIndex } = await import(`./tracks/${rover}/trackIndex.js`);
    buildRoverColumn(rover, trackIndex);
  }
})();

function anyTrackActive() {
  return Object.keys(activeLayers).length > 0;
}


// ---- UI BUILDER ----
function buildRoverColumn(roverName, trackIndex) {
  const roverCol = document.createElement("div");
  roverCol.className = "rover-column";

  const roverHeader = document.createElement("div");
  roverHeader.className = "rover-header";
  roverHeader.textContent = `🚗 ${roverName}`;

  const roverBody = document.createElement("div");
  roverBody.className = "collapsed";

  roverHeader.addEventListener("click", () => {
    roverBody.classList.toggle("collapsed");
  });

  roverCol.appendChild(roverHeader);
  roverCol.appendChild(roverBody);

  // ---- DAYS ----
  Object.entries(trackIndex).forEach(([date, tracks]) => {
    const dayContainer = document.createElement("div");
    dayContainer.className = "day-container";
    allDayContainers.push(dayContainer);

    const dayHeader = document.createElement("div");
    dayHeader.className = "day-header";
    dayHeader.textContent = `📅 ${date}`;

    const dayBody = document.createElement("div");
    dayBody.className = "collapsed";

    dayHeader.addEventListener("click", () => {
      dayBody.classList.toggle("collapsed");
    });

    dayContainer.appendChild(dayHeader);
    dayContainer.appendChild(dayBody);

    // ---- CHECK ALL ----
    const checkAllRow = document.createElement("div");
    const checkAll = document.createElement("input");
    checkAll.type = "checkbox";
    const checkAllLabel = document.createElement("label");
    checkAllLabel.textContent = " Check all tracks";
    checkAllRow.appendChild(checkAll);
    checkAllRow.appendChild(checkAllLabel);
    dayBody.appendChild(checkAllRow);

    const trackRows = [];

    // ---- TRACKS ----
    tracks.forEach(trackInfo => {
      const row = document.createElement("div");
      row.className = "track-row";
      row.dataset.state = trackInfo.state || "UNKNOWN";
      row.dayContainer = dayContainer;

      // ---- REGISTER STATE FILTER ----
      if (!stateFilters[row.dataset.state]) {
        stateFilters[row.dataset.state] = true;

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = true;

        cb.addEventListener("change", () => {
          stateFilters[row.dataset.state] = cb.checked;
          applyStateFilters();
        });

        const label = document.createElement("label");
        label.textContent = ` ${row.dataset.state}`;

        stateFilterBox.appendChild(cb);
        stateFilterBox.appendChild(label);
        stateFilterBox.appendChild(document.createElement("br"));
      }

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";

      const label = document.createElement("label");
      label.textContent = trackInfo.label;

      const colorPicker = document.createElement("input");
      colorPicker.type = "color";
      colorPicker.value = defaultColorForRover(roverName);

      const key = `${roverName}-${date}-${trackInfo.id}`;

      const trackInfoDisplay = document.createElement("div");
      trackInfoDisplay.className = "track-info";
      trackInfoDisplay.style.display = "none";
      row.appendChild(trackInfoDisplay);

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

          trackInfoDisplay.style.display = "block";
        } else {
          trackInfoDisplay.style.display = "none";
          if (activeLayers[key]) {
            map.removeLayer(activeLayers[key]);
            delete activeLayers[key];
          }
        }

        updateDayVisibility(dayContainer);
        checkAll.checked = trackRows.every(r => r.checkbox.checked);
      });

      colorPicker.addEventListener("input", () => {
        if (activeLayers[key]) {
          activeLayers[key].setStyle({ color: colorPicker.value });
        }
      });

      row.appendChild(checkbox);
      row.appendChild(label);
      row.appendChild(colorPicker);
      dayBody.appendChild(row);

      row.checkbox = checkbox;
      trackRows.push(row);
      allTrackRows.push(row);
    });

    checkAll.addEventListener("change", () => {
      trackRows.forEach(r => {
        if (r.checkbox.checked !== checkAll.checked) {
          r.checkbox.checked = checkAll.checked;
          r.checkbox.dispatchEvent(new Event("change"));
        }
      });
    });

    roverBody.appendChild(dayContainer);
  });

  controls.appendChild(roverCol);
  allDayContainers.forEach(updateDayVisibility);
}

// ---- STATE FILTER LOGIC ----
function applyStateFilters() {
  allTrackRows.forEach(row => {
    const enabled = stateFilters[row.dataset.state];
    row.style.display = enabled ? "" : "none";

    if (!enabled && row.checkbox.checked) {
      row.checkbox.checked = false;
      row.checkbox.dispatchEvent(new Event("change"));
    }
  });

  allDayContainers.forEach(updateDayVisibility);
}

// ---- DAY VISIBILITY ----
function updateDayVisibility(dayContainer) {
  const rows = dayContainer.querySelectorAll(".track-row");

  // rows visible after state filter
  const visibleRows = [...rows].filter(
    r => r.style.display !== "none"
  );

  // if no tracks active yet, show dates that have visible rows
  if (!anyTrackActive()) {
    dayContainer.style.display = visibleRows.length > 0 ? "" : "none";
    return;
  }

  // once tracks are active → only show days with checked tracks
  const anyChecked = visibleRows.some(r => r.checkbox.checked);
  dayContainer.style.display = anyChecked ? "" : "none";
}


// ---- DEFAULT COLORS ----
function defaultColorForRover(rover) {
  const colors = {
    Tesla: "#ff0000",
    Metrac: "#0066ff",
    Fiat: "#00f00f",
    Muli: "#0000ff",
    Massey: "#6666ff"
  };
  return colors[rover] || "#00aa00";
}
