// Configurable variables
const config = {
    colors: {
        event: "#ff7e67",
        person: "#4e89ae"
    },
    margin: { top: 40, right: 100, bottom: 40, left: 150 },
    height: 800,
    labelPadding: 5,
    tooltipDelay: 200
};

// Set up SVG canvas for D3
const width = document.getElementById("timeline").clientWidth - config.margin.left - config.margin.right;
const height = config.height - config.margin.top - config.margin.bottom;

// Create tooltip div
const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

const svg = d3.select("#timeline")
    .append("svg")
    .attr("width", "100%")
    .attr("height", height + config.margin.top + config.margin.bottom)
    .append("g")
    .attr("transform", `translate(${config.margin.left},${config.margin.top})`);

// Load data from API
async function loadData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/entries/");
        const data = await response.json();

        // Process data into the correct format
        data.forEach(d => {
            d.startDate = new Date(d.begins);
            d.endDate = new Date(d.ends);
        });

        drawVisualization(data);
    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// Function to format tooltip content
function formatTooltip(d) {
    return `
        <strong>${d.name}</strong><br/>
        Type: ${d.type}<br/>
        Location: ${d.location}<br/>
        Period: ${d.begins} to ${d.ends}<br/>
        <hr/>
        ${d.details}
    `;
}

// Function to compute vertical positions for overlapping events
function computeRows(events, xScale) {
    // Group events by location
    const eventsByLocation = d3.group(events, d => d.location);
    
    // For each location, compute rows for overlapping events
    eventsByLocation.forEach(locationEvents => {
        // Sort events by start date
        locationEvents.sort((a, b) => a.startDate - b.startDate);
        
        // Initialize rows array
        const rows = [];
        
        // For each event, find the first available row
        locationEvents.forEach(event => {
            let rowIndex = 0;
            let foundRow = false;
            
            // Convert dates to pixels for overlap detection
            const eventStart = xScale(event.startDate);
            const eventEnd = xScale(event.endDate);
            
            // Check each existing row for overlap
            while (!foundRow && rowIndex < rows.length) {
                const row = rows[rowIndex];
                // Check if this event overlaps with any event in this row
                const hasOverlap = row.some(existingEvent => {
                    const existingStart = xScale(existingEvent.startDate);
                    const existingEnd = xScale(existingEvent.endDate);
                    return !(eventEnd < existingStart || eventStart > existingEnd);
                });
                
                if (!hasOverlap) {
                    foundRow = true;
                    row.push(event);
                } else {
                    rowIndex++;
                }
            }
            
            // If no existing row works, create a new one
            if (!foundRow) {
                rows.push([event]);
                rowIndex = rows.length - 1;
            }
            
            // Store the row index with the event
            event.row = rowIndex;
        });
        
        // Store the total number of rows for this location
        locationEvents.totalRows = rows.length;
    });
    
    return eventsByLocation;
}

// Function to draw visualization
function drawVisualization(data) {
    // Create x-scale (timeline)
    const xScale = d3.scaleTime()
        .domain([
            d3.min(data, d => d.startDate),
            d3.max(data, d => d.endDate)
        ])
        .range([0, width])
        .nice();

    // Create y-scale for swimlanes based on location
    const locations = [...new Set(data.map(d => d.location))];
    const yScale = d3.scaleBand()
        .domain(locations)
        .range([0, height])
        .padding(0.3);

    // Compute rows for overlapping events
    const eventsByLocation = computeRows(data, xScale);
    
    // Draw x-axis with grid lines
    const xAxis = d3.axisBottom(xScale)
        .ticks(d3.timeYear.every(5));
    
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-45)");

    // Add x-axis label
    svg.append("text")
        .attr("class", "axis-label")
        .attr("x", width / 2)
        .attr("y", height + config.margin.bottom - 5)
        .style("text-anchor", "middle")
        .text("Time Period");

    // Draw y-axis
    const yAxis = d3.axisLeft(yScale);
    svg.append("g")
        .call(yAxis);

    // Add y-axis label
    svg.append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -config.margin.left + 20)
        .style("text-anchor", "middle")
        .text("Location");

    // Plot rectangles representing events/people
    const bars = svg.selectAll(".period")
        .data(data)
        .enter()
        .append("rect")
        .attr("class", d => d.type === "event" ? "event-rect" : "person-rect")
        .attr("x", d => xScale(d.startDate))
        .attr("y", d => {
            const locationBandHeight = yScale.bandwidth();
            const location = d.location;
            const totalRows = eventsByLocation.get(location).totalRows;
            const rowHeight = locationBandHeight / (totalRows + 1); // +1 for padding
            return yScale(location) + (d.row * rowHeight);
        })
        .attr("width", d => Math.max(2, xScale(d.endDate) - xScale(d.startDate)))
        .attr("height", d => {
            const locationBandHeight = yScale.bandwidth();
            const location = d.location;
            const totalRows = eventsByLocation.get(location).totalRows;
            return locationBandHeight / (totalRows + 1) * 0.8; // 0.8 for vertical padding
        });

    // Update text labels
    svg.selectAll(".text-label")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "text-label")
        .attr("x", d => xScale(d.startDate) + (xScale(d.endDate) - xScale(d.startDate)) / 2)
        .attr("y", d => {
            const locationBandHeight = yScale.bandwidth();
            const location = d.location;
            const totalRows = eventsByLocation.get(location).totalRows;
            const rowHeight = locationBandHeight / (totalRows + 1);
            return yScale(location) + (d.row * rowHeight) - 5;
        })
        .attr("text-anchor", "middle")
        .text(d => d.name);

    // Add interactivity
    bars.on("mouseover", function(event, d) {
            d3.select(this)
                .style("opacity", 1);
            
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            
            tooltip.html(formatTooltip(d))
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function() {
            d3.select(this)
                .style("opacity", 0.8);
            
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });
}

// Call the function to load and draw data
loadData();
