const state = {
  store: null,
  selectedStayId: null,
};

const elements = {
  staySelect: document.getElementById("staySelect"),
  propertySelect: document.getElementById("propertySelect"),
  heroGuest: document.getElementById("heroGuest"),
  heroProperty: document.getElementById("heroProperty"),
  heroDates: document.getElementById("heroDates"),
  previewName: document.getElementById("previewName"),
  previewMessage: document.getElementById("previewMessage"),
  previewStay: document.getElementById("previewStay"),
  previewGuestCount: document.getElementById("previewGuestCount"),
  previewWifi: document.getElementById("previewWifi"),
  previewHost: document.getElementById("previewHost"),
  previewLink: document.getElementById("previewLink"),
  sidebarPreviewLink: document.getElementById("sidebarPreviewLink"),
  saveBtn: document.getElementById("saveBtn"),
  newStayBtn: document.getElementById("newStayBtn"),
  setActiveStayBtn: document.getElementById("setActiveStayBtn"),
  addTipBtn: document.getElementById("addTipBtn"),
  saveStatus: document.getElementById("saveStatus"),
  tipsEditor: document.getElementById("tipsEditor"),
  tvStatus: document.getElementById("tvStatus"),
  pairingCodeInput: document.getElementById("pairingCodeInput"),
  deviceNameInput: document.getElementById("deviceNameInput"),
  pairDeviceBtn: document.getElementById("pairDeviceBtn"),
  pairStatus: document.getElementById("pairStatus"),
  deviceList: document.getElementById("deviceList"),
  logoutBtn: document.getElementById("logoutBtn"),
};

const fieldIds = [
  "guestName",
  "guestCount",
  "arrivalDate",
  "departureDate",
  "occasion",
  "message",
  "propertyName",
  "headline",
  "address",
  "contactName",
  "contactPhone",
  "wifiName",
  "wifiPassword",
  "checkInNote",
  "checkoutNote",
];

const fields = Object.fromEntries(fieldIds.map((id) => [id, document.getElementById(id)]));

function formatDate(dateText) {
  const date = new Date(`${dateText}T12:00:00`);
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
}

function getSelectedStay() {
  return state.store.stays.find((stay) => stay.id === state.selectedStayId);
}

function getPropertyById(propertyId) {
  return state.store.properties.find((property) => property.id === propertyId);
}

function getDevicesForProperty(propertyId) {
  return (state.store.tvDevices || []).filter((device) => device.propertyId === propertyId);
}

function buildDisplayUrl(stay) {
  return `/display.html?property=${encodeURIComponent(stay.propertyId)}&stay=${encodeURIComponent(stay.id)}`;
}

function updateStatus(message) {
  elements.saveStatus.textContent = message;
}

function updatePairStatus(message) {
  elements.pairStatus.textContent = message;
}

function renderStayOptions() {
  elements.staySelect.innerHTML = "";
  state.store.stays.forEach((stay) => {
    const property = getPropertyById(stay.propertyId);
    const option = document.createElement("option");
    option.value = stay.id;
    option.textContent = `${stay.guestName} - ${property.name} - ${formatDate(stay.arrivalDate)} to ${formatDate(stay.departureDate)}`;
    elements.staySelect.append(option);
  });
  elements.staySelect.value = state.selectedStayId;
}

function renderPropertyOptions(selectedPropertyId) {
  elements.propertySelect.innerHTML = "";
  state.store.properties.forEach((property) => {
    const option = document.createElement("option");
    option.value = property.id;
    option.textContent = property.name;
    elements.propertySelect.append(option);
  });
  elements.propertySelect.value = selectedPropertyId;
}

function renderTipsEditor(property) {
  elements.tipsEditor.innerHTML = "";
  property.houseTips.forEach((tip, index) => {
    const row = document.createElement("div");
    row.className = "tip-row";

    const input = document.createElement("input");
    input.type = "text";
    input.value = tip;
    input.addEventListener("input", () => {
      property.houseTips[index] = input.value;
      syncPreview();
      updateStatus("You have unsaved changes.");
    });

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "ghost-btn";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      property.houseTips.splice(index, 1);
      renderTipsEditor(property);
      syncPreview();
      updateStatus("You have unsaved changes.");
    });

    row.append(input, removeButton);
    elements.tipsEditor.append(row);
  });
}

function renderDevices(property) {
  elements.deviceList.innerHTML = "";
  const devices = state.store.tvDevices || [];

  if (devices.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No Fire TVs registered yet.";
    elements.deviceList.append(empty);
    return;
  }

  devices.forEach((device) => {
    const item = document.createElement("li");
    const propertyName = device.propertyId ? getPropertyById(device.propertyId)?.name || "Unknown property" : "Not assigned";
    const activeTag = device.propertyId === property.id ? "This property" : propertyName;
    item.textContent = `${device.name} - Code ${device.pairingCode} - ${device.status} - ${activeTag}`;
    elements.deviceList.append(item);
  });
}

