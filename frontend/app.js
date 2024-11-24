// Configurable variables
const config = {
    apiBaseUrl: CONFIG.apiBaseUrl,
    colors: {
        event: "#ff7e67",
        person: "#4e89ae"
    },
    storyColors: d3.schemeCategory10,  // D3's built-in color scheme for stories
    margin: { top: 40, right: 100, bottom: 40, left: 150 },
    height: 600,  // Reduced height
    labelPadding: 5,
    tooltipDelay: 200,
    storyLineOpacity: 0.7,  // Increased opacity
    storyLineWidth: 3,      // Increased width
    maxLanes: 3  // Limit maximum number of lanes per location
};

// Set up SVG canvas for D3
const width = document.getElementById("timeline").clientWidth - config.margin.left - config.margin.right;
const height = config.height - config.margin.top - config.margin.bottom;

// Create tooltip div
const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

// Create story filter div
const storyFilter = d3.select("#timeline")
    .append("div")
    .attr("class", "story-filter")
    .style("margin-bottom", "20px");

// Create location filter div
const locationFilter = d3.select("#timeline")
    .append("div")
    .attr("class", "location-filter")
    .style("margin-bottom", "20px");

// Create date filter div
const dateFilter = d3.select("#timeline")
    .append("div")
    .attr("class", "date-filter")
    .style("margin-bottom", "20px");

// Create main SVG and group for visualization
const svg = d3.select("#timeline")
    .append("svg")
    .attr("width", "100%")
    .attr("height", config.height + config.margin.top + config.margin.bottom)
    .attr("viewBox", [0, 0, width + config.margin.left + config.margin.right, config.height + config.margin.top + config.margin.bottom])
    .attr("preserveAspectRatio", "xMidYMid meet");

// Create a group for zoom transformation
const mainGroup = svg.append("g")
    .attr("transform", `translate(${config.margin.left}, ${config.margin.top})`);

// Create clip path to prevent drawing outside the timeline area
svg.append("defs").append("clipPath")
    .attr("id", "clip")
    .append("rect")
    .attr("width", width)
    .attr("height", config.height);

// Global state
let xScale;
let xAxis;
let allData;
let allStories;
let activeStories = new Set();
let activeLocations = new Set();
let timeRange = {
    start: null,
    end: null
};

// Helper function to convert year and era to numeric year
function yearToNumeric(year, era) {
    if (!year) return null;
    return era === 'BCE' ? -Math.abs(year) : Math.abs(year);
}

// Helper function to initialize date inputs
function initializeDateInputs(data) {
    const timeExtent = d3.extent(data.flatMap(d => [d.begins, d.ends]));
    const startYear = Math.abs(timeExtent[0]);
    const endYear = new Date().getFullYear();
    
    // Set initial values
    document.getElementById('start-year').value = startYear;
    document.getElementById('start-era').value = timeExtent[0] < 0 ? 'BCE' : 'CE';
    document.getElementById('end-year').value = endYear;
    document.getElementById('end-era').value = 'CE';
    
    // Add event listeners
    ['start-year', 'end-year', 'start-era', 'end-era'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            const startYear = document.getElementById('start-year').value;
            const startEra = document.getElementById('start-era').value;
            const endYear = document.getElementById('end-year').value;
            const endEra = document.getElementById('end-era').value;
            
            timeRange.start = yearToNumeric(startYear, startEra);
            timeRange.end = yearToNumeric(endYear, endEra);
            
            if (timeRange.start !== null && timeRange.end !== null) {
                drawVisualization(filterData(allData));
            }
        });
    });
}

// Create story filter select
function createStoryFilter(stories) {
    // Initialize Select2
    const select = $('#story-select');
    
    // Clear existing options except the first one (All Stories)
    select.find('option:not(:first)').remove();
    
    // Add story options
    stories.forEach(story => {
        select.append(new Option(story.name, story.name));
    });
    
    // Initialize Select2 with search
    select.select2({
        placeholder: 'Select stories to filter',
        allowClear: true,
        width: '100%',
        templateResult: formatStoryOption,
        templateSelection: formatStoryOption
    });
    
    // Handle selection changes
    select.on('change', function(e) {
        const selectedStories = $(this).val() || [];
        activeStories.clear();
        selectedStories.forEach(story => {
            if (story !== '') { // Skip the "All Stories" option
                activeStories.add(story);
            }
        });
        
        // Filter and redraw data
        const filteredData = activeStories.size === 0 ? 
            allData : 
            allData.filter(d => d.stories.some(storyName => activeStories.has(storyName)));
        
        drawVisualization(filteredData);
    });
}

