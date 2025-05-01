# Timezone Comparator

A web application to compare timezones and analyze timezone data from CSV files.

## Features
- Select a base timezone from a dropdown or enter manually to see time differences with common timezones.
- Optionally input a specific time for the base timezone (defaults to current time if not specified).
- Upload a CSV file containing a list of timezones to analyze unique entries, their frequency, and time differences from the selected base timezone.
- Automatically detects a column starting with 'Timezones' in the CSV (case-insensitive).
- Displays timezone abbreviations (e.g., PST, CET) for better readability.

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd TimezoneComparator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://127.0.0.1:5000/`.

## Usage

- **Compare Timezones**: Choose a base timezone from the dropdown or type it manually. Optionally, set a specific time. Click "Compare with Common Timezones" to see the differences and current times in other zones.
- **Upload CSV**: Drag and drop a CSV file with a column named starting with 'Timezones' or click to upload. Click "Analyze CSV" to see unique timezones, their counts, and time differences from your selected base timezone.

## CSV Format

The CSV file can have any structure, but it must contain a column with a header starting with 'Timezones' (case-insensitive). The app will scan the first row to find this column and process the data accordingly.

Example:
```csv
Name,Timezones,City
John,US/Pacific,Los Angeles
Jane,Europe/Paris,Paris
```

## License

MIT License - feel free to use and modify this code as needed.