function populateEditor() {
  const stay = getSelectedStay();
  const property = getPropertyById(stay.propertyId);

  fields.guestName.value = stay.guestName;
  fields.guestCount.value = stay.guestCount;
  fields.arrivalDate.value = stay.arrivalDate;
  fields.departureDate.value = stay.departureDate;
  fields.occasion.value = stay.occasion;
  fields.message.value = stay.message;
  fields.propertyName.value = property.name;
  fields.headline.value = property.headline;
  fields.address.value = property.address;
  fields.contactName.value = property.contactName;
  fields.contactPhone.value = property.contactPhone;
  fields.wifiName.value = property.wifiName;
  fields.wifiPassword.value = property.wifiPassword;
  fields.checkInNote.value = property.checkInNote;
  fields.checkoutNote.value = property.checkoutNote;

  renderPropertyOptions(property.id);
  renderTipsEditor(property);
  renderDevices(property);
  syncPreview();
}

function syncModelFromForm() {
  const stay = getSelectedStay();
  const currentProperty = getPropertyById(stay.propertyId);
  const nextProperty = getPropertyById(elements.propertySelect.value);

  stay.guestName = fields.guestName.value.trim() || "Guest";
  stay.guestCount = Number(fields.guestCount.value || 1);
  stay.arrivalDate = fields.arrivalDate.value;
  stay.departureDate = fields.departureDate.value;
  stay.occasion = fields.occasion.value.trim();
  stay.message = fields.message.value.trim();
  stay.propertyId = nextProperty.id;

  currentProperty.name = currentProperty.id === nextProperty.id ? fields.propertyName.value.trim() : currentProperty.name;
  currentProperty.headline = currentProperty.id === nextProperty.id ? fields.headline.value.trim() : currentProperty.headline;
  currentProperty.address = currentProperty.id === nextProperty.id ? fields.address.value.trim() : currentProperty.address;
  currentProperty.contactName = currentProperty.id === nextProperty.id ? fields.contactName.value.trim() : currentProperty.contactName;
  currentProperty.contactPhone = currentProperty.id === nextProperty.id ? fields.contactPhone.value.trim() : currentProperty.contactPhone;
  currentProperty.wifiName = currentProperty.id === nextProperty.id ? fields.wifiName.value.trim() : currentProperty.wifiName;
  currentProperty.wifiPassword = currentProperty.id === nextProperty.id ? fields.wifiPassword.value.trim() : currentProperty.wifiPassword;
  currentProperty.checkInNote = currentProperty.id === nextProperty.id ? fields.checkInNote.value.trim() : currentProperty.checkInNote;
  currentProperty.checkoutNote = currentProperty.id === nextProperty.id ? fields.checkoutNote.value.trim() : currentProperty.checkoutNote;
}

function syncPropertyFromFields(property) {
  property.name = fields.propertyName.value.trim();
  property.headline = fields.headline.value.trim();
  property.address = fields.address.value.trim();
  property.contactName = fields.contactName.value.trim();
  property.contactPhone = fields.contactPhone.value.trim();
  property.wifiName = fields.wifiName.value.trim();
  property.wifiPassword = fields.wifiPassword.value.trim();
  property.checkInNote = fields.checkInNote.value.trim();
  property.checkoutNote = fields.checkoutNote.value.trim();
}

function syncPreview() {
  const stay = getSelectedStay();
  const property = getPropertyById(elements.propertySelect.value || stay.propertyId);

  stay.guestName = fields.guestName.value.trim() || "Guest";
  stay.guestCount = Number(fields.guestCount.value || 1);
  stay.arrivalDate = fields.arrivalDate.value;
  stay.departureDate = fields.departureDate.value;
  stay.occasion = fields.occasion.value.trim();
  stay.message = fields.message.value.trim();
  stay.propertyId = property.id;
  syncPropertyFromFields(property);

  const displayUrl = buildDisplayUrl(stay);
  const isActiveStay = property.activeStayId === stay.id;
  const propertyDevices = getDevicesForProperty(property.id);

  elements.heroGuest.textContent = stay.guestName;
  elements.heroProperty.textContent = property.name;
  elements.heroDates.textContent = `${formatDate(stay.arrivalDate)} - ${formatDate(stay.departureDate)}`;
  elements.previewName.textContent = `Hello, ${stay.guestName}`;
  elements.previewMessage.textContent = stay.message || "We are glad you're here.";
  elements.previewStay.textContent = `${formatDate(stay.arrivalDate)} - ${formatDate(stay.departureDate)}`;
  elements.previewGuestCount.textContent = `${stay.guestCount} guest${stay.guestCount === 1 ? "" : "s"}`;
  elements.previewWifi.textContent = property.wifiName || "Add network";
  elements.previewHost.textContent = property.contactName || "Add host";
  elements.previewLink.href = displayUrl;
  elements.sidebarPreviewLink.href = displayUrl;
  elements.sidebarPreviewLink.textContent = `${window.location.origin}${displayUrl}`;
  elements.tvStatus.textContent = isActiveStay
    ? `Fire TV will show ${stay.guestName} for ${property.name}. ${propertyDevices.length} paired TV(s) currently point at this property.`
    : `A different stay is active for ${property.name}. Use "Show this stay on Fire TV" to switch it.`;

  renderDevices(property);
}