// Create location filter select
function createLocationFilter(locations) {
    const select = $('#location-select');
    
    // Clear existing options except the first one (All Locations)
    select.find('option:not(:first)').remove();
    
    // Add location options
    locations.forEach(location => {
        select.append(new Option(location, location));
    });
    
    // Initialize Select2
    select.select2({
        placeholder: 'Select locations to filter',
        allowClear: true,
        width: '100%'
    });
    
    // Handle selection changes
    select.on('change', function(e) {
        const selectedLocations = $(this).val() || [];
        activeLocations.clear();
        selectedLocations.forEach(location => {
            if (location !== '') {
                activeLocations.add(location);
            }
        });
        
        drawVisualization(filterData(allData));
    });
}

// Format story options with colors
function formatStoryOption(story) {
    if (!story.id || story.id === '') {
        return story.text;
    }
    
    // Get story index for consistent coloring
    const storyIndex = allStories.indexOf(story.id);
    const color = config.storyColors[storyIndex % config.storyColors.length];
    
    return $('<span>')
        .text(story.text)
        .css({
            'border-left': `4px solid ${color}`,
            'padding-left': '8px'
        });
}

// Filter data based on active filters
function filterData(data) {
    return data.filter(d => {
        const matchesStories = activeStories.size === 0 || 
            d.stories.some(storyName => activeStories.has(storyName));
        const matchesLocations = activeLocations.size === 0 || 
            activeLocations.has(d.location);
        return matchesStories && matchesLocations;
    });
}

// Optimized function to calculate vertical offsets
function calculateVerticalOffsets(events, xScale) {
    const lanes = new Map(); // Store occupied lanes for each location
    
    // Sort events by start time to optimize lane assignment
    events.sort((a, b) => a.begins - b.begins);
    
    events.forEach(event => {
        if (!lanes.has(event.location)) {
            lanes.set(event.location, []);
        }
        
        const locationLanes = lanes.get(event.location);
        const eventStart = xScale(event.begins);
        const eventEnd = xScale(event.ends);
        
        // Find first available lane
        let laneIndex = 0;
        while (laneIndex < config.maxLanes) {
            if (!locationLanes[laneIndex]) {
                locationLanes[laneIndex] = [];
                break;
            }
            
            // Check if current lane has space
            const hasOverlap = locationLanes[laneIndex].some(([start, end]) => {
                return Math.max(start, eventStart) <= Math.min(end, eventEnd);
            });
            
            if (!hasOverlap) break;
            laneIndex++;
        }
        
        // If we've exceeded max lanes, put in last lane
        if (laneIndex >= config.maxLanes) {
            laneIndex = config.maxLanes - 1;
        }
        
        // Ensure lane array exists
        if (!locationLanes[laneIndex]) {
            locationLanes[laneIndex] = [];
        }
        
        // Add event to lane
        locationLanes[laneIndex].push([eventStart, eventEnd]);
        event.laneIndex = laneIndex;
    });
    
    return lanes;
}

// Create zoom behavior
const zoom = d3.zoom()
    .scaleExtent([1, 20])  // Min/max zoom level
    .translateExtent([[0, -Infinity], [width, Infinity]])  // Allow vertical panning
    .on("zoom", zoomed);

// Apply zoom behavior to SVG
svg.call(zoom);

// Zoom function
function zoomed(event) {
    // Combine the margin transform with the zoom transform
    const transform = event.transform;
    mainGroup.attr("transform", `translate(${transform.x + config.margin.left}, ${transform.y + config.margin.top}) scale(${transform.k})`);
    
    // Update axes
    if (xScale) {
        const newXScale = event.transform.rescaleX(xScale);
        xAxis.scale(newXScale);
        d3.select(".x-axis").call(xAxis);
    }
}

// Function to format tooltip content
function formatTooltip(d) {
    const years = d.begins === d.ends ? 
        `${Math.abs(d.begins)} ${d.begins < 0 ? 'BCE' : 'CE'}` :
        `${Math.abs(d.begins)} ${d.begins < 0 ? 'BCE' : 'CE'} - ${Math.abs(d.ends)} ${d.ends < 0 ? 'BCE' : 'CE'}`;
    
    const stories = d.stories.length > 0 ?
        `<br><br>Stories: ${d.stories.join(', ')}` :
        '';
    
    return `<strong>${d.name}</strong><br>
            ${years}<br>
            Location: ${d.location}
            ${d.details ? '<br><br>' + d.details : ''}
            ${stories}`;
}

