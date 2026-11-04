/**
 * Unified Google Apps Script Web App for:
 * 1. Live LayoutLMv3 Detailed Per-Seed & Model Comparison Tracker (Google Sheets)
 *    Mimics layout of: https://docs.google.com/spreadsheets/d/1WaGo752pyewFFXkSbrGjPCoZFmNrxisWTvO56RLz2Y8/edit
 * 2. Automated Public Sharing & Material Organization (Google Drive)
 * 
 * Instructions to Update Your Deployment:
 * 1. Open your Google Sheet (https://docs.google.com/spreadsheets/d/173WXkbMXDCEVs4pYBRNXGTHihOda18adbJRJ7RpFw7o/edit).
 * 2. Click "Extensions" > "Apps Script".
 * 3. Replace all code in the editor with this script.
 * 4. In the toolbar function dropdown, select "moveTrackerSheetToFolder" and click "Run" once to place this sheet in the folder!
 * 5. Click "Deploy" > "Manage deployments".
 * 6. Click the Edit (pencil) icon on your Active deployment.
 * 7. Under "Version", select "New version".
 * 8. Click "Deploy". (Your Web App URL remains unchanged!)
 */

/**
 * Moves the Tracker Spreadsheet itself into the dedicated 'Thesis - LayoutLMv3' Google Drive folder.
 */
function moveTrackerSheetToFolder() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetFile = DriveApp.getFileById(ss.getId());
  var folderName = "Thesis - LayoutLMv3";
  var folders = DriveApp.getFoldersByName(folderName);
  var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
  folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  
  var parents = sheetFile.getParents();
  var alreadyIn = false;
  while (parents.hasNext()) {
    if (parents.next().getId() === folder.getId()) {
      alreadyIn = true;
      break;
    }
  }
  
  if (!alreadyIn) {
    folder.addFile(sheetFile);
    Logger.log("Successfully placed sheet '" + ss.getName() + "' into folder '" + folderName + "'!");
  } else {
    Logger.log("Sheet is already in folder '" + folderName + "'.");
  }
  return folder.getUrl();
}

/**
 * One-time authorization trigger for Google Drive permission.
 */
function authorizeDrive() {
  var folder = DriveApp.createFolder("auth_test_drive");
  folder.setTrashed(true);
  Logger.log("Full Drive write authorization complete!");
}

