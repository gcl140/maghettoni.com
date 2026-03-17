// property-unit-edit.js — runs after DOM (placed at end of body, no defer)

// ── Amenity definitions ────────────────────────────────────────────────────────
var RESIDENTIAL_AMENITIES = [
  { key: "ac",            label: "Air Conditioning",     icon: "fa-snowflake" },
  { key: "wifi",          label: "Wi-Fi",                icon: "fa-wifi" },
  { key: "hot_water",     label: "Hot Water",            icon: "fa-fire" },
  { key: "kitchen",       label: "Kitchen",              icon: "fa-utensils" },
  { key: "smart_tv",      label: "Smart TV",             icon: "fa-tv" },
  { key: "furnished",     label: "Furnished",            icon: "fa-couch" },
  { key: "balcony",       label: "Balcony / Terrace",    icon: "fa-door-open" },
  { key: "housekeeping",  label: "Housekeeping",         icon: "fa-broom" },
  { key: "security_24_7", label: "24/7 Security",        icon: "fa-shield-alt" },
  { key: "pool",          label: "Swimming Pool",        icon: "fa-water" },
  { key: "parking",       label: "Parking Spaces",       icon: "fa-car",           quantity: true },
  { key: "generator",     label: "Generator / Inverter", icon: "fa-bolt" },
  { key: "water_storage", label: "Water Storage",        icon: "fa-tint" },
  { key: "gym",           label: "Gym / Fitness",        icon: "fa-dumbbell" },
  { key: "elevator",      label: "Elevator",             icon: "fa-angle-double-up" },
  { key: "garden",        label: "Garden / Grounds",     icon: "fa-seedling" },
];

var COMMERCIAL_AMENITIES = [
  { key: "ac",               label: "Air Conditioning",   icon: "fa-snowflake" },
  { key: "wifi",             label: "Business Wi-Fi",     icon: "fa-wifi" },
  { key: "generator",        label: "Generator",          icon: "fa-bolt" },
  { key: "cctv",             label: "CCTV Security",      icon: "fa-video" },
  { key: "security_guards",  label: "Security Guards",    icon: "fa-user-shield" },
  { key: "furnished_office", label: "Furnished Office",   icon: "fa-chair" },
  { key: "meeting_rooms",    label: "Meeting Rooms",      icon: "fa-users",          quantity: true },
  { key: "conference_rooms", label: "Conference Rooms",   icon: "fa-chalkboard",     quantity: true },
  { key: "coworking",        label: "Co-working Space",   icon: "fa-laptop" },
  { key: "reception",        label: "Reception Service",  icon: "fa-concierge-bell" },
  { key: "kitchen",          label: "Shared Kitchen",     icon: "fa-utensils" },
  { key: "printing",         label: "Print / Scan",       icon: "fa-print" },
  { key: "mail_handling",    label: "Mail Handling",      icon: "fa-envelope" },
  { key: "parking",          label: "Parking Spaces",     icon: "fa-car",            quantity: true },
  { key: "cafe",             label: "Café / Restaurant",  icon: "fa-coffee" },
  { key: "concierge",        label: "Concierge",          icon: "fa-bell" },
];

// ── Determine property type (server-computed flag is authoritative) ────────────
var form = document.querySelector("form[data-property-type]");
var isBusiness = form && form.getAttribute("data-is-business") === "1";
var amenityDefs = isBusiness ? COMMERCIAL_AMENITIES : RESIDENTIAL_AMENITIES;

// ── Read existing data ─────────────────────────────────────────────────────────
var hiddenAmenities = document.getElementById("id_amenities");
var existing = {};
try {
  existing = JSON.parse((hiddenAmenities && hiddenAmenities.value) || "{}");
} catch (e) {
  existing = {};
}

// ── Sync hidden input ──────────────────────────────────────────────────────────
function syncHidden() {
  var result = {};

  // Collect specs
  var bedEl  = document.getElementById("spec_bedrooms");
  var bathEl = document.getElementById("spec_bathrooms");
  var sqftEl = document.getElementById("spec_sqft");
  if (bedEl  && bedEl.value)  result.bedrooms    = parseInt(bedEl.value, 10)  || 0;
  if (bathEl && bathEl.value) result.bathrooms   = parseInt(bathEl.value, 10) || 0;
  if (sqftEl && sqftEl.value) result.square_feet = parseInt(sqftEl.value, 10) || 0;

  // Collect chip states
  amenityDefs.forEach(function (def) {
    var chip = document.getElementById("chip-" + def.key);
    if (!chip || chip.dataset.active !== "1") return;
    if (def.quantity) {
      var qtyEl = chip.querySelector(".chip-qty");
      result[def.key] = parseInt(qtyEl ? qtyEl.textContent : "1", 10) || 1;
    } else {
      result[def.key] = true;
    }
  });

  if (hiddenAmenities) hiddenAmenities.value = JSON.stringify(result);
}

