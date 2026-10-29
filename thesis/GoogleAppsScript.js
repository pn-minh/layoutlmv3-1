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
    
    // 4. Intelligent Styling
    for (var i = 0; i < numRows; i++) {
      var rowIdx = startRow + i;
      var c1 = (rows[i][0] || "").toString().trim();
      var c7 = (numCols >= 7) ? (rows[i][6] || "").toString().trim() : "";
      var c13 = (numCols >= 13) ? (rows[i][12] || "").toString().trim() : "";
      var c19 = (numCols >= 19) ? (rows[i][18] || "").toString().trim() : "";
      
      // Case A: Section Title Row (TABLE 1, SECTION, etc.)
      if (c1.indexOf("TABLE") === 0 || c1.indexOf("SECTION") === 0) {
        var secRange = sheet.getRange(rowIdx, 1, 1, numCols);
        secRange.merge()
                .setBackground("#e8f0fe")
                .setFontColor("#1967d2")
                .setFontWeight("bold")
                .setFontSize(12)
                .setHorizontalAlignment("left")
                .setVerticalAlignment("middle");
        sheet.setRowHeight(rowIdx, 36);
        continue;
      }
      
      // Case B: Model Quad Titles Row (e.g. Layoutlmv3 goc, OURS, etc.)
      if (c1.indexOf("Layoutlmv3") !== -1 || c1.indexOf("OURS") !== -1 || c7.indexOf("Segment") !== -1 || c13.indexOf("OURS") !== -1) {
        sheet.setRowHeight(rowIdx, 32);
        
        // Block 1 Title (Cols 1-5)
        if (c1) {
          var b1Range = sheet.getRange(rowIdx, 1, 1, 5);
          b1Range.merge().setBackground("#f1f3f4").setFontColor("#202124").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
        }
        // Block 2 Title (Cols 7-11)
        if (numCols >= 11 && c7) {
          var b2Range = sheet.getRange(rowIdx, 7, 1, 5);
          b2Range.merge().setBackground("#f3e8fd").setFontColor("#5b21b6").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
        }
        // Block 3 Title (Cols 13-17: OURS)
        if (numCols >= 17 && c13) {
          var b3Range = sheet.getRange(rowIdx, 13, 1, 5);
          b3Range.merge().setBackground("#e6f4ea").setFontColor("#137333").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
        }
        // Block 4 Title (Cols 19-23)
        if (numCols >= 23 && c19) {
          var b4Range = sheet.getRange(rowIdx, 19, 1, 5);
          b4Range.merge().setBackground("#fef7e0").setFontColor("#b45f06").setFontWeight("bold").setFontSize(11).setHorizontalAlignment("center");
        }
        continue;
      }
      
      // Case C: Metric Header Row (Metric | Seed 42 | Seed 123 | Seed 1993 | Mean +/- STD)
      if (c1 === "Metric") {
        sheet.setRowHeight(rowIdx, 30);
        for (var b = 0; b < 4; b++) {
          var startC = 1 + b * 6;
          if (startC + 4 <= numCols) {
            sheet.getRange(rowIdx, startC, 1, 5)
                 .setBackground("#1a365d")
                 .setFontColor("#ffffff")
                 .setFontWeight("bold")
                 .setFontSize(10)
                 .setHorizontalAlignment("center");
          }
        }
        // Delta headers (Cols 12, 18)
        if (numCols >= 12) {
          sheet.getRange(rowIdx, 12).setBackground("#1a365d").setFontColor("#ffffff").setFontWeight("bold").setFontSize(10).setHorizontalAlignment("center");
        }
        if (numCols >= 18) {
          sheet.getRange(rowIdx, 18).setBackground("#1a365d").setFontColor("#ffffff").setFontWeight("bold").setFontSize(10).setHorizontalAlignment("center");
        }
        continue;
      }
      
      // Case D: Blank separator row
      if (c1 === "" && c7 === "" && c13 === "") {
        sheet.setRowHeight(rowIdx, 16);
        continue;
      }
      
      // Case E: Data Row (eval_accuracy, eval_f1, eval_precision, eval_recall, eval_loss)
      sheet.setRowHeight(rowIdx, 27);
      
      // Format each of the 4 model blocks
      for (var b = 0; b < 4; b++) {
        var startC = 1 + b * 6;
        if (startC + 4 <= numCols) {
          // Metric name
          sheet.getRange(rowIdx, startC).setHorizontalAlignment("left").setFontWeight("bold");
          // Seeds 42, 123, 1993
          sheet.getRange(rowIdx, startC + 1, 1, 3).setHorizontalAlignment("center");
          // Mean +/- STD
          sheet.getRange(rowIdx, startC + 4).setHorizontalAlignment("center").setFontWeight("bold");
          
          // OURS block subtle background
          if (b === 2) {
            sheet.getRange(rowIdx, startC, 1, 5).setBackground("#f6fbf7");
          }
        }
      }
      
      // Delta F1 cells (Col 12 and Col 18)
      if (numCols >= 12) {
        var d12 = (rows[i][11] || "").toString().trim();
        if (d12) {
          sheet.getRange(rowIdx, 12)
               .setFontColor("#137333").setFontWeight("bold").setBackground("#edf7ed").setHorizontalAlignment("center");
        }
      }
      if (numCols >= 18) {
        var d18 = (rows[i][17] || "").toString().trim();
        if (d18) {
          sheet.getRange(rowIdx, 18)
               .setFontColor("#137333").setFontWeight("bold").setBackground("#edf7ed").setHorizontalAlignment("center");
        }
      }
    }
    
    // 5. Borders & Column Widths
    sheet.getRange(startRow, 1, numRows, numCols).setBorder(true, true, true, true, true, true, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
    
    for (var c = 1; c <= numCols; c++) {
      sheet.autoResizeColumn(c);
      var curW = sheet.getColumnWidth(c);
      if (c === 6 || c === 12 || c === 18) {
        sheet.setColumnWidth(c, Math.max(curW, 80));
      } else if (c % 6 === 1) { // Metric column
        sheet.setColumnWidth(c, Math.max(curW, 110));
      } else {
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