function doPost(e) {
  try {
    var contents = e.postData.contents;
    var data = JSON.parse(contents);
    var props = PropertiesService.getScriptProperties();

    // ==========================================
    // ACTION: ORGANIZE / MOVE SHEET TO FOLDER
    // ==========================================
    if (data.action === "organize_folder" || data.action === "move_sheet") {
      var folderUrl = moveTrackerSheetToFolder();
      return ContentService.createTextOutput(JSON.stringify({
        status: "OK",
        folderUrl: folderUrl
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // ==========================================
    // ACTION 1: UPLOAD SHARED FILE TO GOOGLE DRIVE
    // ==========================================
    if (data.action === "upload_pdf" || data.action === "upload_file") {
      var filename = data.filename || "Document.pdf";
      var folderName = "Thesis - LayoutLMv3";
      
      var folders = DriveApp.getFoldersByName(folderName);
      var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
      folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      
      var existingFiles = folder.getFilesByName(filename);
      while (existingFiles.hasNext()) {
        existingFiles.next().setTrashed(true);
      }
      
      var rawBase64 = data.fileBase64 || data.pdfBase64 || data.base64;
      var bytes = Utilities.base64Decode(rawBase64);
      var mimeType = data.mimeType || "application/octet-stream";
      if (filename.toLowerCase().endsWith(".pdf")) {
        mimeType = "application/pdf";
      } else if (filename.toLowerCase().endsWith(".png")) {
        mimeType = "image/png";
      } else if (filename.toLowerCase().endsWith(".zip")) {
        mimeType = "application/zip";
      } else if (filename.toLowerCase().endsWith(".pptx")) {
        mimeType = "application/vnd.openxmlformats-officedocument.presentationml.presentation";
      }
      var blob = Utilities.newBlob(bytes, mimeType, filename);
      var file = folder.createFile(blob);
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      
      var fileUrl = file.getUrl();
      var folderUrl = folder.getUrl();
      
      if (data.language === "vi" || filename.indexOf("Vietnamese_Thesis") !== -1) {
        props.setProperty("VI_PDF_URL", fileUrl);
      } else if (data.language === "en" || filename.indexOf("English_Thesis") !== -1) {
        props.setProperty("EN_PDF_URL", fileUrl);
      }
      props.setProperty("FOLDER_URL", folderUrl);
      
      return ContentService.createTextOutput(JSON.stringify({
        status: "OK",
        fileUrl: fileUrl,
        folderUrl: folderUrl,
        filename: filename,
        language: data.language
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // ==========================================
    // ACTION 2: SYNC CITATIONS DASHBOARD TAB
    // ==========================================
    if (data.action === "sync_citations") {
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var tabName = "Citations Dashboard";
      var citSheet = ss.getSheetByName(tabName);
      if (!citSheet) {
        citSheet = ss.insertSheet(tabName);
      }
      citSheet.clear();
      
      var viUrl = props.getProperty("VI_PDF_URL") || "";
      var enUrl = props.getProperty("EN_PDF_URL") || "";
      var folderUrl = props.getProperty("FOLDER_URL") || "";

      citSheet.getRange(1, 1).setValue("Key Information Extraction (KIE) & LayoutLMv3 Research Citations Dashboard")
              .setFontSize(14).setFontWeight("bold").setFontColor("#1a73e8");
      citSheet.getRange(2, 1).setValue("Last Synced: " + (data.lastUpdated || new Date().toLocaleString()) + " | Supervisors: TS. Pham Thi Quynh Trang & PGS. TS. Le Duc Trong")
              .setFontSize(11).setFontStyle("italic").setFontColor("#5f6368");
      
      if (viUrl) {
        citSheet.getRange(2, 5).setFormula('=HYPERLINK("' + viUrl + '", "📄 Vietnamese Thesis PDF")').setFontWeight("bold");
      }
      if (enUrl) {
        citSheet.getRange(2, 6).setFormula('=HYPERLINK("' + enUrl + '", "📄 English Thesis PDF")').setFontWeight("bold");
      }
      if (folderUrl) {
        citSheet.getRange(2, 7).setFormula('=HYPERLINK("' + folderUrl + '", "📁 Drive Folder")').setFontWeight("bold");
      }
      
      var startRow = 4;
      var rows = data.rows;
      if (!rows || rows.length === 0) {
        return ContentService.createTextOutput("No citation rows received.");
      }
      
      var numRows = rows.length;
      var numCols = rows[0].length;
      var range = citSheet.getRange(startRow, 1, numRows, numCols);
      range.setValues(rows);
      
      var headerRange = citSheet.getRange(startRow, 1, 1, numCols);
      headerRange.setBackground("#1a365d")
                 .setFontColor("#ffffff")
                 .setFontWeight("bold")
                 .setFontSize(11)
                 .setHorizontalAlignment("center");
      
      var allDataRange = citSheet.getRange(startRow, 1, numRows, numCols);
      allDataRange.setBorder(true, true, true, true, true, true, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
      allDataRange.setFontSize(11);
      allDataRange.setWrap(true);
      citSheet.setFrozenRows(startRow);
      
      return ContentService.createTextOutput(JSON.stringify({
        status: "OK",
        tab: tabName,
        totalEntries: numRows - 1
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // ==========================================
    // ACTION 3: DETAILED PER-SEED QUAD-BLOCK TRACKER
    // ==========================================
    var rows = data.rows;
    if (!rows || !Array.isArray(rows) || rows.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "ERROR",
        message: "No rows received. Sheet was not cleared."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    sheet.clear();
    
    try {
      moveTrackerSheetToFolder();
    } catch (ignoreErr) {}
    
    var viUrl = props.getProperty("VI_PDF_URL") || "";
    var enUrl = props.getProperty("EN_PDF_URL") || "";
    var folderUrl = props.getProperty("FOLDER_URL") || "";
    
    // 1. Dashboard Title (Large, Clear 15pt font)
    sheet.getRange(1, 1).setValue("LayoutLMv3 Enhancement: Detailed Per-Seed & Model Comparison Report")
         .setFontSize(15).setFontWeight("bold").setFontColor("#1a365d");
    
    // 2. Subtitle & Direct Hyperlinks (11pt font)
    sheet.getRange(2, 1).setValue("Last Synced: " + (data.lastUpdated || new Date().toLocaleString()) + " | Hardware: NVIDIA A100-SXM4-80GB (Ampere TF32 + FP16)")
         .setFontSize(11).setFontStyle("italic").setFontColor("#5f6368");
         
    if (viUrl) {
      sheet.getRange(2, 6).setFormula('=HYPERLINK("' + viUrl + '", "📄 Vietnamese Thesis PDF")').setFontWeight("bold").setFontSize(11);
    }
    if (enUrl) {
      sheet.getRange(2, 10).setFormula('=HYPERLINK("' + enUrl + '", "📄 English Thesis PDF")').setFontWeight("bold").setFontSize(11);
    }
    if (folderUrl) {
      sheet.getRange(2, 14).setFormula('=HYPERLINK("' + folderUrl + '", "📁 Google Drive Folder")').setFontWeight("bold").setFontSize(11);
    }
         
    var startRow = 4;
    
    var numRows = rows.length;
    var numCols = rows[0].length;
    
    // 3. Write Data Matrix
    var dataRange = sheet.getRange(startRow, 1, numRows, numCols);
    dataRange.setValues(rows);
    dataRange.setFontSize(11).setVerticalAlignment("middle");
    
    // 4. Intelligent Styling (Enhanced Quad-Block layout matching reference sheet)
    // Block column start indices: Block 1 (col 1), Block 2 (col 8), Block 3 (col 16), Block 4 (col 24)
    // Separator columns: cols 6-7, 14-15, 22-23 (2 blank columns spacing)
    var blockStarts = [1, 8, 16, 24];
    var blockWidths = [5, 6, 6, 6];
    var deltaCols = [0, 13, 21, 29];

    for (var i = 0; i < numRows; i++) {
      var rowIdx = startRow + i;
      var c1 = (rows[i][0] || "").toString().trim();
      var c8 = (numCols >= 8) ? (rows[i][7] || "").toString().trim() : "";
      var c16 = (numCols >= 16) ? (rows[i][15] || "").toString().trim() : "";
      var c24 = (numCols >= 24) ? (rows[i][23] || "").toString().trim() : "";
      
      // Case A: Section Title Row (TABLE 1, SECTION, etc.)
      if (c1.indexOf("TABLE") === 0 || c1.indexOf("SECTION") === 0) {
        var secRange = sheet.getRange(rowIdx, 1, 1, numCols);
        secRange.merge()
                .setBackground("#e8f0fe")
                .setFontColor("#1967d2")
                .setFontWeight("bold")
                .setFontSize(14)
                .setHorizontalAlignment("left")
                .setVerticalAlignment("middle");
        sheet.setRowHeight(rowIdx, 38);
        continue;
      }
      
      // Case B: Model Configuration Titles Row (Much bigger font 16pt, bold)
      if (c1.indexOf("Baseline") !== -1 || c1.indexOf("OURS") !== -1 || c1.indexOf("w/o") !== -1 || c8.indexOf("w/o") !== -1 || c16.indexOf("OURS") !== -1) {
        sheet.setRowHeight(rowIdx, 36);
        
        // Block 1 Title (Cols 1-5)
        if (c1) {
          var b1Range = sheet.getRange(rowIdx, 1, 1, 5);
          b1Range.merge().setBackground("#f1f3f4").setFontColor("#1a365d").setFontWeight("bold").setFontSize(16).setHorizontalAlignment("center").setVerticalAlignment("middle");
          b1Range.setBorder(true, true, true, true, false, false, "#1a365d", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
        }
        // Block 2 Title (Cols 8-13)
        if (numCols >= 13 && c8) {
          var b2Range = sheet.getRange(rowIdx, 8, 1, 6);
          b2Range.merge().setBackground("#f3e8fd").setFontColor("#5b21b6").setFontWeight("bold").setFontSize(16).setHorizontalAlignment("center").setVerticalAlignment("middle");
          b2Range.setBorder(true, true, true, true, false, false, "#5b21b6", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
        }
        // Block 3 Title (Cols 16-21: OURS)
        if (numCols >= 21 && c16) {
          var b3Range = sheet.getRange(rowIdx, 16, 1, 6);
          b3Range.merge().setBackground("#e6f4ea").setFontColor("#137333").setFontWeight("bold").setFontSize(16).setHorizontalAlignment("center").setVerticalAlignment("middle");
          b3Range.setBorder(true, true, true, true, false, false, "#137333", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
        }
        // Block 4 Title (Cols 24-29)
        if (numCols >= 29 && c24) {
          var b4Range = sheet.getRange(rowIdx, 24, 1, 6);
          b4Range.merge().setBackground("#fef7e0").setFontColor("#b45f06").setFontWeight("bold").setFontSize(16).setHorizontalAlignment("center").setVerticalAlignment("middle");
          b4Range.setBorder(true, true, true, true, false, false, "#b45f06", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
        }
        continue;
      }
      
      // Case C: Column Header Row (Metric | Seed 42 | Seed 123 | Seed 1993 | Mean +/- STD | Delta F1)
      // Color 1: Deep steel blue #425D90 with white text, bold, medium bottom border
      if (c1 === "Metric") {
        sheet.setRowHeight(rowIdx, 32);
        for (var b = 0; b < 4; b++) {
          var sCol = blockStarts[b];
          var wCol = blockWidths[b];
          if (sCol + wCol - 1 <= numCols) {
            var colHdr = sheet.getRange(rowIdx, sCol, 1, wCol);
            colHdr.setBackground("#425D90")
                  .setFontColor("#ffffff")
                  .setFontWeight("bold")
                  .setFontSize(11)
                  .setHorizontalAlignment("center")
                  .setVerticalAlignment("middle");
            // Thick/Medium border between header and data cells below
            colHdr.setBorder(true, true, true, true, true, true, "#1a365d", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          }
        }
        continue;
      }
      
      // Case D: Blank separator row (at least 2 blank rows between sections)
      if (c1 === "" && c8 === "" && c16 === "") {
        sheet.setRowHeight(rowIdx, 16);
        // Clear borders in separator rows
        sheet.getRange(rowIdx, 1, 1, numCols).setBorder(false, false, false, false, false, false);
        continue;
      }
      
      // Case E: Data Row (eval_accuracy, eval_f1, eval_precision, eval_recall, eval_loss)
      sheet.setRowHeight(rowIdx, 28);
      
      // Format each of the 4 model blocks
      for (var b = 0; b < 4; b++) {
        var sCol = blockStarts[b];
        var wCol = blockWidths[b];
        if (sCol + wCol - 1 <= numCols) {
          // Row Header (Color 2: #e8edf5 with bold #1a365d text, medium right border)
          var metricCell = sheet.getRange(rowIdx, sCol);
          metricCell.setBackground("#e8edf5")
                    .setFontColor("#1a365d")
                    .setFontWeight("bold")
                    .setFontSize(10)
                    .setHorizontalAlignment("left")
                    .setVerticalAlignment("middle");
          metricCell.setBorder(true, true, true, true, false, false, "#1a365d", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          
          // Seed values (Cols sCol+1 .. sCol+3)
          var seedsRange = sheet.getRange(rowIdx, sCol + 1, 1, 3);
          seedsRange.setHorizontalAlignment("center").setFontSize(10.5).setFontColor("#202124");
          seedsRange.setBorder(true, true, true, true, true, true, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
          
          // Mean +/- STD (Col sCol+4)
          var msCell = sheet.getRange(rowIdx, sCol + 4);
          msCell.setHorizontalAlignment("center").setFontWeight("bold").setFontSize(10.5);
          msCell.setBorder(true, true, true, true, false, false, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
          
          // OURS block subtle background tint
          if (b === 2) {
            sheet.getRange(rowIdx, sCol + 1, 1, 4).setBackground("#f6fbf7");
          }
          
          // Outer border for data row in this block
          sheet.getRange(rowIdx, sCol, 1, wCol).setBorder(true, true, true, true, false, false, "#1a365d", SpreadsheetApp.BorderStyle.SOLID);
        }
      }
      
      // Delta F1 cells (Cols 13, 21, 29)
      for (var d = 1; d < 4; d++) {
        var dCol = deltaCols[d];
        if (numCols >= dCol) {
          var val = (rows[i][dCol - 1] || "").toString().trim();
          var dCell = sheet.getRange(rowIdx, dCol);
          if (val && val !== "--") {
            dCell.setFontColor("#137333")
                 .setFontWeight("bold")
                 .setBackground("#edf7ed")
                 .setHorizontalAlignment("center")
                 .setVerticalAlignment("middle")
                 .setFontSize(11);
            dCell.setBorder(true, true, true, true, false, false, "#137333", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          } else {
            dCell.setHorizontalAlignment("center").setFontColor("#5f6368");
            dCell.setBorder(true, true, true, true, false, false, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
          }
        }
      }
    }
    
    // 5. Clean up Separator Columns & Adjust Widths
    // Separator columns: 6, 7, 14, 15, 22, 23
    var sepCols = [6, 7, 14, 15, 22, 23];
    for (var s = 0; s < sepCols.length; s++) {
      var sc = sepCols[s];
      if (sc <= numCols) {
        sheet.setColumnWidth(sc, 24); // Narrow spacing columns
        sheet.getRange(startRow, sc, numRows, 1).setBorder(false, false, false, false, false, false);
      }
    }
    
    for (var c = 1; c <= numCols; c++) {
      if (sepCols.indexOf(c) !== -1) continue;
      sheet.autoResizeColumn(c);
      var curW = sheet.getColumnWidth(c);
      if (c === 1 || c === 8 || c === 16 || c === 24) { // Metric row header column
        sheet.setColumnWidth(c, Math.max(curW, 115));
      } else if (c === 13 || c === 21 || c === 29) { // Delta F1 column
        sheet.setColumnWidth(c, Math.max(curW, 95));
      } else if (c === 5 || c === 12 || c === 20 || c === 28) { // Mean +/- STD column
        sheet.setColumnWidth(c, Math.max(curW, 135));
      } else { // Seed columns
        sheet.setColumnWidth(c, Math.max(curW, 85));
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({ status: "OK", updatedRows: numRows, cols: numCols }))
                         .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput("Google Sheets & Drive Webhook is Active. Ready for POST requests.");
}

