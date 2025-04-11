let chartData; // Datos de la gráfica
const timeFrames = ["daily", "weekly", "monthly", "quarter", "year"];

const timeFrameLabels = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  quarter: "Quarterly",
  year: "Yearly",
}; // Etiquetas de tiempo

const timeFrameKeyMap = {
  daily: "daily_data",
  weekly: "weekly_data",
  monthly: "monthly_data",
  quarter: "quarterly_data",
  year: "yearly_data",
};

let currentTimeFrameIndex = 0;

// Configuración de cada gráfica con nuevos tipos
const chartsConfig = [
  {
    container: "#chart-production",
    metric: "production",
    title: "Production",
    yLabel: "units",
    color: "#ffb6c1",
    type: "bar",
    isMainChart: true, // Marcar como gráfica principal
  },
  {
    container: "#chart-rejected",
    metric: "rejected_units",
    title: "Rejected Units",
    yLabel: "units",
    color: "#ff94c2",
    type: "pie",
    isMainChart: false,
  },
  {
    container: "#chart-delay",
    metric: "avg_delay_minutes",
    title: "Average Delay",
    yLabel: "minutes",
    color: "#ffc3a0",
    type: "bar",
    isMainChart: false,
  },
  {
    container: "#chart-accidents",
    metric: "accidents",
    title: "Accidents",
    yLabel: "incidents",
    color: "#add8e6",
    type: "line",
    isMainChart: false,
  },
  {
    container: "#chart-occupancy",
    metric: "occupancy_hours",
    title: "Occupancy Hours",
    yLabel: "hours",
    color: "#c3b1e1",
    type: "area",
    isMainChart: false,
  },
  {
    container: "#chart-rejection-percentage",
    metric: "rejection_percentage",
    title: "Rejection Percentage",
    yLabel: "%",
    color: "#f0e68c",
    type: "pie",
    isMainChart: false,
  },
];

