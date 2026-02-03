// ---- MAP ----
const map = L.map("map").setView([61.185881, 5.987860], 16);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

// ---- STATE ----
const activeLayers = {};
const controls = document.getElementById("controls");

// List of rovers
const ROVERS = ["Muli", "Metrac", "Fiat", "Massey", "Tesla", ];

// ---- LOAD ALL ROVERS ----
(async function loadAllRovers() {
  for (const rover of ROVERS) {
    const { trackIndex } = await import(`./tracks/${rover}/trackIndex.js`);
    buildRoverColumn(rover, trackIndex);
  }
})();

// ---- UI BUILDER ----
function buildRoverColumn(roverName, trackIndex) {
  const roverCol = document.createElement("div");
  roverCol.className = "rover-column";

  // ---- ROVER HEADER (COLLAPSIBLE) ----
  const roverHeader = document.createElement("div");
  roverHeader.className = "rover-header";
  roverHeader.textContent = `🚗 ${roverName}`;

  const roverBody = document.createElement("div");
  roverBody.className = "collapsed"; // start collapsed

  roverHeader.addEventListener("click", () => {
    roverBody.classList.toggle("collapsed");
  });

  roverCol.appendChild(roverHeader);
  roverCol.appendChild(roverBody);

  // ---- DAYS ----
  Object.entries(trackIndex).forEach(([date, tracks]) => {
    const dayContainer = document.createElement("div");

    // ---- DAY HEADER (COLLAPSIBLE) ----
    const dayHeader = document.createElement("div");
    dayHeader.className = "day-header";
    dayHeader.textContent = `📅 ${date}`;

    const dayBody = document.createElement("div");
    dayBody.className = "collapsed"; // start collapsed

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

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";

      const label = document.createElement("label");
      label.textContent = trackInfo.label;

      const colorPicker = document.createElement("input");
      colorPicker.type = "color";
      colorPicker.value = defaultColorForRover(roverName);

      const key = `${roverName}-${date}-${trackInfo.id}`;

      // ---- TRACK INFO DISPLAY ----
      const trackInfoDisplay = document.createElement("div");
      trackInfoDisplay.className = "track-info";
      trackInfoDisplay.style.display = "none"; // hidden by default
      row.appendChild(trackInfoDisplay);

      // ---- CHECKBOX HANDLER ----
      checkbox.addEventListener("change", async () => {
        if (checkbox.checked) {
          if (!activeLayers[key]) {
            const module = await import(trackInfo.path);
            const track = module.track;
            const geojson = track.geojson;

            // add layer to map
            const layer = L.geoJSON(geojson, {
              renderer: L.canvas(),
              style: { color: colorPicker.value, weight: 3 }
            }).addTo(map);

            // hover popup
            layer.eachLayer(l => {
              const p = geojson.features[0].properties;
              l.bindPopup(`
                <strong>${track.name}</strong><br>
                Start: ${p.start_time}<br>
                End: ${p.end_time || "N/A"}<br>
                Track Time: ${p.track_time || "N/A"}<br>
                Length: ${p.track_length || "N/A"} m<br>
                Avg Speed: ${p.avg_speed || "N/A"} km/h
              `);
              l.on('mouseover', e => e.target.openPopup());
              l.on('mouseout', e => e.target.closePopup());
            });

            activeLayers[key] = layer;
            map.fitBounds(layer.getBounds());

            // update track info display
            const p = geojson.features[0].properties;
            trackInfoDisplay.innerHTML = `
              Track Time: ${p.track_time || "N/A"}<br>
              Avg Speed: ${p.avg_speed || "N/A"} km/h<br>
              Length: ${p.track_length || "N/A"} m
            `;
          }

          // show info
          trackInfoDisplay.style.display = "block";

        } else {
          // hide info
          trackInfoDisplay.style.display = "none";

          // remove map layer
          if (activeLayers[key]) {
            map.removeLayer(activeLayers[key]);
            delete activeLayers[key];
          }
        }

        // update "check all"
        checkAll.checked = trackRows.every(r => r.checkbox.checked);
      });

      // ---- COLOR PICKER ----
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
    });

    // ---- CHECK ALL HANDLER ----
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