// ── Build specs row (bed / bath / sqft) ───────────────────────────────────────
var specsContainer = document.getElementById("amenities-specs");
if (specsContainer) {
  function makeStepperCard(label, icon, hiddenId, initialVal) {
    var val = parseInt(initialVal, 10) || 0;

    var card = document.createElement("div");
    card.style.cssText =
      "display:flex;align-items:center;justify-content:space-between;padding:10px 14px;" +
      "border:1.5px solid #d1c4bc;border-left:4px solid #7c5c45;background:#fff;gap:8px;";

    var left = document.createElement("span");
    left.style.cssText = "display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#5c3f2e;white-space:nowrap;";
    left.innerHTML = '<i class="fas ' + icon + '" style="font-size:12px;color:#7c5c45;"></i>' + label;

    var stepper = document.createElement("span");
    stepper.style.cssText = "display:flex;align-items:center;gap:6px;flex-shrink:0;";

    var btnMinus = document.createElement("button");
    btnMinus.type = "button";
    btnMinus.textContent = "−";
    btnMinus.style.cssText =
      "width:22px;height:22px;border:1px solid #d1c4bc;background:#f9f5f3;" +
      "color:#7c5c45;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;";

    var display = document.createElement("span");
    display.style.cssText = "min-width:22px;text-align:center;font-size:14px;font-weight:600;color:#3b2512;";
    display.textContent = String(val);

    var btnPlus = document.createElement("button");
    btnPlus.type = "button";
    btnPlus.textContent = "+";
    btnPlus.style.cssText = btnMinus.style.cssText;

    function update(newVal) {
      val = Math.max(0, newVal);
      display.textContent = String(val);
      var hidEl = document.getElementById(hiddenId);
      if (hidEl) hidEl.value = val > 0 ? String(val) : "";
      syncHidden();
    }

    btnMinus.addEventListener("click", function () { update(val - 1); });
    btnPlus.addEventListener("click",  function () { update(val + 1); });

    stepper.appendChild(btnMinus);
    stepper.appendChild(display);
    stepper.appendChild(btnPlus);
    card.appendChild(left);
    card.appendChild(stepper);
    return card;
  }

  function makeSqftCard(hiddenId, initialVal) {
    var card = document.createElement("div");
    card.style.cssText =
      "display:flex;align-items:center;justify-content:space-between;padding:10px 14px;" +
      "border:1.5px solid #d1c4bc;border-left:4px solid #7c5c45;background:#fff;gap:8px;";

    var left = document.createElement("span");
    left.style.cssText = "display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#5c3f2e;white-space:nowrap;";
    left.innerHTML = '<i class="fas fa-ruler-combined" style="font-size:12px;color:#7c5c45;"></i>Sq ft';

    var input = document.createElement("input");
    input.type = "number";
    input.placeholder = "e.g. 850";
    input.value = initialVal || "";
    input.min = "0";
    input.style.cssText =
      "width:80px;padding:4px 8px;border:1px solid #d1c4bc;font-size:13px;text-align:right;" +
      "color:#3b2512;background:#faf7f5;outline:none;";

    input.addEventListener("input", function () {
      var hidEl = document.getElementById(hiddenId);
      if (hidEl) hidEl.value = this.value;
      syncHidden();
    });

    card.appendChild(left);
    card.appendChild(input);
    return card;
  }

  var bedVal  = document.getElementById("spec_bedrooms")  ? document.getElementById("spec_bedrooms").value  : "";
  var bathVal = document.getElementById("spec_bathrooms") ? document.getElementById("spec_bathrooms").value : "";
  var sqftVal = document.getElementById("spec_sqft")      ? document.getElementById("spec_sqft").value      : "";

  if (!isBusiness) {
    specsContainer.appendChild(makeStepperCard("Bedrooms",  "fa-bed",  "spec_bedrooms",  bedVal));
    specsContainer.appendChild(makeStepperCard("Bathrooms", "fa-bath", "spec_bathrooms", bathVal));
  }
  specsContainer.appendChild(makeSqftCard("spec_sqft", sqftVal));
}

