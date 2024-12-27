console.log("create_cnote.js is loaded");
// Import data.js file
import data from "../static/data.js";
// ... rest of your code ...

// Import data.js file
import data from "../static/data.js";
try {
  const data = await import("../static/data.js");
  console.log(data.default.articles);
  console.log(data.default.destinations);
  console.log(data.default.items);
} catch (error) {
  console.error("Error importing data.js file:", error);
}

// Update date and time
function updateDateTime() {
  const now = new Date();
  const formattedDateTime = now.toLocaleString("en-US", { hour12: true });
  document.getElementById("datetime").innerText = formattedDateTime;
}

setInterval(updateDateTime, 1000);
updateDateTime();

// Calculate total
const inputs = document.querySelectorAll('.relative input[type="number"]');
inputs.forEach((input) => {
  input.addEventListener("input", calculateTotal);
});

function calculateTotal() {
  let total = 0;
  inputs.forEach((input) => {
    total += parseFloat(input.value) || 0;
  });
  document.getElementById("grandTotal").innerText = total;
}

// Said to contain dropdown
const saidToContainInput = document.getElementById("saidToContain");
const saidToContainList = document.getElementById("saidToContainList");

saidToContainInput.addEventListener("input", function () {
  const query = this.value.toLowerCase();
  saidToContainList.innerHTML = "";
  const filteredItems = data.items.filter((item) =>
    item.toLowerCase().includes(query)
  );
  filteredItems.forEach((item) => {
    const div = document.createElement("div");
    div.className = "dropdown-item";
    div.textContent = item;
    div.addEventListener("click", function () {
      saidToContainInput.value = item;
      saidToContainList.classList.remove("show");
    });
    saidToContainList.appendChild(div);
  });
  if (filteredItems.length > 0) {
    saidToContainList.classList.add("show");
  } else {
    saidToContainList.classList.remove("show");
  }
});

document.addEventListener("click", function (event) {
  if (!event.target.closest(".dropdown-container")) {
    saidToContainList.classList.remove("show");
  }
});

// Destination dropdown
const destinationInput = document.getElementById("destinationInput");
const destinationList = document.getElementById("destinationList");

destinationInput.addEventListener("input", function () {
  const query = this.value.toLowerCase();
  destinationList.innerHTML = "";
  const filteredDestinations = data.destinations.filter((destination) =>
    destination.toLowerCase().includes(query)
  );
  filteredDestinations.forEach((destination) => {
    const div = document.createElement("div");
    div.className = "dropdown-item";
    div.textContent = destination;
    div.addEventListener("click", function () {
      destinationInput.value = destination;
      destinationList.classList.remove("show");
    });
    destinationList.appendChild(div);
  });
  if (filteredDestinations.length > 0) {
    destinationList.classList.add("show");
  } else {
    destinationList.classList.remove("show ");
  }
});

document.addEventListener("click", function (event) {
  if (!event.target.closest(".dropdown-container")) {
    destinationList.classList.remove("show");
  }
});

let currentFocus = -1;

destinationInput.addEventListener("keydown", function (e) {
  const items = destinationList.getElementsByClassName("dropdown-item");
  if (e.keyCode === 40) {
    // Down arrow
    currentFocus++;
    addActive(items);
  } else if (e.keyCode === 38) {
    // Up arrow
    currentFocus--;
    addActive(items);
  } else if (e.keyCode === 13) {
    // Enter
    e.preventDefault();
    if (currentFocus > -1) {
      if (items) items[currentFocus].click();
    }
  }
});

function addActive(items) {
  if (!items) return false;
  removeActive(items);
  if (currentFocus >= items.length) currentFocus = 0;
  if (currentFocus < 0) currentFocus = items.length - 1;
  items[currentFocus].classList.add("active");
}

function removeActive(items) {
  for (let i = 0; i < items.length; i++) {
    items[i].classList.remove("active");
  }
}

// Add article
function addArticle() {
  const article = document.getElementById("article").value;
  const art = document.getElementById("art").value;
  const saidToContain = document.getElementById("saidToContain").value;
  const amount = document.getElementById("amount").value;
  const statusColor = document.getElementById("status").style.backgroundColor;

  if (
    article &&
    art &&
    saidToContain &&
    (amount || article === "Weight" || article === "Fix")
  ) {
    const container = document.getElementById("articleDetailsContainer");
    const row = document.createElement("div");
    row.className = "grid grid-cols-5 gap-4 p-2 rounded";
    row.style.backgroundColor = statusColor;

    row.innerHTML = `
                  <div>${article}</div>
                  <div>${art}</div>
                  <div>${saidToContain}</div>
                  <div>₹${amount}</div>
                  <button class="bg-red-500 text-white px-2 py-1 rounded" onclick="deleteArticle(this, ${
                    amount || 0
                  })">Delete</button>
              `;

    container.appendChild(row);

    const freightInput = document.getElementById("freight");
    freightInput.value =
      parseFloat(freightInput.value) + (parseFloat(amount) || 0);

    calculateTotalCharges();

    document.getElementById("article").value = "Article";
    document.getElementById("art").value = "";
    document.getElementById("saidToContain").value = "";
    document.getElementById("amount").value = "";
    toggleAmountInput();
    toggleWtRateInput();
  }
}

// Delete article
function deleteArticle(button, amount) {
  const row = button.parentElement;
  row.remove();

  const freightInput = document.getElementById("freight");
  freightInput.value = parseFloat(freightInput.value) - amount;

  calculateTotalCharges();
}

// Calculate total charges
function calculateTotalCharges() {
  const freight = parseFloat(document.getElementById("freight").value) || 0;
  const doorDly = parseFloat(document.getElementById("doorDly").value) || 0;
  const pickup = parseFloat(document.getElementById("pickup").value) || 0;
  const other = parseFloat(document.getElementById("other").value) || 0;

  const total = freight + doorDly + pickup + other;
  document.getElementById("grandTotal").innerText = total;
}

const chargeInputs = document.querySelectorAll('.grid input[type="number"]');
chargeInputs.forEach((input) => {
  input.addEventListener("input", calculateTotalCharges);
});

// Update status
function updateStatus(status, color) {
  const statusElement = document.getElementById("status");
  statusElement.innerText = status;
  statusElement.style.backgroundColor = color;
  statusElement.style.fontWeight = "bold";

  // Update the color of existing rows
  const rows = document.querySelectorAll("#articleDetailsContainer > div");
  rows.forEach((row) => {
    row.style.backgroundColor = color;
  });
}

// Toggle amount input
function toggleAmountInput() {
  const article = document.getElementById("article").value;
  const amountInput = document.getElementById("amount");
  if (article === "Weight" || article === "Fix") {
    amountInput.disabled = true;
    amountInput.value = "";
  } else {
    amountInput.disabled = false;
  }
}

// Toggle weight rate input
function toggleWtRateInput() {
  const article = document.getElementById("article").value;
  const wtRateInput = document.getElementById("wtRate");
  if (article === "Weight") {
    wtRateInput.disabled = false;
  } else {
    wtRateInput.disabled = true;
    wtRateInput.value = "";
  }
}

// Initialize the amount input state based on the default article value
document.addEventListener("DOMContentLoaded", function () {
  toggleAmountInput();
  toggleWtRateInput();
  updateStatus("TO PAY", "#ff9800");
});