// Inicializar gráficas
function initializeCharts() {
  chartsConfig.forEach((config) => {
    const container = d3.select(config.container);

    // Configurar márgenes basados en si es la gráfica principal o no
    const margin = config.isMainChart
      ? { left: 100, right: 40, top: 60, bottom: 100 }
      : { left: 60, right: 20, top: 40, bottom: 60 };

    // Obtener ancho y alto del contenedor
    const width = container.node().clientWidth - margin.left - margin.right;
    const height = container.node().clientHeight - margin.top - margin.bottom;

    const svg = container
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .style("background", "#fffafc");

    // Hacer SVG responsive
    svg.attr(
      "viewBox",
      `0 0 ${width + margin.left + margin.right} ${
        height + margin.top + margin.bottom
      }`
    );
    svg.attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(chartData.map((d) => d.name))
      .range([0, width])
      .padding(0.4);

    const y = d3.scaleLinear().range([height, 0]);

    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("fill", "#ff69b4")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    g.append("g")
      .attr("class", "y-axis")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d} ${config.yLabel}`)
      )
      .selectAll(".tick text")
      .style("fill", "#ff69b4");

    // Tamaño de fuente mayor para la principal
    const titleFontSize = config.isMainChart ? "24px" : "16px";

    // Título de gráfica
    g.append("text")
      .attr("class", "chart-title")
      .attr("x", width / 2)
      .attr("y", config.isMainChart ? -40 : -25)
      .style("text-anchor", "middle")
      .style("fill", "#d81b60")
      .style("font-size", titleFontSize)
      .style("font-family", "'Poppins', 'Helvetica Neue', sans-serif")
      .style("font-weight", "600")
      .text(config.title);

    config.margin = margin;
    config.g = g;
    config.x = x;
    config.y = y;
    config.width = width;
    config.height = height;
  });
}

// Actualizar todas las gráficas
function updateCharts(timeFrame) {
  chartsConfig.forEach((config) => {
    const maxValue = d3.max(
      chartData,
      (d) => d[timeFrameKeyMap[timeFrame]][config.metric]
    );
    config.y.domain([0, maxValue * 1.1]);

    if (config.type === "bar") {
      const bars = config.g.selectAll("rect").data(chartData);

      bars
        .enter()
        .append("rect")
        .attr("x", (d) => config.x(d.name))
        .attr("width", config.x.bandwidth())
        .attr("fill", config.color)
        .attr("rx", 12)
        .merge(bars)
        .transition()
        .duration(500)
        .attr("y", (d) =>
          config.y(d[timeFrameKeyMap[timeFrame]][config.metric])
        )
        .attr(
          "height",
          (d) =>
            config.height -
            config.y(d[timeFrameKeyMap[timeFrame]][config.metric])
        );

      // Etiquetas de valor para la gráfica principal
      if (config.isMainChart) {
        const valueLabels = config.g.selectAll(".value-label").data(chartData);

        valueLabels
          .enter()
          .append("text")
          .attr("class", "value-label")
          .attr("text-anchor", "middle")
          .style("fill", "#ff69b4")
          .style("font-weight", "bold")
          .merge(valueLabels)
          .transition()
          .duration(500)
          .attr("x", (d) => config.x(d.name) + config.x.bandwidth() / 2)
          .attr(
            "y",
            (d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]) - 10
          )
          .text((d) => d[timeFrameKeyMap[timeFrame]][config.metric]);
      }
    } else if (config.type === "pie") {
      // Limpiar ejes y labels
      config.g.selectAll(".x-axis, .y-axis").remove();

      const radius = Math.min(config.width, config.height) / 2;
      const pie = d3
        .pie()
        .value((d) => d[timeFrameKeyMap[timeFrame]][config.metric]);
      const arc = d3.arc().innerRadius(0).outerRadius(radius);

      const totalWidth = radius * 2 + 200;
      const offsetX = (config.width - totalWidth) / 2;

      // Posicionar gráfica a la izquierda
      const pieGroup = config.g.selectAll(".pie-group").data([null]);
      const enterGroup = pieGroup
        .enter()
        .append("g")
        .attr("class", "pie-group");
      const finalGroup = enterGroup.merge(pieGroup);
      finalGroup.attr(
        "transform",
        `translate(${offsetX + radius}, ${config.height / 2})`
      );

      // Dibujar pastel
      const path = finalGroup.selectAll("path").data(pie(chartData));

      path
        .enter()
        .append("path")
        .merge(path)
        .transition()
        .duration(500)
        .attr("d", arc)
        .attr("fill", (d, i) => d3.schemePastel1[i % d3.schemePastel1.length]);

      path.exit().remove();

      // Crear leyenda a la derecha y centrada verticalmente
      const legend = config.g.selectAll(".legend").data(chartData);
      const legendGroup = legend.enter().append("g").attr("class", "legend");

      legendGroup
        .append("rect")
        .attr("width", 14)
        .attr("height", 14)
        .attr("fill", (d, i) => d3.schemePastel1[i % d3.schemePastel1.length]);

      legendGroup
        .append("text")
        .attr("x", 20)
        .attr("y", 12)
        .text(
          (d) => `${d.name}: ${d[timeFrameKeyMap[timeFrame]][config.metric]}`
        )
        .style("fill", "#333")
        .style("font-size", "12px");

      const legendHeight = chartData.length * 20;
      const legendY = (config.height - legendHeight) / 2;

      legendGroup.attr(
        "transform",
        (d, i) => `translate(${offsetX + radius * 2 + 40}, ${legendY + i * 20})`
      );

      legend.exit().remove();
    } else if (config.type === "line") {
      const line = d3
        .line()
        .x((d) => config.x(d.name) + config.x.bandwidth() / 2)
        .y((d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]));

      const linePath = config.g.selectAll(".line").data([chartData]);

      linePath
        .enter()
        .append("path")
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", config.color)
        .attr("stroke-width", 3)
        .merge(linePath)
        .transition()
        .duration(500)
        .attr("d", line);

      // Agregar círculos en los puntos de datos
      const circles = config.g.selectAll(".data-point").data(chartData);

      circles
        .enter()
        .append("circle")
        .attr("class", "data-point")
        .attr("r", 5)
        .attr("fill", config.color)
        .merge(circles)
        .transition()
        .duration(500)
        .attr("cx", (d) => config.x(d.name) + config.x.bandwidth() / 2)
        .attr("cy", (d) =>
          config.y(d[timeFrameKeyMap[timeFrame]][config.metric])
        );
    } else if (config.type === "area") {
      const area = d3
        .area()
        .x((d) => config.x(d.name) + config.x.bandwidth() / 2)
        .y0(config.height)
        .y1((d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]));

      const areaPath = config.g.selectAll(".area").data([chartData]);

      areaPath
        .enter()
        .append("path")
        .attr("class", "area")
        .attr("fill", config.color)
        .attr("fill-opacity", 0.7)
        .merge(areaPath)
        .transition()
        .duration(500)
        .attr("d", area);
    }

    config.g
      .select(".y-axis")
      .transition()
      .duration(500)
      .call(
        d3
          .axisLeft(config.y)
          .ticks(5)
          .tickFormat((d) => `${d} ${config.yLabel}`)
      );
  });

  // Actualizar etiqueta de tiempo
  document.getElementById("timeframe-label").textContent =
    timeFrameLabels[timeFrame];
}

// Inicializar solo la gráfica principal
function initializeMainChartOnly() {
  const mainChart = chartsConfig.find((config) => config.isMainChart);
  if (mainChart) {
    const container = d3.select(mainChart.container);

    // Configurar márgenes para la gráfica principal
    const margin = { left: 100, right: 40, top: 60, bottom: 100 };

    // Obtener ancho y alto del contenedor
    const width = container.node().clientWidth - margin.left - margin.right;
    const height = container.node().clientHeight - margin.top - margin.bottom;

    const svg = container
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .style("background", "#fffafc");

    // Viewport para hacer SVG responsive
    svg.attr(
      "viewBox",
      `0 0 ${width + margin.left + margin.right} ${
        height + margin.top + margin.bottom
      }`
    );
    svg.attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(chartData.map((d) => d.name))
      .range([0, width])
      .padding(0.4);

    const y = d3.scaleLinear().range([height, 0]);

    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("fill", "#ff69b4")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    g.append("g")
      .attr("class", "y-axis")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d} ${mainChart.yLabel}`)
      )
      .selectAll(".tick text")
      .style("fill", "#ff69b4");

    // Título de gráfica
    g.append("text")
      .attr("class", "chart-title")
      .attr("x", width / 2)
      .attr("y", -30)
      .style("text-anchor", "middle")
      .style("fill", "#ff69b4")
      .style("font-size", "24px")
      .style("font-family", "'Poppins', cursive")
      .text(mainChart.title);

    mainChart.margin = margin;
    mainChart.g = g;
    mainChart.x = x;
    mainChart.y = y;
    mainChart.width = width;
    mainChart.height = height;
  }
}