// ── Build amenity chips ────────────────────────────────────────────────────────
var grid = document.getElementById("amenities-grid");
if (grid) {
  amenityDefs.forEach(function (def) {
    var isOn = !!(existing[def.key]);
    var qty  = (typeof existing[def.key] === "number") ? existing[def.key] : 1;

    var chip = document.createElement("div");
    chip.id = "chip-" + def.key;
    chip.dataset.active = isOn ? "1" : "0";

    function applyStyle() {
      var on = chip.dataset.active === "1";
      chip.style.cssText =
        "display:flex;align-items:center;gap:6px;padding:8px 10px;" +
        "border:1.5px solid " + (on ? "#7c5c45" : "#d1c4bc") + ";" +
        "background:" + (on ? "#7c5c45" : "#fff") + ";" +
        "color:" + (on ? "#fff" : "#6b5344") + ";" +
        "cursor:pointer;user-select:none;font-size:13px;font-weight:500;transition:all .12s;";
    }
    applyStyle();

    var icon = document.createElement("i");
    icon.className = "fas " + def.icon;
    icon.style.cssText = "font-size:11px;flex-shrink:0;";

    var labelEl = document.createElement("span");
    labelEl.style.cssText = "flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;";
    labelEl.textContent = def.label;

    chip.appendChild(icon);
    chip.appendChild(labelEl);

    if (def.quantity) {
      var stepper = document.createElement("span");
      stepper.style.cssText =
        "display:" + (isOn ? "flex" : "none") + ";align-items:center;gap:3px;margin-left:auto;flex-shrink:0;";

      var bMinus = document.createElement("button");
      bMinus.type = "button";
      bMinus.textContent = "−";
      bMinus.style.cssText =
        "width:18px;height:18px;border:1px solid rgba(255,255,255,.5);background:rgba(255,255,255,.2);" +
        "color:#fff;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;";

      var qtyEl = document.createElement("span");
      qtyEl.className = "chip-qty";
      qtyEl.style.cssText = "min-width:16px;text-align:center;font-size:12px;";
      qtyEl.textContent = String(qty);

      var bPlus = document.createElement("button");
      bPlus.type = "button";
      bPlus.textContent = "+";
      bPlus.style.cssText = bMinus.style.cssText;

      bMinus.addEventListener("click", function (e) {
        e.stopPropagation();
        var v = parseInt(qtyEl.textContent, 10) || 1;
        if (v > 1) { qtyEl.textContent = String(v - 1); syncHidden(); }
      });
      bPlus.addEventListener("click", function (e) {
        e.stopPropagation();
        qtyEl.textContent = String((parseInt(qtyEl.textContent, 10) || 1) + 1);
        syncHidden();
      });

      stepper.appendChild(bMinus);
      stepper.appendChild(qtyEl);
      stepper.appendChild(bPlus);
      chip.appendChild(stepper);

      chip.addEventListener("click", function () {
        chip.dataset.active = chip.dataset.active === "1" ? "0" : "1";
        applyStyle();
        stepper.style.display = chip.dataset.active === "1" ? "flex" : "none";
        syncHidden();
      });
    } else {
      chip.addEventListener("click", function () {
        chip.dataset.active = chip.dataset.active === "1" ? "0" : "1";
        applyStyle();
        syncHidden();
      });
    }

    grid.appendChild(chip);
  });

  syncHidden(); // write initial state
}

// ── Rent formatting ────────────────────────────────────────────────────────────
var rentInput = document.getElementById("id_monthly_rent");
if (rentInput) {
  rentInput.addEventListener("blur", function () {
    var value = parseFloat(this.value);
    if (!isNaN(value) && value >= 0) this.value = value.toFixed(2);
  });
}

// ── Price suggestion by bedroom count ─────────────────────────────────────────
var priceSuggestions = { 0: "800-1200", 1: "1200-1800", 2: "1800-2500", 3: "2500-3500", 4: "3500-5000" };
var specBedrooms = document.getElementById("spec_bedrooms");
if (specBedrooms && rentInput && rentInput.parentNode) {
  var observer = new MutationObserver(function () {
    var beds = parseInt(specBedrooms.value, 10) || 0;
    var suggestion = priceSuggestions[beds] || priceSuggestions[4];
    var tip = document.getElementById("price-suggestion");
    if (!tip) {
      tip = document.createElement("div");
      tip.id = "price-suggestion";
      tip.style.cssText = "margin-top:8px;padding:10px 12px;background:#eff6ff;border:1px solid #bfdbfe;font-size:13px;color:#1e40af;";
      rentInput.parentNode.appendChild(tip);
    }
    tip.innerHTML = '<i class="fas fa-lightbulb" style="margin-right:4px;"></i><strong>Market range:</strong> $' + suggestion + "/mo for " + beds + " bed" + (beds !== 1 ? "s" : "");
  });
  observer.observe(specBedrooms, { attributes: true, attributeFilter: ["value"] });
}

// ── Required field validation ──────────────────────────────────────────────────
var mainForm = document.querySelector("form");
if (mainForm) {
  mainForm.addEventListener("submit", function (e) {
    var fields = mainForm.querySelectorAll("[required]");
    var isValid = true;
    fields.forEach(function (field) {
      if (!field.value.trim() && field.type !== "checkbox") {
        field.classList.add("border-red-500", "bg-red-50");
        isValid = false;
      } else {
        field.classList.remove("border-red-500", "bg-red-50");
      }
    });
    if (!isValid) {
      e.preventDefault();
      var first = mainForm.querySelector(".border-red-500");
      if (first) { first.scrollIntoView({ behavior: "smooth", block: "center" }); first.focus(); }
      showAlert("Please fill in all required fields!", "error");
    }
  });
}
