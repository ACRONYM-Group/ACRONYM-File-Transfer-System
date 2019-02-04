const ipc = require('node-ipc');
const spawn = require('child_process').spawn;
const {app, BrowserWindow, dialog, ipcMain} = require('electron');
const fs = require("fs");
const ACE = require("./ACEManager.js");

var randomID = Math.floor(Math.random()*5000)*Date.now();
var requiredACEs = [];
var ownedACEs = [];
var ownedACEsData = {};
var loginWin;
var waitingToOpenPackManager = false;
var username = "NOTLOGGEDIN";
var CardsData = "<div class='programStatusCard' style='height:45px;'><h5 style='color:white; width:100%; background-color:#444444;'>Minecraft Server</h5><div style='width:100%; height:1px; background-color:black;'></div><div style='display:flex; width:100%;'><div style='display:flex;'><h5 style='color:white;'>Status: Online </h5><div class='cardHorizontalSpacer' style='width:1px; height:25px; background-color:black;'></div><h5 style='color:white;'>Players: 3 </h5></div></div></div>";
var programInstallDirectory = "Z:/AcroFTPClient/";
var packageToDisplay = "StatusCards";

var config = {};
var subbedPackages = {};

config = JSON.parse(fs.readFileSync(programInstallDirectory + "data/config.json"));

subbedPackages = JSON.parse(fs.readFileSync(programInstallDirectory + "data/subbedPackages.json"));

console.log("Config loaded. I am " + config["computerName"])

var avaliablePackageUpdates = [];
var avaliablePackages = {};

function createHubWindow() {
  hubWin = new BrowserWindow({width: 625, height: 340, frame: false, show: true});
  hubWin.loadFile('hub.html')
  return hubWin;
}

function createUpdateDialog(data) {
  updateWin = new BrowserWindow({width: 375, height: 225, frame: false, show: true});
  updateWin.loadFile('update.html')
  updateWin.webContents.openDevTools();
  return updateWin;
}

function writeSubbedPackagesToDisk() {
  fs.writeFileSync(programInstallDirectory + "\\data\\subbedPackages.json", JSON.stringify(subbedPackages));
}

function checkForPackageUpdates() {
  mainACE.send("checkForPackageUpdates", {username:username, computerName:config["computerName"]});
}

class frontendClass {
  constructor() {
    
  }

  loginResult(message) {
    if (message["data"]) {
      loginWin.send("authResult", message["data"]);
      loginWin.close();
      hubWin = createHubWindow();
    } else {
      loginWin.send("authResult", message["data"]);
    }
  }

  genericHandler(message) {
    console.log("Receiving Generic Command");
    if (message["type"] == "avaliablePackageUpdates") {
      avaliablePackageUpdates = message["data"];
      createUpdateDialog(message["data"]);
    }

    else if (message["type"] == "avaliablePackages") {
      if (waitingToOpenPackManager) {
        var packManagerWin = new BrowserWindow({width: 350, height: 360, frame: false, show: true});
        packManagerWin.loadFile('packManager.html');
        packManagerWin.openDevTools();
        waitingToOpenPackManager = false;
      }

      avaliablePackages = message["data"];
    }

    else if (message["type"] == "packageDownloadComplete") {
      console.log(message["data"] + " installation complete");
      subbedPackages[message["data"]]["status"] = "installed";
      writeSubbedPackagesToDisk();
    }

    else if (message["type"] == "printToConsole") {
      console.log("ACE Output: " + message["data"]);
    }
  }
}

frontend = new frontendClass();

mainACE = new ACE("generalPurpose", frontend);









ipcMain.on('login', (event, arg) => {
  console.log("Attempting Login")

  mainACE.login(arg["username"], arg["password"], config["computerName"]);
  username = arg["username"];
  checkForPackageUpdates();
});

ipcMain.on('requestProgramStatusCards', (event, arg) => {
  event.sender.send("programStatusCards", CardsData);
});

ipcMain.on('openPackManager', (event, arg) => {
  mainACE.send("requestListOfPackages", {username:username, computerName:config["computerName"]});

  waitingToOpenPackManager = true;
});

ipcMain.on('requestAvaliablePackageUpdates', (event, arg) => {
  event.sender.send("avaliablePackageUpdates", avaliablePackageUpdates);
});

ipcMain.on('requestAvaliablePackages', (event, arg) => {
  event.sender.send("avaliablePackages", avaliablePackages);
});

ipcMain.on('updatePackage', (event, arg) => {
  event.sender.send("updatingPackage", arg);

  dataToSend = {username:username, package:arg["package"], version:arg["version"], computerName:config["computerName"]};
  mainACE.send("requestDownloadPackage", dataToSend);

  subbedPackages[arg["package"]]["version"] = arg["version"]; 
  writeSubbedPackagesToDisk();
});

