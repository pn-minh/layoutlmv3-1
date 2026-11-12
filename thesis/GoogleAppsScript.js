/**
 * Unified Google Apps Script Web App for:
 * 1. Live LayoutLMv3 Detailed Per-Seed & Model Comparison Tracker (Google Sheets)
 *    Supports creating a new sheet tab ("Additional Experiments & Calibrated Tracker")
 *    by copying the exact 6-Table Horizontal Layout format of the previous sheet!
 * 2. Automated Google Drive Folder Organization & Cleanup ("Thesis - LayoutLMv3")
 *    Keeps only:
 *      - English_Thesis_LayoutLMv3.pdf
 *      - Weekly Presentation Slides (including Final Thesis Defense Slides)
 *      - Model_Architecture_Diagram.drawio & Model_Architecture_Diagram.pdf
 *      - Thesis Changelog Google Doc (tracking both Local & Overleaf supervisor changes)
 *      - "Experiments & Logs" subfolder (storing all GPU logs, JSON metrics, and archives)
 *
 * Instructions to Update Your Deployment (takes 20 seconds):
 * 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/173WXkbMXDCEVs4pYBRNXGTHihOda18adbJRJ7RpFw7o/edit
 * 2. Click "Extensions" > "Apps Script".
 * 3. Replace all code in the editor with this script and press Ctrl+S.
 * 4. Click "Deploy" > "Manage deployments" > Edit (pencil icon) > Version: "New version" > "Deploy".
 */

var ROOT_FOLDER_NAME = "Thesis - LayoutLMv3";
var LOGS_SUBFOLDER_NAME = "Experiments & Logs";
var CHANGELOG_DOC_NAME = "Thesis Changelog (Local & Overleaf Revisions)";

function getOrCreateRootFolder() {
  var folders = DriveApp.getFoldersByName(ROOT_FOLDER_NAME);
  var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(ROOT_FOLDER_NAME);
  folder.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return folder;
}

function getOrCreateSubfolder(parentFolder, subName) {
  var subs = parentFolder.getFoldersByName(subName);
  var sub = subs.hasNext() ? subs.next() : parentFolder.createFolder(subName);
  sub.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return sub;
}

function moveTrackerSheetToFolder() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetFile = DriveApp.getFileById(ss.getId());
  var folder = getOrCreateRootFolder();

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
  }
  return folder.getUrl();
}

function authorizeDrive() {
  var folder = DriveApp.createFolder("auth_test_drive");
  folder.setTrashed(true);
  var doc = DocumentApp.create("auth_test_doc");
  DriveApp.getFileById(doc.getId()).setTrashed(true);
  Logger.log("Full Drive + DocumentApp write authorization complete!");
}

/**
 * Cleans up the 'Thesis - LayoutLMv3' Google Drive folder so the root folder contains ONLY:
 * 1. English_Thesis_LayoutLMv3.pdf
 * 2. Weekly presentation slides (including final defense slides)
 * 3. Model_Architecture_Diagram.drawio & Model_Architecture_Diagram.pdf
 * 4. Thesis Changelog Google Doc
 * 5. Live Tracker Google Sheet & 'Experiments & Logs' subfolder
 */
