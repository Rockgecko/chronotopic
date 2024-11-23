# Chronotopic Frontend

A dynamic historical timeline visualization built with D3.js that displays historical events across different locations and connects related stories.

## Features

### Timeline Visualization

- **Location-based Swimlanes**: Events are organized in horizontal lanes by location
- **Event Blocks**:
  - Color-coded by story
  - Automatically stacked when overlapping (max 3 layers)
  - Shows event name, dates, and location
  - Hover for detailed information

### Story Connections

- **Story Lines**: Connecting lines between related events
- **Dynamic Filtering**: Toggle story visibility with filter buttons
- **Interactive Highlighting**:
  - Hover over events to highlight related story connections
  - Other story lines fade to help focus attention

### Navigation

- **Zoom**: Use mouse wheel to zoom in/out (1x to 20x)
- **Pan**: Click and drag to move around the timeline
- **Time Scale**: Supports both BCE and CE dates
- **Responsive**: Adapts to window size

### Visual Design

- **Event Layout**:
  - Automatic vertical stacking for overlapping events
  - Maximum 3 lanes per location to prevent overcrowding
  - Rotated labels for better readability in narrow events
- **Color Scheme**:
  - Alternating swimlane backgrounds
  - Story-based event colors
  - Configurable opacity and line widths

## Running the Frontend

1. Ensure the backend server is running first:

   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

2. Serve the frontend files:

   ```bash
   cd ../frontend
   python -m http.server 8080
   ```

3. Open in browser:

   ```bash
   http://localhost:8080
   ```

## Project Structure

```bash
frontend/
├── index.html      # Main HTML file
├── app.js          # Core visualization logic
└── styles.css      # Styling and layout
```

### Key Components

#### HTML (index.html)

- Basic structure with timeline container
- D3.js library import
- Debug div for development

#### JavaScript (app.js)

- `config`: Visualization settings and parameters
- `calculateVerticalOffsets()`: Event layout algorithm
- `drawVisualization()`: Main rendering function
- `loadData()`: API data fetching
- Event handlers for interactivity

#### CSS (styles.css)

- Timeline container styling
- Event and story line appearance
- Swimlane backgrounds
- Interactive elements (hover states, tooltips)

## Configuration

Key settings in `config` object:

```javascript
{
    height: 600,            // Visualization height
    maxLanes: 3,           // Max vertical stacking
    storyLineOpacity: 0.7, // Story connection opacity
    storyLineWidth: 3      // Story connection width
}
```

## API Integration

Connects to backend at `http://localhost:8000/api/entries` expecting data in format:

```javascript
{
    type: "event",
    name: "Event Name",
    begins: number,  // BCE (negative) / CE (positive)
    ends: number,
    location: string,
    details: string,
    stories: [{ name: string }]
}
```

## Browser Support

- Tested on modern browsers (Chrome, Firefox, Safari)
- Requires JavaScript enabled
- Uses D3.js v7

## Development Notes

### Known Limitations

- Maximum 3 overlapping events per location
- Text may be cut off in very narrow event blocks
- Large datasets may affect performance

### Future Improvements

- Advanced filtering options
- Custom color schemes
- Timeline annotations
- Export/save functionality
- Performance optimizations for large datasets