// Inicializar una gráfica secundaria específica
function initializeSecondaryChart(chartId) {
  // Ocultar el placeholder
  document.getElementById("chart-placeholder").style.display = "none";

  // Ocultar todas las vistas de gráficas
  document.querySelectorAll(".chart-view").forEach((el) => {
    el.style.display = "none";
  });

  // Mostrar la gráfica seleccionada
  const chartElement = document.getElementById(`chart-${chartId}`);
  chartElement.style.display = "block";

  // Limpiar cualquier gráfica existente
  d3.select(`#chart-${chartId}`).selectAll("svg").remove();

  // Encontrar la configuración de la gráfica
  const config = chartsConfig.find((c) => c.container === `#chart-${chartId}`);

  if (config) {
    const container = d3.select(config.container);

    // Configurar márgenes
    const margin = { left: 60, right: 20, top: 40, bottom: 60 };

    // Obtener ancho y alto del contenedor
    const width = container.node().clientWidth - margin.left - margin.right;
    const height = container.node().clientHeight - margin.top - margin.bottom;

    const svg = container
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .style("background", "#fffafc");

    // Viewport para hacer SVG responsive
    svg.attr(
      "viewBox",
      `0 0 ${width + margin.left + margin.right} ${
        height + margin.top + margin.bottom
      }`
    );
    svg.attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const x = d3
      .scaleBand()
      .domain(chartData.map((d) => d.name))
      .range([0, width])
      .padding(0.4);

    const y = d3.scaleLinear().range([height, 0]);

    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0, ${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("fill", "#ff69b4")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    g.append("g")
      .attr("class", "y-axis")
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickFormat((d) => `${d} ${config.yLabel}`)
      )
      .selectAll(".tick text")
      .style("fill", "#ff69b4");

    // Título de gráfica
    g.append("text")
      .attr("class", "chart-title")
      .attr("x", width / 2)
      .attr("y", -15)
      .style("text-anchor", "middle")
      .style("fill", "#ff69b4")
      .style("font-size", "18px")
      .style("font-family", "'Poppins', cursive")
      .text(config.title);

    config.margin = margin;
    config.g = g;
    config.x = x;
    config.y = y;
    config.width = width;
    config.height = height;

    // Actualizar la gráfica con los datos actuales
    updateChart(config, timeFrames[currentTimeFrameIndex]);
  }
}