function cleanupThesisDriveFolder() {
  var rootFolder = getOrCreateRootFolder();
  var logsFolder = getOrCreateSubfolder(rootFolder, LOGS_SUBFOLDER_NAME);

  var keepExactNames = [
    "English_Thesis_LayoutLMv3.pdf",
    "Model_Architecture_Diagram.drawio",
    "Model_Architecture_Diagram.pdf",
    CHANGELOG_DOC_NAME
  ];

  var movedToLogs = [];
  var trashedFiles = [];
  var keptFiles = [];

  var files = rootFolder.getFiles();
  while (files.hasNext()) {
    var f = files.next();
    var name = f.getName();
    var lower = name.toLowerCase();
    var mime = f.getMimeType();

    // Always keep Google Sheets (Tracker), Google Docs (Changelog), and Google Slides (Weekly/Defense presentations)
    if (
      mime === MimeType.GOOGLE_SHEETS ||
      mime === MimeType.GOOGLE_DOCS ||
      mime === MimeType.GOOGLE_SLIDES
    ) {
      keptFiles.push(name);
      continue;
    }

    // Keep exact whitelisted thesis PDF & model architecture diagram (.drawio + .pdf)
    if (keepExactNames.indexOf(name) !== -1) {
      keptFiles.push(name);
      continue;
    }

    // Keep weekly / defense presentation slides (.pptx or .pdf with Slide/Presentation/Defense/Weekly in name)
    if (
      (lower.indexOf("slide") !== -1 ||
        lower.indexOf("presentation") !== -1 ||
        lower.indexOf("defense") !== -1 ||
        lower.indexOf("defence") !== -1 ||
        lower.indexOf("weekly") !== -1) &&
      (lower.endsWith(".pdf") || lower.endsWith(".pptx"))
    ) {
      keptFiles.push(name);
      continue;
    }

    // Move experiment logs, JSON summaries, snapshots, CSVs, and result archives into 'Experiments & Logs'
    if (
      lower.endsWith(".json") ||
      lower.endsWith(".log") ||
      lower.endsWith(".csv") ||
      lower.indexOf("experiment") !== -1 ||
      lower.indexOf("summary") !== -1 ||
      lower.indexOf("ablation") !== -1 ||
      lower.indexOf("snapshot") !== -1
    ) {
      logsFolder.addFile(f);
      rootFolder.removeFile(f);
      movedToLogs.push(name);
      continue;
    }

    // Trash redundant PNGs, old Vietnamese PDF, raw .tex files, or old zip files from root folder
    f.setTrashed(true);
    trashedFiles.push(name);
  }

  return {
    status: "OK",
    folderUrl: rootFolder.getUrl(),
    logsFolderUrl: logsFolder.getUrl(),
    keptFiles: keptFiles,
    movedToLogs: movedToLogs,
    trashedFiles: trashedFiles
  };
}

/**
 * Creates or updates the Google Doc documenting changelogs to the thesis PDF
 * from both local changes and Overleaf collaborator/supervisor changes.
 */
function syncChangelogGoogleDoc(changelogEntries, fullTextOverride) {
  var rootFolder = getOrCreateRootFolder();
  var props = PropertiesService.getScriptProperties();
  var docId = props.getProperty("CHANGELOG_DOC_ID");
  var doc = null;

  if (docId) {
    try {
      doc = DocumentApp.openById(docId);
    } catch (e) {
      doc = null;
    }
  }

  if (!doc) {
    var existing = rootFolder.getFilesByName(CHANGELOG_DOC_NAME);
    while (existing.hasNext()) {
      var candidate = existing.next();
      if (candidate.getMimeType() === MimeType.GOOGLE_DOCS) {
        doc = DocumentApp.openById(candidate.getId());
        break;
      }
    }
  }

  if (!doc) {
    doc = DocumentApp.create(CHANGELOG_DOC_NAME);
    var docFile = DriveApp.getFileById(doc.getId());
    rootFolder.addFile(docFile);
    docFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    props.setProperty("CHANGELOG_DOC_ID", doc.getId());
  }

  var body = doc.getBody();
  body.clear();

  var title = body.appendParagraph("English Thesis PDF — Master Changelog (Local & Overleaf Revisions)");
  title.setHeading(DocumentApp.ParagraphHeading.HEADING1);

  var meta = body.appendParagraph(
    "Last Updated: " + new Date().toLocaleString() +
    "\nOverleaf Project: https://www.overleaf.com/project/6aeeb45d264c70bbb1215bc4" +
    "\nGoogle Drive Folder: " + rootFolder.getUrl()
  );
  meta.setItalic(true);

  body.appendHorizontalRule();

  if (fullTextOverride) {
    var lines = fullTextOverride.split("\n");
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (ln.indexOf("## ") === 0) {
        body.appendParagraph(ln.substring(3)).setHeading(DocumentApp.ParagraphHeading.HEADING2);
      } else if (ln.indexOf("### ") === 0) {
        body.appendParagraph(ln.substring(4)).setHeading(DocumentApp.ParagraphHeading.HEADING3);
      } else if (ln.indexOf("- ") === 0) {
        body.appendListItem(ln.substring(2)).setGlyphType(DocumentApp.GlyphType.BULLET);
      } else if (ln.trim() !== "") {
        body.appendParagraph(ln);
      }
    }
  } else if (changelogEntries && Array.isArray(changelogEntries)) {
    for (var j = 0; j < changelogEntries.length; j++) {
      var entry = changelogEntries[j];
      var h = body.appendParagraph("[" + (entry.date || "") + "] " + (entry.source || "LOCAL") + " — " + (entry.title || ""));
      h.setHeading(DocumentApp.ParagraphHeading.HEADING2);
      var items = entry.items || [];
      for (var k = 0; k < items.length; k++) {
        body.appendListItem(items[k]).setGlyphType(DocumentApp.GlyphType.BULLET);
      }
    }
  }

  doc.saveAndClose();
  return {
    status: "OK",
    docUrl: doc.getUrl(),
    docId: doc.getId()
  };
}

