// Configurable variables for colors
const colors = {
    event: "orange",
    person: "steelblue"
};

// Set up SVG canvas for D3
const margin = { top: 20, right: 30, bottom: 30, left: 50 };
const width = document.getElementById("timeline").clientWidth - margin.left - margin.right;
const height = 500 - margin.top - margin.bottom;

const svg = d3.select("#timeline")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// Load data from API
async function loadData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/entries/");
        const data = await response.json();

        // Process data into the correct format
        data.forEach(d => {
            d.startDate = new Date(d.start_date);
            d.endDate = new Date(d.end_date);
        });

        drawVisualization(data);
    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// Function to draw visualization
function drawVisualization(data) {
    // Create x-scale (timeline)
    const xScale = d3.scaleTime()
        .domain([d3.min(data, d => d.startDate), d3.max(data, d => d.endDate)])
        .range([0, width]);

    // Create y-scale for swimlanes based on location
    const locations = [...new Set(data.map(d => d.location))];
    const yScale = d3.scaleBand()
        .domain(locations)
        .range([0, height])
        .padding(0.1);

    // Draw x-axis
    const xAxis = d3.axisBottom(xScale);
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(xAxis);

    // Draw y-axis for locations
    const yAxis = d3.axisLeft(yScale);
    svg.append("g")
        .call(yAxis);

    // Plot rectangles representing events/people
    svg.selectAll(".period")
        .data(data)
        .enter()
        .append("rect")
        .attr("x", d => xScale(d.startDate))
        .attr("y", d => yScale(d.location))
        .attr("width", d => xScale(d.endDate) - xScale(d.startDate))
        .attr("height", yScale.bandwidth() / 4)
        .attr("fill", d => d.type === "event" ? colors.event : colors.person)  // Use configurable color variables
        .on("click", (event, d) => {
            alert(`More info: ${d.details}`);
        });

    // Add text labels
    svg.selectAll(".text-label")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "text-label")
        .attr("x", d => xScale((d.startDate.getTime() + d.endDate.getTime()) / 2))
        .attr("y", d => yScale(d.location) - 5)
        .attr("text-anchor", "middle")
        .text(d => d.name);
}

// Call the function to load and draw data
loadData();
