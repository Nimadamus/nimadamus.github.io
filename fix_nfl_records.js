// Updated conversion function to work with OLD sheet format: Date,,Pick,Line,Result,Units
function convertToMLBFormat(sheetData) {
    return sheetData.map(row => ({
        Date: row.Date || '',
        Sport: 'NFL',  // Hardcode sport since this is the NFL sheet
        Pick: row.Pick || '',  // Use Pick column directly
        Line: row.Line || '',  // Use Line column for odds
        Result: row.Result || '',
        Units: row.Units || ''  // Use Units directly (this is profit/loss in old format)
    }));
}

// Updated filter - NO filtering needed, all rows are NFL
async function loadDataFromSheets() {
    try {
        const response = await fetch(GOOGLE_SHEETS_CSV_URL);
        const csvData = await response.text();
        const sheetData = parseCSV(csvData);

        // NO FILTER - all rows in this sheet are NFL picks
        const mlbPicksData = convertToMLBFormat(sheetData);
        
        // Hide loading message
        document.getElementById('loading-message').style.display = 'none';
        
        // Process the data using the original logic
        processPicksData(mlbPicksData);
        
    } catch (error) {
        console.error('Error loading data from Google Sheets:', error);
        document.getElementById('loading-message').textContent = 'Error loading data. Please refresh the page.';
    }
}
