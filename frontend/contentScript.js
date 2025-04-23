console.log('Walmart Recipe Assistant Extension loaded');

// Listen for messages from popup or background script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'cart_loaded') {
    // This could be used to enhance the Walmart cart page
    console.log('Cart loaded:', request.cartData);
    
    // You could modify the Walmart page here to show additional info
    // For example, add a banner confirming the cart was created from a recipe
  }
});