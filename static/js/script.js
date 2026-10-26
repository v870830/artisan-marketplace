
// ============================================
// ARTISAN MARKETPLACE
// Database-backed marketplace and smart pricing
// ============================================

// Flask passes all database products to this page.
const products = window.marketplaceProducts || [];

let selectedCategory = "All";
let currentLanguage = localStorage.getItem("artisanLanguage") || "en";

const productGrid = document.getElementById("productGrid");
const searchInput = document.getElementById("searchInput");
const emptyMessage = document.getElementById("emptyMessage");
const languageSelect = document.getElementById("languageSelect");

// ============================================
// TRANSLATIONS
// ============================================

const translations = {
    en: {
        location: "Location",
        artisan: "Artisan",
        view: "View Details",
        buy: "Buy Now",
        noProducts: "No products found. Try another search.",
        invalid: "Please enter valid non-negative costs and a margin between 0 and 500%.",
        suggested: "Suggested Price",
        buyerPrompt: "Enter your name to place this order:",
        quantityPrompt: "Enter quantity:",
        orderSuccess: "Your order has been placed!",
        orderError: "Could not place the order. Please try again.",
        price: "Price",
        description: "Description",
        category: "Category",
        imageFallback: "Handmade Craft"
    },

    hi: {
        location: "स्थान",
        artisan: "कारीगर",
        view: "विवरण देखें",
        buy: "अभी खरीदें",
        noProducts: "कोई उत्पाद नहीं मिला। दूसरी खोज करें।",
        invalid: "कृपया सही लागत और 0 से 500% के बीच लाभ प्रतिशत दर्ज करें।",
        suggested: "संभावित मूल्य",
        buyerPrompt: "ऑर्डर करने के लिए अपना नाम दर्ज करें:",
        quantityPrompt: "मात्रा दर्ज करें:",
        orderSuccess: "आपका ऑर्डर सफलतापूर्वक दर्ज हो गया!",
        orderError: "ऑर्डर नहीं हो सका। कृपया दोबारा कोशिश करें।",
        price: "कीमत",
        description: "विवरण",
        category: "श्रेणी",
        imageFallback: "हस्तनिर्मित उत्पाद"
    }
};

// ============================================
// SAFE HTML HELPERS
// ============================================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}

function formatPrice(price) {
    const amount = Number(price);

    if (!Number.isFinite(amount)) {
        return "0";
    }

    return amount.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}

// ============================================
// RENDER DATABASE PRODUCTS
// ============================================

function renderProducts() {
    if (!productGrid || !searchInput || !emptyMessage) {
        return;
    }

    const query = searchInput.value.trim().toLowerCase();
    const labels = translations[currentLanguage];

    const filteredProducts = products.filter(product => {
        const matchesCategory =
            selectedCategory === "All" ||
            String(product.category).toLowerCase() ===
                selectedCategory.toLowerCase();

        const searchableText = [
            product.name,
            product.category,
            product.location,
            product.artisan,
            product.description
        ].join(" ").toLowerCase();

        return matchesCategory && searchableText.includes(query);
    });

    productGrid.innerHTML = "";

    filteredProducts.forEach(product => {
        const card = document.createElement("article");
        card.className = "product-card";

        // Store the product ID on the card.
        const productId = Number(product.id);
        card.dataset.productId = productId;

        const imageHTML = product.image
            ? `<img
                   src="${escapeHTML(product.image)}"
                   alt="${escapeHTML(product.name)}"
                   loading="lazy"
                   onerror="this.onerror=null;this.src='https://placehold.co/600x400/f5e9d8/70452c?text=Handmade+Craft'">`
            : `<img
                   src="https://placehold.co/600x400/f5e9d8/70452c?text=Handmade+Craft"
                   alt="${escapeHTML(labels.imageFallback)}">`;

        card.innerHTML = `
            <div class="product-image">
                ${imageHTML}

                <span class="product-tag">
                    ${escapeHTML(product.category)}
                </span>
            </div>

            <div class="product-info">
                <span class="product-category">
                    ${escapeHTML(product.category)}
                </span>

                <h3>${escapeHTML(product.name)}</h3>

                <p>${escapeHTML(product.description)}</p>

                <div class="product-location">
                    📍 ${escapeHTML(labels.location)}:
                    ${escapeHTML(product.location)}
                </div>

                <div class="product-location">
                    👤 ${escapeHTML(labels.artisan)}:
                    ${escapeHTML(product.artisan)}
                </div>

                <div class="product-bottom">
                    <span class="product-price">
                        ₹${formatPrice(product.price)}
                    </span>

                    <button
                        type="button"
                        class="view-product"
                        data-product-id="${productId}">
                        ${escapeHTML(labels.view)} →
                    </button>

                    <button
                        type="button"
                        class="buy-product"
                        data-product-id="${productId}">
                        ${escapeHTML(labels.buy)}
                    </button>
                </div>
            </div>
        `;

        productGrid.appendChild(card);
    });

    emptyMessage.hidden = filteredProducts.length !== 0;

    if (filteredProducts.length === 0) {
        emptyMessage.textContent = labels.noProducts;
    }
}