function doPost(e) {
  try {
    var contents = e.postData.contents;
    var data = JSON.parse(contents);
    var props = PropertiesService.getScriptProperties();

    // ==========================================
    // ACTION: ORGANIZE / CLEANUP DRIVE FOLDER
    // ==========================================
    if (data.action === "cleanup_drive_folder") {
      var cleanRes = cleanupThesisDriveFolder();
      return ContentService.createTextOutput(JSON.stringify(cleanRes))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    if (data.action === "sync_changelog_doc") {
      var docRes = syncChangelogGoogleDoc(data.entries, data.markdown);
      return ContentService.createTextOutput(JSON.stringify(docRes))
                           .setMimeType(ContentService.MimeType.JSON);
    }

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
      var rootFolder = getOrCreateRootFolder();
      var targetFolder = rootFolder;

      // Route experiment logs, JSONs, and archives into 'Experiments & Logs' subfolder automatically
      var lowerName = filename.toLowerCase();
      var isExperimentArtifact = (
        data.subfolder ||
        lowerName.endsWith(".json") ||
        lowerName.endsWith(".log") ||
        (lowerName.endsWith(".zip") && lowerName.indexOf("experiment") !== -1) ||
        lowerName.indexOf("ablation") !== -1 ||
        lowerName.indexOf("snapshot") !== -1
      );
      if (isExperimentArtifact) {
        var subName = data.subfolder || LOGS_SUBFOLDER_NAME;
        targetFolder = getOrCreateSubfolder(rootFolder, subName);
      }

      var existingFiles = targetFolder.getFilesByName(filename);
      while (existingFiles.hasNext()) {
        existingFiles.next().setTrashed(true);
      }

      var rawBase64 = data.fileBase64 || data.pdfBase64 || data.base64;
      var bytes = Utilities.base64Decode(rawBase64);
      var mimeType = data.mimeType || "application/octet-stream";
      if (lowerName.endsWith(".pdf")) {
        mimeType = "application/pdf";
      } else if (lowerName.endsWith(".png")) {
        mimeType = "image/png";
      } else if (lowerName.endsWith(".zip")) {
        mimeType = "application/zip";
      } else if (lowerName.endsWith(".pptx")) {
        mimeType = "application/vnd.openxmlformats-officedocument.presentationml.presentation";
      } else if (lowerName.endsWith(".drawio") || lowerName.endsWith(".xml")) {
        mimeType = "application/xml";
      }
      var blob = Utilities.newBlob(bytes, mimeType, filename);
      var file = targetFolder.createFile(blob);
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

      var fileUrl = file.getUrl();
      var folderUrl = rootFolder.getUrl();

      if (data.language === "en" || filename.indexOf("English_Thesis") !== -1) {
        props.setProperty("EN_PDF_URL", fileUrl);
      }
      props.setProperty("FOLDER_URL", folderUrl);

      return ContentService.createTextOutput(JSON.stringify({
        status: "OK",
        fileUrl: fileUrl,
        folderUrl: folderUrl,
        targetFolder: targetFolder.getName(),
        filename: filename
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

      var enUrl = props.getProperty("EN_PDF_URL") || "";
      var folderUrl = props.getProperty("FOLDER_URL") || "";

      citSheet.getRange(1, 1).setValue("Key Information Extraction (KIE) & LayoutLMv3 Research Citations Dashboard")
              .setFontSize(14).setFontWeight("bold").setFontColor("#1a73e8");
      citSheet.getRange(2, 1).setValue("Last Synced: " + (data.lastUpdated || new Date().toLocaleString()))
              .setFontSize(11).setFontStyle("italic").setFontColor("#5f6368");

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
    // ACTION 3: DETAILED PER-SEED 6-TABLE TRACKER (SUPPORTS NEW SHEET TAB!)
    // ==========================================
    var rows = data.rows;
    if (!rows || !Array.isArray(rows) || rows.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "ERROR",
        message: "No rows received. Sheet was not cleared."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var targetSheetName = data.sheetName || data.tabName || "";
    var sheet = null;

    if (targetSheetName) {
      sheet = ss.getSheetByName(targetSheetName);
      if (!sheet) {
        // Copy the previous sheet tab so all base formatting, gridlines, and column settings carry over
        var baseSheet = ss.getSheets()[0];
        sheet = baseSheet.copyTo(ss).setName(targetSheetName);
      }
    } else {
      sheet = ss.getSheets()[0];
    }

    sheet.clear();

    try {
      moveTrackerSheetToFolder();
    } catch (ignoreErr) {}

    var enUrl = props.getProperty("EN_PDF_URL") || "";
    var folderUrl = props.getProperty("FOLDER_URL") || "";

    var titleText = data.title || "LayoutLMv3 Enhancement: Detailed Per-Seed & Model Comparison Report";
    sheet.getRange(1, 1).setValue(titleText)
         .setFontSize(15).setFontWeight("bold").setFontColor("#1a365d");

    sheet.getRange(2, 1).setValue("Last Synced: " + (data.lastUpdated || new Date().toLocaleString()) + " | Hardware: Dual NVIDIA A100-SXM4-80GB (Ampere TF32 + FP16)")
         .setFontSize(11).setFontStyle("italic").setFontColor("#5f6368");

    if (enUrl) {
      sheet.getRange(2, 10).setFormula('=HYPERLINK("' + enUrl + '", "📄 English Thesis PDF")').setFontWeight("bold").setFontSize(11);
    }
    if (folderUrl) {
      sheet.getRange(2, 14).setFormula('=HYPERLINK("' + folderUrl + '", "📁 Google Drive Folder")').setFontWeight("bold").setFontSize(11);
    }

    var startRow = 4;
    var numRows = rows.length;
    var numCols = rows[0].length;

    var dataRange = sheet.getRange(startRow, 1, numRows, numCols);
    dataRange.setValues(rows);
    dataRange.setFontSize(11).setVerticalAlignment("middle");

    var blockStarts = [1, 8, 16, 25, 34, 43];
    var blockWidths = [5, 6, 7, 7, 7, 7];
    var deltaCols = [13, 21, 22, 30, 31, 39, 40, 48, 49];
    var sepCols = [6, 7, 14, 15, 23, 24, 32, 33, 41, 42];
    var msCols = [5, 12, 20, 29, 38, 47];

    for (var i = 0; i < numRows; i++) {
      var rowIdx = startRow + i;
      var c1 = (rows[i][0] || "").toString().trim();
      var c8 = (numCols >= 8) ? (rows[i][7] || "").toString().trim() : "";
      var c16 = (numCols >= 16) ? (rows[i][15] || "").toString().trim() : "";

      if (c1.indexOf("TABLE") === 0 || c1.indexOf("SECTION") === 0 || c1.indexOf("PART") === 0) {
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

      if (
        c1.indexOf("Baseline") !== -1 ||
        c8.indexOf("HPE") !== -1 ||
        c16.indexOf("w/o") !== -1 ||
        c1.indexOf("Sensitivity") !== -1 ||
        c1.indexOf("Few-Shot") !== -1
      ) {
        sheet.setRowHeight(rowIdx, 36);
        var titleBgs = ["#f1f3f4", "#e6f4ea", "#f3e8fd", "#e8f0fe", "#fef7e0", "#fce8e6"];
        var titleColors = ["#1a365d", "#137333", "#5b21b6", "#1967d2", "#b45f06", "#c5221f"];
        for (var b = 0; b < blockStarts.length; b++) {
          var sCol = blockStarts[b];
          var wCol = blockWidths[b];
          if (sCol + wCol - 1 <= numCols && (rows[i][sCol - 1] || "").toString().trim() !== "") {
            var bRange = sheet.getRange(rowIdx, sCol, 1, wCol);
            bRange.merge()
                  .setBackground(titleBgs[b])
                  .setFontColor(titleColors[b])
                  .setFontWeight("bold")
                  .setFontSize(16)
                  .setHorizontalAlignment("center")
                  .setVerticalAlignment("middle");
            bRange.setBorder(true, true, true, true, false, false, titleColors[b], SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          }
        }
        continue;
      }

      if (c1 === "Metric") {
        sheet.setRowHeight(rowIdx, 38);
        for (var b = 0; b < blockStarts.length; b++) {
          var sCol = blockStarts[b];
          var wCol = blockWidths[b];
          if (sCol + wCol - 1 <= numCols && (rows[i][sCol - 1] || "").toString().trim() !== "") {
            var colHdr = sheet.getRange(rowIdx, sCol, 1, wCol);
            colHdr.setBackground("#425D90")
                  .setFontColor("#ffffff")
                  .setFontWeight("bold")
                  .setFontSize(10.5)
                  .setWrap(true)
                  .setHorizontalAlignment("center")
                  .setVerticalAlignment("middle");
            colHdr.setBorder(true, true, true, true, true, true, "#1a365d", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          }
        }
        continue;
      }

      if (c1 === "" && c8 === "" && c16 === "") {
        sheet.setRowHeight(rowIdx, 16);
        sheet.getRange(rowIdx, 1, 1, numCols).setBorder(false, false, false, false, false, false);
        continue;
      }

      sheet.setRowHeight(rowIdx, 28);

      for (var b = 0; b < blockStarts.length; b++) {
        var sCol = blockStarts[b];
        var wCol = blockWidths[b];
        if (sCol + wCol - 1 <= numCols && (rows[i][sCol - 1] || "").toString().trim() !== "") {
          var metricCell = sheet.getRange(rowIdx, sCol);
          metricCell.setBackground("#e8edf5")
                    .setFontColor("#1a365d")
                    .setFontWeight("bold")
                    .setFontSize(10)
                    .setHorizontalAlignment("left")
                    .setVerticalAlignment("middle");
          metricCell.setBorder(true, true, true, true, false, false, "#1a365d", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

          var seedsRange = sheet.getRange(rowIdx, sCol + 1, 1, 3);
          seedsRange.setHorizontalAlignment("center").setFontSize(10.5).setFontColor("#202124");
          seedsRange.setBorder(true, true, true, true, true, true, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);

          var msCell = sheet.getRange(rowIdx, sCol + 4);
          msCell.setHorizontalAlignment("center").setFontWeight("bold").setFontSize(10.5);
          msCell.setBorder(true, true, true, true, false, false, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);

          if (b === 1) {
            sheet.getRange(rowIdx, sCol + 1, 1, 4).setBackground("#f6fbf7");
          }

          sheet.getRange(rowIdx, sCol, 1, wCol).setBorder(true, true, true, true, false, false, "#1a365d", SpreadsheetApp.BorderStyle.SOLID);
        }
      }

      for (var d = 0; d < deltaCols.length; d++) {
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
                 .setFontSize(10.5);
            dCell.setBorder(true, true, true, true, false, false, "#137333", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
          } else if ((rows[i][0] || "") !== "") {
            dCell.setHorizontalAlignment("center").setFontColor("#5f6368");
            dCell.setBorder(true, true, true, true, false, false, "#d0d7de", SpreadsheetApp.BorderStyle.SOLID);
          }
        }
      }
    }

    for (var s = 0; s < sepCols.length; s++) {
      var sc = sepCols[s];
      if (sc <= numCols) {
        sheet.setColumnWidth(sc, 24);
        sheet.getRange(startRow, sc, numRows, 1).setBorder(false, false, false, false, false, false);
      }
    }

    for (var c = 1; c <= numCols; c++) {
      if (sepCols.indexOf(c) !== -1) continue;
      sheet.autoResizeColumn(c);
      var curW = sheet.getColumnWidth(c);
      if (blockStarts.indexOf(c) !== -1) {
        sheet.setColumnWidth(c, Math.max(curW, 115));
      } else if (deltaCols.indexOf(c) !== -1) {
        sheet.setColumnWidth(c, Math.max(curW, 95));
      } else if (msCols.indexOf(c) !== -1) {
        sheet.setColumnWidth(c, Math.max(curW, 135));
      } else {
        sheet.setColumnWidth(c, Math.max(curW, 85));
      }
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "OK",
      sheetName: sheet.getName(),
      updatedRows: numRows,
      cols: numCols
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput("Google Sheets & Drive Webhook is Active. Ready for POST requests.");
}
