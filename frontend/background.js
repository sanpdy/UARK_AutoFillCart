// background.js - Background service worker
  // This script runs in the background and can handle events
  chrome.runtime.onInstalled.addListener(function() {
    console.log('Walmart Recipe Assistant Extension installed');
    
    // Initialize with default settings
    chrome.storage.local.set({
      backendUrl: 'http://localhost:8080/' // Default backend URL
    });
  });
  
  // Listen for messages
  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    // Handle any background tasks if needed
  });
