// ==========================
// CONFIG
// ==========================
const sensors = ["A1", "B4", "TEMP2"]; // <-- ADD SENSORS HERE
const dataFolder = "data";

// ==========================
// SETUP UI
// ==========================
const select = document.getElementById("sensorSelect");

sensors.forEach(name => {
  const option = document.createElement("option");
  option.value = name;
  option.textContent = name;
  select.appendChild(option);
});

// ==========================
// CHART SETUP
// ==========================
const ctx = document.getElementById("sensorChart").getContext("2d");
let chart = null;

// ==========================
// LOAD SENSOR DATA
// ==========================
function loadSensor(sensorName) {
  const scriptId = "sensor-script";

  // Remove previous sensor script
  const old = document.getElementById(scriptId);
  if (old) old.remove();

  // Load new sensor file
  const script = document.createElement("script");
  script.id = scriptId;
  script.src = `${dataFolder}/${sensorName}.js`;

  script.onload = () => {
    drawChart(sensorName, sensorData);
  };

  script.onerror = () => {
    alert(`Failed to load data for sensor ${sensorName}`);
  };

  document.body.appendChild(script);
}

// ==========================
// DRAW / UPDATE CHART
// ==========================
function drawChart(sensorName, data) {
  const values = data.map(d => ({
    x: new Date(d.time),
    y: d.value
  }));

  const batteries = data.map(d => ({
    x: new Date(d.time),
    y: d.battery
  }));

  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: `${sensorName} Value`,
          data: values,
          borderColor: "blue",
          tension: 0.2,
          yAxisID: "y"
        },
        {
          label: `${sensorName} Battery`,
          data: batteries,
          borderColor: "green",
          tension: 0.2,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          type: "time",
          title: {
            display: true,
            text: "Time"
          }
        },
        y: {
          position: "left",
          title: {
            display: true,
            text: "Sensor Value"
          }
        },
        y1: {
          position: "right",
          grid: {
            drawOnChartArea: false
          },
          title: {
            display: true,
            text: "Battery Voltage (V)"
          }
        }
      }
    }
  });
}

// ==========================
// EVENTS
// ==========================
select.addEventListener("change", () => {
  loadSensor(select.value);
});

// Load first sensor by default
loadSensor(sensors[0]);