// Function to draw visualization
function drawVisualization(data) {
    // Clear existing elements
    mainGroup.selectAll("*").remove();
    
    if (!data || data.length === 0) {
        document.getElementById("timeline").innerHTML = '<p>No data available to display.</p>';
        return;
    }
    
    // Create scales
    const timeExtent = d3.extent(data.flatMap(d => [d.begins, d.ends]));
    const currentYear = new Date().getFullYear();
    const timeBuffer = Math.abs(timeExtent[1] - timeExtent[0]) * 0.05; // Add 5% buffer
    
    // Use custom time range if set, otherwise use data extent
    const domainStart = timeRange.start !== null ? timeRange.start : timeExtent[0] - timeBuffer;
    const domainEnd = timeRange.end !== null ? timeRange.end : currentYear;
    
    xScale = d3.scaleLinear()
        .domain([domainStart, domainEnd])
        .range([0, width]);
    
    // Create y-scale for locations (swimlanes)
    const locations = [...new Set(data.map(d => d.location))];
    const yScale = d3.scaleBand()
        .domain(locations)
        .range([0, config.height])
        .padding(0.2);  // Increased padding between swimlanes
    
    // Calculate vertical offsets for events
    const verticalOffsets = calculateVerticalOffsets(data, xScale);
    
    // Add x-axis with BCE/CE formatting
    xAxis = d3.axisBottom(xScale)
        .tickFormat(d => `${Math.abs(d)} ${d < 0 ? 'BCE' : 'CE'}`);
    
    mainGroup.append("g")
        .attr("class", "x-axis axis")
        .attr("transform", `translate(0,${config.height})`)
        .call(xAxis);
    
    // Add y-axis (locations)
    const yAxis = d3.axisLeft(yScale);
    mainGroup.append("g")
        .attr("class", "y-axis axis")
        .call(yAxis);
    
    // Create a group for each location (swimlane)
    const swimlanes = mainGroup.selectAll(".swimlane")
        .data(locations)
        .enter()
        .append("g")
        .attr("class", "swimlane")
        .attr("transform", d => `translate(0,${yScale(d)})`);
    
    // Add swimlane background
    swimlanes.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", width)
        .attr("height", yScale.bandwidth())
        .attr("class", "swimlane-bg");
    
    // Draw story connection lines
    const storyLinesGroup = mainGroup.append("g")
        .attr("class", "story-lines")
        .attr("clip-path", "url(#clip)");
    
    // Only draw lines for active stories or all if none are active
    const activeStoriesArray = Array.from(activeStories);
    const storiesToDraw = activeStoriesArray.length > 0 ? activeStoriesArray : allStories;
    
    storiesToDraw.forEach(story => {
        const storyEvents = data.filter(d => d.stories.includes(story))
            .sort((a, b) => a.begins - b.begins);
        
        if (storyEvents.length > 1) {
            const line = d3.line()
                .x(d => xScale(d.begins) + (xScale(d.ends) - xScale(d.begins)) / 2)
                .y(d => {
                    const laneHeight = yScale.bandwidth() / config.maxLanes;
                    return yScale(d.location) + (d.laneIndex + 0.5) * laneHeight;
                })
                .curve(d3.curveMonotoneX);
            
            storyLinesGroup.append("path")
                .datum(storyEvents)
                .attr("class", "story-line")
                .attr("d", line)
                .style("stroke", config.storyColors[allStories.indexOf(story) % config.storyColors.length])
                .style("stroke-width", config.storyLineWidth)
                .style("opacity", config.storyLineOpacity);
        }
    });
    
    // Create event blocks with fixed lane height
    const laneHeight = yScale.bandwidth() / config.maxLanes;
    const events = mainGroup.selectAll(".event")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "event")
        .attr("transform", d => {
            const x = xScale(d.begins);
            const y = yScale(d.location) + d.laneIndex * laneHeight;
            return `translate(${x},${y})`;
        });
    
    // Add event rectangles
    const eventHeight = laneHeight * 0.8;  // Leave some vertical padding
    events.append("rect")
        .attr("class", "event-rect")
        .attr("x", 0)
        .attr("y", laneHeight * 0.1)  // Center in lane
        .attr("width", d => Math.max(2, xScale(d.ends) - xScale(d.begins)))
        .attr("height", eventHeight)
        .style("fill", d => config.colors[d.type]);  // Color based on type only
    
    // Add event labels
    events.append("text")
        .attr("class", "event-label")
        .attr("x", 0)
        .attr("y", laneHeight / 2)
        .attr("text-anchor", "end")
        .attr("transform", d => `rotate(-30, 0, ${laneHeight/2})`)
        .text(d => d.name)
        .style("opacity", 1);  // Initial opacity

    // Add interactivity
    events.on("mouseover", function(event, d) {
        if (!focusedEvent) {  // Only highlight on hover if no event is focused
            d3.select(this).select("rect")
                .style("opacity", 1);
            
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            
            tooltip.html(formatTooltip(d))
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
            
            // Highlight associated story lines
            storyLinesGroup.selectAll(".story-line")
                .style("opacity", path => {
                    const pathData = d3.select(path).datum();
                    return pathData.some(e => e.stories.some(s => 
                        d.stories.includes(s)
                    )) ? 1 : 0.1;
                })
                .style("stroke-width", path => {
                    const pathData = d3.select(path).datum();
                    return pathData.some(e => e.stories.some(s => 
                        d.stories.includes(s)
                    )) ? config.storyLineWidth * 2 : config.storyLineWidth;
                });
        }
    })
    .on("mouseout", function(event, d) {
        if (!focusedEvent) {  // Only reset on mouseout if no event is focused
            d3.select(this).select("rect")
                .style("opacity", 0.8);
            
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
            
            // Reset story lines
            storyLinesGroup.selectAll(".story-line")
                .style("opacity", config.storyLineOpacity)
                .style("stroke-width", config.storyLineWidth);
        }
    })
    .on("click", function(event, d) {
        event.stopPropagation();  // Prevent click from bubbling to SVG
        
        if (focusedEvent === d) {
            // If clicking the focused event, unfocus it
            focusedEvent = null;
            d3.selectAll(".event text")
                .transition()
                .duration(200)
                .style("opacity", 1);
        } else {
            // Focus this event
            focusedEvent = d;
            d3.selectAll(".event text")
                .transition()
                .duration(200)
                .style("opacity", 0.1);
            d3.select(this).select("text")
                .transition()
                .duration(200)
                .style("opacity", 1);
        }
    });

    // Add click handler to SVG to clear focus when clicking background
    svg.on("click", function() {
        if (focusedEvent) {
            focusedEvent = null;
            d3.selectAll(".event text")
                .transition()
                .duration(200)
                .style("opacity", 1);
        }
    });
    
    // Add zoom instructions
    svg.append("text")
        .attr("class", "zoom-instructions")
        .attr("x", 10)
        .attr("y", 20)
        .text("Use mouse wheel to zoom, drag to pan");
}