// Actualizar una gráfica específica
function updateChart(config, timeFrame) {
  const maxValue = d3.max(
    chartData,
    (d) => d[timeFrameKeyMap[timeFrame]][config.metric]
  );
  config.y.domain([0, maxValue * 1.1]);

  if (config.type === "bar") {
    const bars = config.g.selectAll("rect").data(chartData);

    bars
      .enter()
      .append("rect")
      .attr("x", (d) => config.x(d.name))
      .attr("width", config.x.bandwidth())
      .attr("fill", config.color)
      .attr("rx", 12)
      .merge(bars)
      .transition()
      .duration(500)
      .attr("y", (d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]))
      .attr(
        "height",
        (d) =>
          config.height - config.y(d[timeFrameKeyMap[timeFrame]][config.metric])
      );

    // Para la gráfica principal de barras, agregar etiquetas de valor
    if (config.isMainChart) {
      const valueLabels = config.g.selectAll(".value-label").data(chartData);

      valueLabels
        .enter()
        .append("text")
        .attr("class", "value-label")
        .attr("text-anchor", "middle")
        .style("fill", "#ff69b4")
        .style("font-weight", "bold")
        .merge(valueLabels)
        .transition()
        .duration(500)
        .attr("x", (d) => config.x(d.name) + config.x.bandwidth() / 2)
        .attr(
          "y",
          (d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]) - 10
        )
        .text((d) => d[timeFrameKeyMap[timeFrame]][config.metric]);
    }
  } else if (config.type === "pie") {
    // Limpiar ejes y labels
    config.g.selectAll(".x-axis, .y-axis").remove();

    const radius = Math.min(config.width, config.height) / 2;
    const pie = d3
      .pie()
      .value((d) => d[timeFrameKeyMap[timeFrame]][config.metric]);
    const arc = d3.arc().innerRadius(0).outerRadius(radius);

    // Calcular posición centrada horizontalmente
    const totalWidth = radius * 2 + 200; // 200 para la leyenda
    const offsetX = (config.width - totalWidth) / 2;

    // Posicionar gráfica a la izquierda
    const pieGroup = config.g.selectAll(".pie-group").data([null]);
    const enterGroup = pieGroup.enter().append("g").attr("class", "pie-group");
    const finalGroup = enterGroup.merge(pieGroup);
    finalGroup.attr(
      "transform",
      `translate(${offsetX + radius}, ${config.height / 2})`
    );

    // Dibujar pastel
    const path = finalGroup.selectAll("path").data(pie(chartData));

    path
      .enter()
      .append("path")
      .merge(path)
      .transition()
      .duration(500)
      .attr("d", arc)
      .attr("fill", (d, i) => d3.schemePastel1[i % d3.schemePastel1.length]);

    path.exit().remove();

    // Crear leyenda a la derecha y centrada verticalmente
    const legend = config.g.selectAll(".legend").data(chartData);
    const legendGroup = legend.enter().append("g").attr("class", "legend");

    legendGroup
      .append("rect")
      .attr("width", 14)
      .attr("height", 14)
      .attr("fill", (d, i) => d3.schemePastel1[i % d3.schemePastel1.length]);

    legendGroup
      .append("text")
      .attr("x", 20)
      .attr("y", 12)
      .text((d) => `${d.name}: ${d[timeFrameKeyMap[timeFrame]][config.metric]}`)
      .style("fill", "#333")
      .style("font-size", "12px");

    const legendHeight = chartData.length * 20;
    const legendY = (config.height - legendHeight) / 2;

    legendGroup.attr(
      "transform",
      (d, i) => `translate(${offsetX + radius * 2 + 40}, ${legendY + i * 20})`
    );

    legend.exit().remove();
  } else if (config.type === "line") {
    const line = d3
      .line()
      .x((d) => config.x(d.name) + config.x.bandwidth() / 2)
      .y((d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]));

    const linePath = config.g.selectAll(".line").data([chartData]);

    linePath
      .enter()
      .append("path")
      .attr("class", "line")
      .attr("fill", "none")
      .attr("stroke", config.color)
      .attr("stroke-width", 3)
      .merge(linePath)
      .transition()
      .duration(500)
      .attr("d", line);

    // Agregar círculos en los puntos de datos
    const circles = config.g.selectAll(".data-point").data(chartData);

    circles
      .enter()
      .append("circle")
      .attr("class", "data-point")
      .attr("r", 5)
      .attr("fill", config.color)
      .merge(circles)
      .transition()
      .duration(500)
      .attr("cx", (d) => config.x(d.name) + config.x.bandwidth() / 2)
      .attr("cy", (d) =>
        config.y(d[timeFrameKeyMap[timeFrame]][config.metric])
      );
  } else if (config.type === "area") {
    const area = d3
      .area()
      .x((d) => config.x(d.name) + config.x.bandwidth() / 2)
      .y0(config.height)
      .y1((d) => config.y(d[timeFrameKeyMap[timeFrame]][config.metric]));

    const areaPath = config.g.selectAll(".area").data([chartData]);

    areaPath
      .enter()
      .append("path")
      .attr("class", "area")
      .attr("fill", config.color)
      .attr("fill-opacity", 0.7)
      .merge(areaPath)
      .transition()
      .duration(500)
      .attr("d", area);
  }

  config.g
    .select(".y-axis")
    .transition()
    .duration(500)
    .call(
      d3
        .axisLeft(config.y)
        .ticks(5)
        .tickFormat((d) => `${d} ${config.yLabel}`)
    );
}

