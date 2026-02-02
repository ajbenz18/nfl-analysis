
// get the data
const tableBody = $0;
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    const extractedData = rows.map(row => {
      const cells = Array.from(row.querySelectorAll('td'));
      return cells.map(cell => cell.textContent.trim());
    });
    const data = { tableData: extractedData };


// save the data
const dataToSave = JSON.stringify(tableData, null, 2); // 'tableData' is the variable from your previous extraction
    const blob = new Blob([dataToSave], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chart_data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // get column headers
    const tableHead = $0.parentElement.querySelector('thead');
    const headerCells = Array.from(tableHead.querySelectorAll('th'));
    const columnHeaders = headerCells.map(cell => cell.textContent.trim());
    const data = { columnHeaders: columnHeaders };