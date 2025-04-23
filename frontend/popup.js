// Walmart Recipe Assistant Extension

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const elements = {
    tabs: document.querySelectorAll('.tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    chatMessages: document.getElementById('chat-messages'),
    userMessageInput: document.getElementById('user-message'),
    sendMessageButton: document.getElementById('send-message'),
    fileInput: document.getElementById('recipe-pdf'),
    fileNameDisplay: document.getElementById('file-name'),
    backendUrlInput: document.getElementById('backend-url'),
    saveSettingsButton: document.getElementById('save-settings'),
    loadingIndicator: document.getElementById('loading-indicator')
  };
  
  // State
  const state = {
    conversationHistory: [],
    conversationId: null,
    cartItems: [],
    messageCount: 0, // Track number of messages
    ingredientsList: null, // Store ingredients when found in messages
    cartGenerationRequested: false, // Flag to track if cart generation was already requested
    processingInput: false // Flag to prevent multiple simultaneous requests
  };
  
  initializeApp();
  
  function initializeApp() {
    setupTabs();
    loadBackendUrl();
    setupEventListeners();
    initializeConversation();
  }
  
  // UI Setup
  function setupTabs() {
    elements.tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        elements.tabs.forEach(t => t.classList.remove('active'));
        elements.tabContents.forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        const tabName = tab.getAttribute('data-tab');
        document.getElementById(tabName + '-tab').classList.add('active');
      });
    });
  }
  
  function loadBackendUrl() {
    chrome.storage.local.get('backendUrl', data => {
      if (data.backendUrl) {
        elements.backendUrlInput.value = data.backendUrl;
      }
    });
  }
  
  function setupEventListeners() {
    elements.sendMessageButton.addEventListener('click', handleSendMessage);
    
    elements.userMessageInput.addEventListener('keypress', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });
    
    elements.userMessageInput.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Updated PDF file handling
    elements.fileInput.addEventListener('change', e => {
      if (state.processingInput) return;
      
      const selectedFile = e.target.files[0];
      if (selectedFile) {
        elements.fileNameDisplay.textContent = selectedFile.name;
        elements.fileNameDisplay.style.display = 'block';
        addUserMessage(`I've uploaded a recipe file: ${selectedFile.name}`);
        
        // Process the PDF file directly
        processPdfFile(selectedFile);
      } else {
        elements.fileNameDisplay.style.display = 'none';
      }
    });
    
    elements.saveSettingsButton.addEventListener('click', saveSettings);
  }
  
  // Add a new function to handle PDF file processing
  function processPdfFile(pdfFile) {
    // Prevent multiple simultaneous requests
    if (state.processingInput) return;
    state.processingInput = true;
    
    // Show loading indicator
    showLoading(true);
    addBotMessage("I'm processing your recipe file and looking for ingredients...");
    
    getBackendUrl(backendUrl => {
      if (!backendUrl) {
        handleNoBackendUrl();
        state.processingInput = false;
        return;
      }
      
      // Create form data with the PDF file
      const formData = new FormData();
      formData.append('recipe_pdf', pdfFile);
      
      // Send to the PDF processing endpoint
      fetch(`${backendUrl}/api/process-pdf`, {
        method: 'POST',
        body: formData
      })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        hideLoading();
        state.processingInput = false;
        
        if (data.success) {
          // Store conversation data
          if (data.conversation_id) {
            state.conversationId = data.conversation_id;
          }
          
          if (data.conversation_history) {
            state.conversationHistory = data.conversation_history;
          }
          
          // Display extracted ingredients
          if (data.ingredients && data.ingredients.length > 0) {
            state.ingredientsList = data.ingredients;
            state.cartGenerationRequested = true; // Mark that we've requested cart generation
            
            // Format the ingredients list nicely
            const ingredientsList = data.ingredients.map(ing => 
              `- ${ing.ingredient} - ${ing.quantity}`
            ).join('\n');
            
            addBotMessage(`I've extracted these ingredients from your recipe:\n\n${ingredientsList}`);
          }
          
          // Show cart items if available
          if (data.cart_items && data.cart_items.length > 0) {
            state.cartItems = data.cart_items;
            addProductMessage(data.cart_items);
          } else {
            addBotMessage("I couldn't find matching products for these ingredients at Walmart.");
          }
        } else {
          addBotMessage(data.message || "Sorry, I had trouble processing your recipe file.");
        }
      })
      .catch(error => {
        hideLoading();
        state.processingInput = false;
        addBotMessage("Sorry, there was an error processing your recipe file. Please try again.");
        console.error('Error:', error);
      });
    });
  }
  
  // Debounced message sending to prevent duplicate requests
  function handleSendMessage() {
    if (state.processingInput) return;
    
    const message = elements.userMessageInput.value.trim();
    if (!message) return;
    
    addUserMessage(message);
    state.messageCount++;
    elements.userMessageInput.value = '';
    elements.userMessageInput.style.height = 'auto';
    
    processUserInput(message, null);
  }
  
  // Conversation handling
  function initializeConversation() {
    addBotMessage("Hello! I'm your Walmart Recipe Assistant. Tell me what recipe you'd like to make, or upload a recipe PDF, and I'll help you create a shopping list.");
  }
  
  function resetConversation() {
    state.conversationHistory = [];
    state.conversationId = null;
    state.cartItems = [];
    state.messageCount = 0;
    state.ingredientsList = null;
    state.cartGenerationRequested = false;
    elements.chatMessages.innerHTML = '';
    
    initializeConversation();
  }
  
  // Message display functions
  function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    messageElement.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
    elements.chatMessages.appendChild(messageElement);
    
    scrollToBottom();
  }
  
  function addBotMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot';
    messageElement.innerHTML = `<div class="message-content">${message}</div>`;
    elements.chatMessages.appendChild(messageElement);
    
    // CRITICAL FIX: Only extract ingredients and request cart if:
    // 1. We don't have cart items already 
    // 2. We don't have ingredients list already
    // 3. We haven't requested cart generation already
    // 4. Message doesn't contain confirmation text about searching ingredients
    if (!state.cartItems.length && 
        !state.ingredientsList && 
        !state.cartGenerationRequested && 
        !message.includes("I'll help you find these ingredients") && 
        !message.includes("Here are the ingredients I found")) {
      
      console.log("Checking message for ingredients...");
      const extractedIngredients = extractIngredientsFromMessage(message);
      if (extractedIngredients && extractedIngredients.length > 0) {
        console.log(`Found ${extractedIngredients.length} ingredients, setting state and requesting cart.`);
        state.ingredientsList = extractedIngredients;
        
        // SET THIS FLAG IMMEDIATELY before making request
        state.cartGenerationRequested = true;
        
        // If we find ingredients in the message, trigger a cart generation request
        requestCartFromIngredients(extractedIngredients);
      }
    } else {
      // Log why we're not extracting ingredients
      console.log("Skipping ingredient extraction:", {
        hasCartItems: state.cartItems.length > 0,
        hasIngredientsList: !!state.ingredientsList,
        cartRequested: state.cartGenerationRequested,
        hasSearchText: message.includes("I'll help you find these ingredients") || message.includes("Here are the ingredients I found")
      });
    }
    
    scrollToBottom();
  }
  
  function extractIngredientsFromMessage(message) {
    // Check if the message contains ingredient listing patterns
    if (message.includes("ingredient") || message.includes("Ingredient") || 
        message.includes("you'll need") || message.includes("You'll need")) {
      
      // Try to find patterns that look like ingredients with quantities
      const lines = message.split(/[.•\n<br>]/).map(line => line.trim()).filter(line => line);
      
      const ingredients = [];
      const ingredientRegex = /([0-9¼½¾⅓⅔]+ ?(?:cup|tablespoon|tbsp|tsp|teaspoon|oz|ounce|pound|lb|g|gram|kg|ml|liter|l|bunch|pinch|dash|to taste|small|medium|large|clove|slice|piece|can)[s]? (?:of )?)?([a-zA-Z\s,]+)/i;
      
      for (const line of lines) {
        // Skip very short lines or lines that don't look like ingredients
        if (line.length < 5 || line.startsWith("Here") || line.startsWith("For") || 
            line.includes("recipe") || line.includes("Recipe")) {
          continue;
        }
        
        const match = line.match(ingredientRegex);
        if (match) {
          const quantity = match[1] ? match[1].trim() : "as needed";
          const ingredient = match[2].trim().replace(/,$/, '');
          
          // Only add if it looks like a real ingredient
          if (ingredient.length > 2 && !/^(if|and|or|to|the|for|your|with)$/i.test(ingredient)) {
            ingredients.push({
              ingredient,
              quantity
            });
          }
        }
      }
      
      // Only return ingredients if we found a reasonable number
      return ingredients.length >= 2 ? ingredients : null;
    }
    
    return null;
  }
  
  function requestCartFromIngredients(ingredients) {
    // Check if cart generation was already requested or if we already have cart items
    if (state.cartGenerationRequested || state.cartItems.length > 0) {
      console.log("Cart generation already requested or cart items exist, skipping duplicate request");
      return;
    }
    
    // CRITICAL: Show loading indicator BEFORE setting the flag
    showLoading(true);
    console.log("Showing loading indicator for cart generation");
    
    // Then set the flag to prevent concurrent requests
    state.cartGenerationRequested = true;
    
    addBotMessage("I'll help you find these ingredients at Walmart. Let me search for them...");
    
    getBackendUrl(backendUrl => {
      if (!backendUrl) {
        state.cartGenerationRequested = false; // Reset flag on error
        handleNoBackendUrl();
        return;
      }
      
      // Create a formatting ingredients list for tool call as expected by the backend
      const formattedIngredients = ingredients.map(ing => ({
        ingredient: ing.ingredient,
        quantity: ing.quantity
      }));
      
      // Disable all buttons during this operation
      document.querySelectorAll('button').forEach(btn => {
        btn.disabled = true;
      });
      
      console.log("Sending ingredients to backend:", formattedIngredients);
      
      // Send to backend for processing
      fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          isText: true,
          recipe_text: "Please find these ingredients for me",
          conversation_id: state.conversationId,
          conversation_history: state.conversationHistory,
          // Send the extracted ingredients directly to help the backend
          extracted_ingredients: formattedIngredients,
          // Make sure we don't accidentally create duplicate carts
          skip_cart_generation: false // We explicitly want to generate a cart here
        })
      })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        hideLoading();
        
        // Re-enable buttons
        document.querySelectorAll('button').forEach(btn => {
          btn.disabled = false;
        });
        
        if (data.success) {
          if (data.conversation_id) {
            state.conversationId = data.conversation_id;
          }
          
          if (data.conversation_history) {
            state.conversationHistory = data.conversation_history;
          }
          
          if (data.cart_items && data.cart_items.length > 0) {
            console.log(`Successfully received ${data.cart_items.length} cart items from backend`);
            state.cartItems = data.cart_items;
            addProductMessage(data.cart_items);
          } else {
            console.warn("Backend didn't return any cart items");
            state.cartGenerationRequested = false; // Reset the flag so we can try again
            addBotMessage("I couldn't find all the ingredients for your recipe. Could you try describing it again?");
          }
        } else {
          console.error("Backend returned error:", data.message);
          // If the call failed, don't reset cartGenerationRequested
          addBotMessage(data.message || "I had trouble processing your ingredients. Could you describe your recipe again?");
        }
      })
      .catch(error => {
        hideLoading();
        
        // Re-enable buttons
        document.querySelectorAll('button').forEach(btn => {
          btn.disabled = false;
        });
        
        console.error('Error requesting cart items:', error);
        state.cartGenerationRequested = false; // Reset flag on error
        addBotMessage("I'm having trouble connecting to the Walmart product search. Please try again later.");
      });
    });
  }
  
  function ensureValidImageUrl(url) {
    if (!url) return '/images/placeholder.png';
    
    return (url.startsWith('http://') || url.startsWith('https://')) 
      ? url 
      : chrome.runtime.getURL('/images/placeholder.png');
  }
  
  function addProductMessage(products) {
    // IMPORTANT: Filter out products that clearly don't belong
    const validProducts = products.filter(product => {
      // Skip products with invalid or missing data
      if (!product.main || !product.main.name) return false;
      
      // Skip products with suspicious names (not food-related)
      const name = product.main.name.toLowerCase();
      const suspiciousTerms = [
        'thank you card', 'ring', 'book', 'hardcover', 'paperback', 'ebook', 
        'jewelry', 't-shirt', 'tshirt', 'shirt', 'clothes', 'clothing', 'shoes',
        'bandana', 'background cloth', 'descendants', 'kindle', 'office desk',
        'home decor', 'sign', 'air conditioner', 'kettle'
      ];
      
      // Check if the product name contains any suspicious terms
      return !suspiciousTerms.some(term => name.includes(term));
    });
    
    // If we filtered out more than half the products, log a warning
    if (validProducts.length < products.length / 2) {
      console.warn(`Filtered out ${products.length - validProducts.length} suspicious products!`);
    }
    
    // Update state with filtered products only
    state.cartItems = validProducts.length > 0 ? validProducts : products;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'product-grid';
    
    let html = `<h3>Here are the ingredients I found for your recipe:</h3>`;
    
    state.cartItems.forEach((product, index) => {
      const mainItem = product.main;
      const mainImageUrl = ensureValidImageUrl(mainItem.image);
      
      html += `
        <div class="product-card" data-index="${index}">
          <div class="product-card-header">
            <img src="${mainImageUrl}" alt="${mainItem.name}" class="product-card-image" onerror="this.src='/images/placeholder.png'">
            <div class="product-card-info">
              <div class="product-card-name">${mainItem.name}</div>
              <div class="product-card-details">
                <span class="product-card-price">${mainItem.price || 'Price unavailable'}</span>
                <span class="product-card-quantity">${mainItem.quantity || ''}</span>
              </div>
            </div>
          </div>
      `;
      
      if (product.alternatives && product.alternatives.length > 0) {
        html += `
          <div class="product-card-alternatives">
            <div class="alternatives-title">Alternatives</div>
        `;
        
        product.alternatives.forEach((alt, altIndex) => {
          const altImageUrl = ensureValidImageUrl(alt.image);
          
          html += `
            <div class="alternative-item" data-product-index="${index}" data-alt-index="${altIndex}">
              <img src="${altImageUrl}" alt="${alt.name}" class="alternative-image" onerror="this.src='/images/placeholder.png'">
              <div class="alternative-info">
                <div class="alternative-name">${alt.name}</div>
                <div class="alternative-details">
                  <span class="alternative-price">${alt.price || 'Price unavailable'}</span>
                </div>
              </div>
              <button class="substitute-button" data-product-index="${index}" data-alt-index="${altIndex}">Use This</button>
            </div>
          `;
        });
        
        html += `</div>`;
      }
      
      html += `</div>`;
    });
    
    html += `
      <div class="cart-confirmation">
        <button id="view-cart-button" class="view-cart-button">
          Add All to Walmart Cart
        </button>
      </div>
    `;
    
    messageElement.innerHTML = html;
    elements.chatMessages.appendChild(messageElement);
    
    // Set up event listeners with direct onclick assignment for more reliable handling
    document.querySelectorAll('.substitute-button').forEach(button => {
      button.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const productIndex = parseInt(this.getAttribute('data-product-index'));
        const altIndex = parseInt(this.getAttribute('data-alt-index'));
        substituteProduct(productIndex, altIndex);
      };
    });
    
    // Direct onclick assignment for cart button
    const cartButton = document.getElementById('view-cart-button');
    if (cartButton) {
      cartButton.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        cartButtonClicked();
      };
    }
    
    scrollToBottom();
  }
  
  // Add this new function to handle cart button clicks
  function cartButtonClicked() {
    console.log("Cart button clicked");
    console.log("Cart items:", state.cartItems);
    console.log("Conversation ID:", state.conversationId);
    
    // Call the regular generate cart function
    generateCart();
  }
  
  function updateProductDisplay() {
    const existingGrid = document.querySelector('.product-grid');
    if (existingGrid) {
      existingGrid.remove();
    }
    
    addProductMessage(state.cartItems);
  }
  
  // API interaction functions
  function processUserInput(textMessage, fileMessage) {
    // Prevent multiple simultaneous requests
    if (state.processingInput) return;
    state.processingInput = true;
    
    // Only show loading for significant operations, not just chat messages
    const isSignificantOperation = fileMessage || state.messageCount <= 1;
    if (isSignificantOperation) {
      showLoading(true);
    }
    
    getBackendUrl(backendUrl => {
      if (!backendUrl) {
        handleNoBackendUrl();
        state.processingInput = false;
        return;
      }
      
      const formData = new FormData();
      const isText = !!textMessage;
      
      if (isText) {
        formData.append('recipe_text', textMessage);
      } else if (fileMessage) {
        formData.append('recipe_pdf', fileMessage);
      }
      
      formData.append('isText', isText);
      formData.append('conversation_history', JSON.stringify(state.conversationHistory));
      
      if (state.conversationId) {
        formData.append('conversation_id', state.conversationId);
      }
      
      // CRITICAL: Set skip_cart_generation to true if:
      // 1. We already have cart items OR
      // 2. We've already requested cart generation
      const skipCartGeneration = state.cartItems.length > 0 || state.cartGenerationRequested;
      formData.append('skip_cart_generation', skipCartGeneration);
      
      // Log this important flag to help with debugging
      console.log(`Processing user input with skip_cart_generation=${skipCartGeneration}`);
      console.log(`Current cart items: ${state.cartItems.length}, cartGenerationRequested: ${state.cartGenerationRequested}`);
      
      fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        body: formData
      })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        if (isSignificantOperation) {
          hideLoading();
        }
        state.processingInput = false;
        
        if (data.success) {
          if (data.conversation_id) {
            state.conversationId = data.conversation_id;
          }
          
          if (data.conversation_history) {
            state.conversationHistory = data.conversation_history;
          }
          
          if (data.message) {
            addBotMessage(data.message);
          }
          
          // Check for ingredients from the API response
          if (data.ingredients && data.ingredients.length > 0 && !state.ingredientsList) {
            state.ingredientsList = data.ingredients;
          }
          
          // Show cart items only if we don't already have cart items
          if (data.cart_items && data.cart_items.length > 0 && !state.cartItems.length) {
            state.cartItems = data.cart_items;
            addProductMessage(data.cart_items);
            state.cartGenerationRequested = true; // Mark that we have completed cart generation
          }
        } else {
          addBotMessage(data.message || "Sorry, I encountered an error processing your request.");
        }
      })
      .catch(error => {
        if (isSignificantOperation) {
          hideLoading();
        }
        state.processingInput = false;
        addBotMessage("Sorry, there was an error connecting to the server. Please try again.");
        console.error('Error:', error);
      });
    });
  }
  
  function substituteProduct(productIndex, alternativeIndex) {
    showLoading(true);
    
    getBackendUrl(backendUrl => {
      if (!backendUrl) {
        handleNoBackendUrl();
        return;
      }
      
      const substituteUrl = `${backendUrl}/api/substitute`;
      
      fetch(substituteUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredient_index: productIndex,
          substitute_index: alternativeIndex,
          conversation_id: state.conversationId,
          cart_items: state.cartItems // Include cart items in request for better reliability
        })
      })
      .then(response => {
        if (!response.ok) throw new Error(`Network response was not ok: ${response.status}`);
        return response.json();
      })
      .then(data => {
        hideLoading();
        
        if (data.success) {
          state.cartItems = data.cart_items;
          updateProductDisplay();
          addBotMessage("I've updated your selection. Is there anything else you'd like to change?");
        } else {
          addBotMessage(`Sorry, I couldn't substitute that product: ${data.message}`);
        }
      })
      .catch(error => {
        hideLoading();
        addBotMessage("Sorry, there was an error substituting the product. Please try again later.");
        console.error('Error:', error);
      });
    });
  }
  
  // Add a flag to prevent multiple cart generation requests
  let cartGenerationInProgress = false;
  
  function generateCart() {
    // Prevent duplicate cart generation requests
    if (cartGenerationInProgress) {
      console.log("Cart generation already in progress, skipping duplicate request");
      return;
    }
    
    cartGenerationInProgress = true;
    showLoading(true);
    
    getBackendUrl(backendUrl => {
      if (!backendUrl) {
        handleNoBackendUrl();
        cartGenerationInProgress = false;
        return;
      }
      
      // Log cart items for debugging
      console.log("Generating cart with items:", state.cartItems);
      
      // Validate cart items before sending to server
      const validCartItems = state.cartItems.filter(item => 
        item && item.main && (item.main.id || (item.main.item_details && item.main.item_details.itemId))
      );
      
      if (validCartItems.length === 0) {
        console.warn("No valid cart items with IDs found!");
        createFallbackCart();
        cartGenerationInProgress = false;
        return;
      }
      
      addBotMessage("Great! I'm preparing your Walmart cart with these ingredients...");
      
      // Prepare a simple request body - the real processing happens on the server
      fetch(`${backendUrl}/api/generate-cart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: state.conversationId,
          cart_items: state.cartItems
        })
      })
      .then(response => {
        if (!response.ok) throw new Error(`Network response was not ok: ${response.status}`);
        return response.json();
      })
      .then(data => {
        hideLoading();
        cartGenerationInProgress = false;
        
        if (data.success && data.cart_url) {
          // Success case
          console.log("Successfully generated cart URL:", data.cart_url);
          displayCartLink(data.cart_url);
          window.open(data.cart_url, '_blank');
        } else {
          // Error from server
          console.warn("Server failed to generate cart:", data.message || 'Unknown error');
          addBotMessage(`I'm having trouble creating your cart. Let me try a different approach.`);
          
          // Try the fallback method
          setTimeout(() => {
            createFallbackCart();
          }, 1000);
        }
      })
      .catch(error => {
        hideLoading();
        cartGenerationInProgress = false;
        console.error('Error generating cart:', error);
        
        addBotMessage("I'm having trouble connecting to the cart generation service. Let me prepare a direct link for you instead.");
        
        // Try to create a fallback cart with basic URL
        setTimeout(() => {
          createFallbackCart();
        }, 1000);
      });
    });
  }
  
  function createFallbackCart() {
    // Check if we have any valid cart items
    let validItemIds = [];
    
    for (const product of state.cartItems) {
      // Make sure we have a valid item ID that's not 0
      if (product.main && product.main.id && product.main.id !== 0) {
        validItemIds.push({
          id: product.main.id,
          quantity: 1
        });
      }
    }
    
    // If we have valid product IDs, create a cart URL
    if (validItemIds.length > 0) {
      // Format: https://www.walmart.com/cart?items=12345:1:walmart&items=67890:1:walmart
      let cartUrl = "https://www.walmart.com/cart?";
      const params = validItemIds.map(item => `items=${item.id}:1:walmart`);
      cartUrl += params.join('&');
      
      console.log("Generated cart URL with items:", cartUrl);
      displayCartLink(cartUrl);
      window.open(cartUrl, '_blank');
    } else {
      // If no valid items, try to use item details
      try {
        let validItems = [];
        for (const product of state.cartItems) {
          if (product.main && product.main.name) {
            // Try to extract ID from more complex objects
            let itemId = null;
            
            if (product.main.id) {
              itemId = product.main.id;
            } else if (product.main.item_details && product.main.item_details.itemId) {
              itemId = product.main.item_details.itemId;
            } else if (product.item_details && product.item_details.itemId) {
              itemId = product.item_details.itemId;
            }
            
            if (itemId && itemId !== 0) {
              validItems.push({
                id: itemId,
                quantity: 1
              });
            }
          }
        }
        
        if (validItems.length > 0) {
          let cartUrl = "https://www.walmart.com/cart?";
          const params = validItems.map(item => `items=${item.id}:1:walmart`);
          cartUrl += params.join('&');
          
          console.log("Generated alternative cart URL with items:", cartUrl);
          displayCartLink(cartUrl);
          window.open(cartUrl, '_blank');
          return;
        }
      } catch (e) {
        console.error("Error trying to extract item IDs:", e);
      }
      
      // Just open the empty cart if no valid items
      console.warn("No valid item IDs found, opening empty cart");
      displayCartLink("https://www.walmart.com/cart");
      window.open('https://www.walmart.com/cart', '_blank');
    }
  }
  
  function displayCartLink(url) {
    const messageElement = document.createElement('div');
    messageElement.className = 'cart-confirmation-message';
    messageElement.innerHTML = `
      <div class="success-message">Your cart is ready!</div>
      <a href="${url}" target="_blank" class="cart-link">
        Open Walmart.com to Complete Your Order
      </a>
    `;
    elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
  }
  
  // Utility functions
  function getBackendUrl(callback) {
    chrome.storage.local.get('backendUrl', data => callback(data.backendUrl));
  }
  
  function handleNoBackendUrl() {
    hideLoading();
    addBotMessage("Please set the backend URL in Settings before we continue.");
  }
  
  function saveSettings() {
    const backendUrl = elements.backendUrlInput.value.trim();
    if (backendUrl) {
      chrome.storage.local.set({ backendUrl }, () => {
        showStatus('Settings saved successfully!', 'success');
      });
    } else {
      showStatus('Please enter a valid URL!', 'error');
    }
  }
  
  function showLoading(show) {
    elements.loadingIndicator.style.display = show ? 'block' : 'none';
  }
  
  function hideLoading() {
    showLoading(false);
  }
  
  function showStatus(message, type) {
    const statusElement = document.createElement('div');
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    
    const activeTabContent = document.querySelector('.tab-content.active');
    activeTabContent.appendChild(statusElement);
    
    setTimeout(() => {
      statusElement.remove();
    }, 5000);
  }
  
  function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
  
  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});