ipcMain.on('installPackage', (event, arg) => {
  event.sender.send("installingPackage", arg);

  dataToSend = {username:username, package:arg["name"], version:arg["version"], computerName:config["computerName"]};
  mainACE.send("requestInstallPackage", dataToSend);

  subbedPackages[arg["name"]] = {
    status: "installing",
    version: arg["version"],
    specificMajor: -1
  };

  writeSubbedPackagesToDisk();
});

ipcMain.on('uninstallPackage', (event, arg) => {

  dataToSend = {username:username, package:arg["name"], computerName:config["computerName"], subbedPackages:subbedPackages, programInstallDirectory:programInstallDirectory};
  mainACE.send("requestUninstallPackage", dataToSend);

  subbedPackages[arg["name"]] = undefined;
  writeSubbedPackagesToDisk();
});

ipcMain.on('requestSubbedPackages', (event, arg) => {
  event.sender.send("subbedPackages", subbedPackages);

});

ipcMain.on('openPackageEditor', (event, arg) => {
  packageToDisplay = arg;
  packageEditorWin = new BrowserWindow({width: 325, height: 520, frame: false, show: true});
  packageEditorWin.loadFile('packageEditor.html');
  packageEditorWin.webContents.openDevTools();
  console.log("Opening Package Editor");
});

ipcMain.on('requestPackageToDisplay', (event, arg) => {
  event.sender.send("packageToDisplay", packageToDisplay);
});

ipcMain.on('requestPackageInfo', (event, arg) => {
  dataToSend = {username:username, computerName:config["computerName"]};
  mainACE.send("requestListOfPackages", dataToSend);

  setTimeout(function(){
    event.sender.send("localPackageInfo", subbedPackages[arg]);
    event.sender.send("serverPackageInfo", avaliablePackages[arg]);
  }, 1000);
});

ipcMain.on('newSpecificMajor', (event, arg) => {
  subbedPackages[arg["name"]]["specificMajor"] = arg["newSpecificMajor"];

  dataToSend = {username:username, computerName:config["computerName"], subbedPackages: subbedPackages};
  mainACE.send("updateSubbedPackages", dataToSend);

  checkForPackageUpdates();

});

ipcMain.on('newPackageDefaultVersion', (event, arg) => {

  dataToSend = {username:username, computerName:config["computerName"], package:arg["name"], newDefaultVersion:arg["newDefaultVersion"]};
  mainACE.send("updatePackageDefaultVersion", dataToSend);

  checkForPackageUpdates();

});

ipcMain.on('uploadNewVersion', (event, arg) => {

  dataToSend = {username:username, computerName:config["computerName"], package:arg["name"], newVersionNumber:arg["newVersionNumber"], uploadDir:arg["newVersionPath"]};
  mainACE.send("uploadNewVersion", dataToSend);

  checkForPackageUpdates();

});

ipcMain.on('uploadNewPackage', (event, arg) => {

  dataToSend = {username:username, computerName:config["computerName"], package:arg["name"], newVersionNumber:arg["newVersionNumber"], packageDesc: arg["packageDesc"], uploadDir:arg["newVersionPath"]};
  mainACE.send("uploadNewPackage", dataToSend);

  checkForPackageUpdates();

  dataToSend = {username:username, computerName:config["computerName"]};
  mainACE.send("requestListOfPackages", dataToSend);

});

ipcMain.on('checkForUpdates', (event, arg) => {
  checkForPackageUpdates();
});

ipcMain.on('deletePackage', (event, arg) => {
  dataToSend = {username:username, computerName:config["computerName"], package:arg};
  mainACE.send("deletePackage", dataToSend);

  dataToSend = {username:username, computerName:config["computerName"]};
  mainACE.send("requestListOfPackages", dataToSend);

  /*
  var ACEID = findGeneralPurposeACE(ownedACEs, ownedACEsData);
  dataToSend = {target:ACEID, username:username, computerName:config["computerName"]};
  ipc.server.emit(ownedACEsData[ACEID]["socket"], "requestListOfPackages", dataToSend);*/
});




app.on('ready', function() {
  keepAliveWin = new BrowserWindow({width: 10, height: 10, frame: false, show: false});
  loginWin = new BrowserWindow({width: 235, height: 240, frame: false, show: true});
  loginWin.loadFile('login.html')
  //loginWin.webContents.openDevTools()
})

app.on('window-all-closed', () => {
  console.log("Ending App");
  ipc.server.emit(socket, "endProccess", "closingUI");
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  console.log("Ending App");
  ipc.server.emit(socket, "endProccess", "closingUI");
})