// ============================================
// CATEGORY FILTER
// ============================================

document.querySelectorAll(".category").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".category").forEach(item => {
            item.classList.remove("active");
        });

        button.classList.add("active");
        selectedCategory = button.dataset.category;

        renderProducts();
    });
});

// ============================================
// SEARCH
// ============================================

if (searchInput) {
    searchInput.addEventListener("input", renderProducts);
}

// ============================================
// PRODUCT DETAILS BUTTON
// ============================================

if (productGrid) {
    productGrid.addEventListener("click", event => {
        const button = event.target.closest(".view-product");

        if (!button) {
            return;
        }

        const productId = Number(button.dataset.productId);

        const product = products.find(item =>
            Number(item.id) === productId
        );

        if (!product) {
            return;
        }

        const labels = translations[currentLanguage];

        alert(
            `${product.name}\n\n` +
            `${labels.description}: ${product.description}\n\n` +
            `${labels.category}: ${product.category}\n` +
            `${labels.location}: ${product.location}\n` +
            `${labels.artisan}: ${product.artisan}\n` +
            `${labels.price}: ₹${formatPrice(product.price)}`
        );
    });
}

// ============================================
// PLACE ORDER
// ============================================

if (productGrid) {
    productGrid.addEventListener("click", async event => {
        const button = event.target.closest(".buy-product");

        if (!button) {
            return;
        }

        const productId = Number(button.dataset.productId);
        const labels = translations[currentLanguage];

        const buyerName = prompt(labels.buyerPrompt);

        if (!buyerName || !buyerName.trim()) {
            return;
        }

        const quantityInput = prompt(labels.quantityPrompt, "1");

        if (quantityInput === null) {
            return;
        }

        const quantity = Number(quantityInput);

        if (
            !Number.isInteger(quantity) ||
            quantity < 1 ||
            quantity > 100
        ) {
            alert(
                currentLanguage === "hi"
                    ? "मात्रा 1 से 100 के बीच पूरी संख्या होनी चाहिए।"
                    : "Quantity must be a whole number between 1 and 100."
            );

            return;
        }

        button.disabled = true;

        try {
            const response = await fetch(
                `/place-order/${productId}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: new URLSearchParams({
                        buyer_name: buyerName.trim(),
                        quantity: String(quantity)
                    })
                }
            );

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                throw new Error("Order request failed");
            }

            alert(labels.orderSuccess);
            window.location.href = "/orders";

        } catch (error) {
            console.error("Order error:", error);
            alert(labels.orderError);
        } finally {
            button.disabled = false;
        }
    });
}

// ============================================
// LANGUAGE SWITCH
// ============================================

function setLanguage(language) {
    currentLanguage = language === "hi" ? "hi" : "en";

    document.documentElement.lang = currentLanguage;

    localStorage.setItem("artisanLanguage", currentLanguage);

    if (languageSelect) {
        languageSelect.value = currentLanguage;
    }

    document.querySelectorAll("[data-en][data-hi]").forEach(element => {
        element.textContent =
            element.dataset[currentLanguage];
    });

    if (searchInput) {
        searchInput.placeholder =
            searchInput.dataset[
                `placeholder${currentLanguage.toUpperCase()}`
            ] || (
                currentLanguage === "hi"
                    ? "हस्तशिल्प खोजें..."
                    : "Search crafts..."
            );
    }

    renderProducts();
    calculatePrice();
}

if (languageSelect) {
    languageSelect.addEventListener("change", () => {
        setLanguage(languageSelect.value);
    });
}

// ============================================
// SMART PRICING CALCULATOR
// ============================================

function calculatePrice() {
    const materialInput = document.getElementById("materialCost");
    const labourInput = document.getElementById("labourCost");
    const marginInput = document.getElementById("margin");
    const result = document.getElementById("priceResult");

    if (!materialInput || !labourInput || !marginInput || !result) {
        return;
    }

    const material = Number(materialInput.value);
    const labour = Number(labourInput.value);
    const margin = Number(marginInput.value);

    const labels = translations[currentLanguage];

    if (
        materialInput.value === "" ||
        labourInput.value === "" ||
        marginInput.value === "" ||
        !Number.isFinite(material) ||
        !Number.isFinite(labour) ||
        !Number.isFinite(margin) ||
        material < 0 ||
        labour < 0 ||
        margin < 0 ||
        margin > 500
    ) {
        result.textContent = labels.invalid;
        return;
    }

    const totalCost = material + labour;
    const suggestedPrice = Math.ceil(
        totalCost * (1 + margin / 100)
    );

    result.textContent =
        `${labels.suggested}: ₹${formatPrice(suggestedPrice)}`;
}

const calculateButton = document.getElementById("calculatePrice");

if (calculateButton) {
    calculateButton.addEventListener("click", calculatePrice);
}

// ============================================
// PRODUCT IMAGE PREVIEW POPUP
// Double-click a product image to open it.
// ============================================

function openProductPreview(product) {
    const modal = document.getElementById("productPreviewModal");

    if (!modal || !product) {
        return;
    }

    const image = document.getElementById("previewImage");

    if (!image) {
        return;
    }

    image.src = product.image ||
        "https://placehold.co/600x400/f5e9d8/70452c?text=Handmade+Craft";

    image.alt = product.name || "Handmade craft";

    document.getElementById("previewName").textContent =
        product.name || "";

    document.getElementById("previewPrice").textContent =
        "₹" + formatPrice(product.price);

    document.getElementById("previewCategory").textContent =
        product.category || "";

    document.getElementById("previewArtisan").textContent =
        product.artisan || "";

    document.getElementById("previewLocation").textContent =
        product.location || "";

    document.getElementById("previewDescription").textContent =
        product.description || "";

    const isHindi = currentLanguage === "hi";

    document.getElementById("previewCategoryLabel").textContent =
        isHindi ? "श्रेणी:" : "Category:";

    document.getElementById("previewArtisanLabel").textContent =
        isHindi ? "कारीगर:" : "Artisan:";

    document.getElementById("previewLocationLabel").textContent =
        isHindi ? "स्थान:" : "Location:";

    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
}

// Close the product preview popup.
function closeProductPreview() {
    const modal = document.getElementById("productPreviewModal");
    const image = document.getElementById("previewImage");

    if (!modal) {
        return;
    }

    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");

    if (image) {
        image.src = "";
    }
}

// Use event delegation because product cards are rendered dynamically.
if (productGrid) {
    productGrid.addEventListener("dblclick", event => {
        // Make sure the clicked target is an HTML element.
        if (!(event.target instanceof Element)) {
            return;
        }

        const image = event.target.closest(".product-image img");

        if (!image) {
            return;
        }

        const card = image.closest(".product-card");

        if (!card) {
            return;
        }

        // Find the exact product using its ID, not its name.
        const productId = Number(card.dataset.productId);

        const product = products.find(item =>
            Number(item.id) === productId
        );

        if (product) {
            openProductPreview(product);
        }
    });
}

// Close button.
const previewCloseButton =
    document.getElementById("closeProductPreview");

if (previewCloseButton) {
    previewCloseButton.addEventListener(
        "click",
        closeProductPreview
    );
}

// Close when the dark background is clicked.
const previewModalElement =
    document.getElementById("productPreviewModal");

if (previewModalElement) {
    previewModalElement.addEventListener("click", event => {
        if (event.target === previewModalElement) {
            closeProductPreview();
        }
    });
}

// Close when the Escape key is pressed.
document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
        closeProductPreview();
    }
});

// ============================================
// INITIALIZE APPLICATION
// ============================================

setLanguage(currentLanguage);