// Actualizar todas las gráficas
function updateCharts(timeFrame) {
  // Actualizar la gráfica principal
  const mainChart = chartsConfig.find((config) => config.isMainChart);
  if (mainChart) {
    updateChart(mainChart, timeFrame);
  }

  // Buscar el botón activo
  const activeButton = document.querySelector(".chart-btn.active");
  if (activeButton) {
    // Actualizar la gráfica secundaria activa
    const chartId = activeButton.dataset.chart;
    const secondaryChart = chartsConfig.find(
      (c) => c.container === `#chart-${chartId}`
    );
    if (secondaryChart) {
      updateChart(secondaryChart, timeFrame);
    }
  }

  // Actualizar etiqueta de tiempo
  document.getElementById("timeframe-label").textContent =
    timeFrameLabels[timeFrame];
}

// Configurar eventos de botones de gráficas
function setupChartButtons() {
  document.querySelectorAll(".chart-btn").forEach((button) => {
    button.addEventListener("click", () => {
      // Remover clase activa de todos los botones
      document.querySelectorAll(".chart-btn").forEach((btn) => {
        btn.classList.remove("active");
      });

      // Agregar clase activa al botón seleccionado
      button.classList.add("active");

      // Inicializar la gráfica seleccionada
      const chartId = button.dataset.chart;
      initializeSecondaryChart(chartId);
    });
  });
}

// Cargar datos y eventos
d3.json("data/StationsInfo1.json")
  .then((data) => {
    chartData = data;
    console.log("Ejemplo de datos:", chartData[0]);

    // Inicializar solo la gráfica principal
    initializeMainChartOnly();

    // Actualizar la gráfica principal con los datos actuales
    const mainChart = chartsConfig.find((config) => config.isMainChart);
    if (mainChart) {
      updateChart(mainChart, timeFrames[currentTimeFrameIndex]);
    }

    // Configurar eventos de botones de gráficas
    setupChartButtons();

    // Manejar redimensionamiento de la ventana
    window.addEventListener("resize", () => {
      // Reinicializar la gráfica principal
      d3.select("#chart-production").selectAll("svg").remove();
      initializeMainChartOnly();
      updateChart(mainChart, timeFrames[currentTimeFrameIndex]);

      // Reinicializar la gráfica secundaria activa si existe
      const activeButton = document.querySelector(".chart-btn.active");
      if (activeButton) {
        const chartId = activeButton.dataset.chart;
        initializeSecondaryChart(chartId);
      }
    });
  })
  .catch(console.error);

// Eventos de botones de tiempo
document.getElementById("prev-btn").addEventListener("click", () => {
  currentTimeFrameIndex =
    (currentTimeFrameIndex - 1 + timeFrames.length) % timeFrames.length;
  updateCharts(timeFrames[currentTimeFrameIndex]);
});

document.getElementById("next-btn").addEventListener("click", () => {
  currentTimeFrameIndex = (currentTimeFrameIndex + 1) % timeFrames.length;
  updateCharts(timeFrames[currentTimeFrameIndex]);
});
