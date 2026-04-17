function queryParams() {
  return new URLSearchParams(window.location.search);
}

function formatDate(dateText) {
  const date = new Date(`${dateText}T12:00:00`);
  return new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric" }).format(date);
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function showError(message) {
  const errorBox = document.getElementById("errorBox");
  errorBox.hidden = false;
  errorBox.textContent = message;
}

function render(data) {
  const { property, stay } = data;
  document.getElementById("displayCard").hidden = false;

  setText("propertyHeadline", property.headline || "Your Airbnb stay");
  setText("guestGreeting", `Hello, ${stay.guestName}`);
  setText("propertyName", `${property.name} • ${property.address}`);
  setText("stayDates", `${formatDate(stay.arrivalDate)} - ${formatDate(stay.departureDate)}`);
  setText("guestCount", `${stay.guestCount} guest${stay.guestCount === 1 ? "" : "s"}`);
  setText("occasion", stay.occasion || "Enjoy your stay");
  setText("messageCard", stay.message || "Welcome. We hope you have a comfortable visit.");
  setText("wifiName", property.wifiName || "-");
  setText("wifiPassword", property.wifiPassword || "-");
  setText("checkInNote", property.checkInNote || "-");
  setText("checkoutNote", property.checkoutNote || "-");
  setText("contactName", property.contactName || "-");
  setText("contactPhone", property.contactPhone || "-");

  const tipsList = document.getElementById("houseTips");
  tipsList.innerHTML = "";
  (property.houseTips || []).forEach((tip) => {
    const item = document.createElement("li");
    item.textContent = tip;
    tipsList.append(item);
  });
}

async function init() {
  const params = queryParams();
  const propertyId = params.get("property");
  const stayId = params.get("stay");

  if (!propertyId || !stayId) {
    showError("Missing property or stay in the URL. Open this page from the admin dashboard.");
    return;
  }

  const response = await fetch(`/api/display?property=${encodeURIComponent(propertyId)}&stay=${encodeURIComponent(stayId)}`);
  if (!response.ok) {
    showError("We could not load this welcome screen. Check the selected property and stay.");
    return;
  }

  render(await response.json());
}

init();