// Helper function to reset all filters
function resetFilters() {
    // Reset story select
    $('#story-select').val(null).trigger('change');
    activeStories.clear();
    
    // Reset location select
    $('#location-select').val(null).trigger('change');
    activeLocations.clear();
    
    // Reset date inputs
    const timeExtent = d3.extent(allData.flatMap(d => [d.begins, d.ends]));
    const startYear = Math.abs(timeExtent[0]);
    const endYear = new Date().getFullYear();
    
    document.getElementById('start-year').value = startYear;
    document.getElementById('start-era').value = timeExtent[0] < 0 ? 'BCE' : 'CE';
    document.getElementById('end-year').value = endYear;
    document.getElementById('end-era').value = 'CE';
    
    timeRange.start = null;
    timeRange.end = null;
    
    // Reset zoom transform
    svg.transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity);
        
    // Redraw visualization
    drawVisualization(allData);
}

// Load data from API
async function loadData() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/entries`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const text = await response.text();
        let entries;
        try {
            entries = JSON.parse(text);
        } catch (e) {
            console.error('Response text:', text);
            throw new Error('Failed to parse JSON response: ' + e.message);
        }
        
        // Get unique stories
        const stories = [...new Set(entries.flatMap(d => d.stories))].map(name => ({ name }));
        
        // Store data globally
        allData = entries;
        allStories = stories.map(s => s.name);
        
        // Create filters
        createStoryFilter(stories);
        createLocationFilter([...new Set(entries.map(d => d.location))]);
        initializeDateInputs(entries);
        
        // Add reset button handler
        document.getElementById('reset-filters').addEventListener('click', resetFilters);
        
        // Initial draw
        drawVisualization(entries);
    } catch (error) {
        console.error('Error loading data:', error);
        console.error('Full error details:', error.stack);
        document.getElementById("timeline").innerHTML = `<p style="color: red">Error loading data: ${error.message}</p>`;
    }
}

// Call the function to load and draw data
loadData();