async function saveStore() {
  const response = await fetch("/api/store", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state.store),
  });

  if (response.status === 401) {
    window.location.href = "/login.html";
    return;
  }

  updateStatus(response.ok ? "Saved. Fire TVs and browser previews now reflect these updates." : "Save failed. Please try again.");
  if (response.ok) {
    renderStayOptions();
    populateEditor();
  }
}

async function pairDevice() {
  const stay = getSelectedStay();
  const property = getPropertyById(stay.propertyId);
  const pairingCode = elements.pairingCodeInput.value.trim().toUpperCase();
  const displayName = elements.deviceNameInput.value.trim();

  if (!pairingCode) {
    updatePairStatus("Enter the code shown on the Fire TV first.");
    return;
  }

  const response = await fetch("/api/tv/assign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pairingCode,
      propertyId: property.id,
      displayName,
    }),
  });

  const payload = await response.json();
  if (response.status === 401) {
    window.location.href = "/login.html";
    return;
  }
  if (!response.ok) {
    updatePairStatus(payload.error || "Could not pair that Fire TV.");
    return;
  }

  const existingIndex = state.store.tvDevices.findIndex((device) => device.id === payload.device.id);
  if (existingIndex >= 0) {
    state.store.tvDevices[existingIndex] = payload.device;
  } else {
    state.store.tvDevices.push(payload.device);
  }

  elements.pairingCodeInput.value = "";
  elements.deviceNameInput.value = "";
  renderDevices(property);
  syncPreview();
  updatePairStatus(`Paired ${payload.device.name} to ${property.name}. Save the stay data separately if you changed anything else.`);
}

function attachFieldListeners() {
  Object.values(fields).forEach((field) => {
    field.addEventListener("input", () => {
      syncPreview();
      updateStatus("You have unsaved changes.");
    });
  });

  elements.propertySelect.addEventListener("change", () => {
    const stay = getSelectedStay();
    stay.propertyId = elements.propertySelect.value;
    populateEditor();
    updateStatus("You have unsaved changes.");
  });

  elements.staySelect.addEventListener("change", () => {
    state.selectedStayId = elements.staySelect.value;
    populateEditor();
    updateStatus("Viewing selected stay.");
  });

  elements.addTipBtn.addEventListener("click", () => {
    const property = getPropertyById(elements.propertySelect.value);
    property.houseTips.push("New house tip");
    renderTipsEditor(property);
    syncPreview();
    updateStatus("You have unsaved changes.");
  });

  elements.newStayBtn.addEventListener("click", () => {
    const firstProperty = state.store.properties[0];
    const newStay = {
      id: `stay-${Date.now()}`,
      propertyId: firstProperty.id,
      guestName: "New Guest",
      guestCount: 2,
      arrivalDate: "2026-05-01",
      departureDate: "2026-05-04",
      occasion: "Weekend stay",
      message: "Welcome to your stay. We are glad to host you.",
    };
    state.store.stays.push(newStay);
    state.selectedStayId = newStay.id;
    renderStayOptions();
    populateEditor();
    updateStatus("New stay added. Save when ready.");
  });

  elements.setActiveStayBtn.addEventListener("click", () => {
    const stay = getSelectedStay();
    const property = getPropertyById(stay.propertyId);
    property.activeStayId = stay.id;
    syncPreview();
    updateStatus("This stay is now the active Fire TV stay for that property. Save when ready.");
  });

  elements.pairDeviceBtn.addEventListener("click", pairDevice);
  elements.saveBtn.addEventListener("click", saveStore);
  elements.logoutBtn.addEventListener("click", async () => {
    await fetch("/api/session", { method: "DELETE" });
    window.location.href = "/login.html";
  });
}

async function loadStore() {
  const response = await fetch("/api/store");
  if (response.status === 401) {
    window.location.href = "/login.html";
    return;
  }
  state.store = await response.json();
  state.store.tvDevices = state.store.tvDevices || [];
  state.selectedStayId = state.store.stays[0]?.id || null;
  renderStayOptions();
  attachFieldListeners();
  populateEditor();
}

loadStore();
