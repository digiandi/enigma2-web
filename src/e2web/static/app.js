"use strict";
document.addEventListener("change", event => {
  if (event.target.matches("[data-receiver-select], [data-auto-submit]")) event.target.form.requestSubmit();
});
function filterTable(input) {
  const area = document.getElementById(input.dataset.tableFilter);
  if (!area) return;
  const query = input.value.trim().toLocaleLowerCase("de");
  let visible = 0;
  area.querySelectorAll("[data-search-name]").forEach(row => {
    const fields = [row.dataset.searchName, row.dataset.searchChannel, row.dataset.searchFilename];
    row.hidden = !fields.some(value => (value || "").toLocaleLowerCase("de").includes(query));
    if (!row.hidden) visible++;
    const detail = row.nextElementSibling;
    if (detail?.matches("[data-filter-detail]")) detail.hidden = row.hidden;
  });
  area.querySelectorAll("[data-filter-section]").forEach(section => {
    const count = section.querySelectorAll("[data-search-name]:not([hidden])").length;
    section.querySelectorAll("[data-filter-count]").forEach(label => {
      label.textContent = `${label.dataset.filterLabel} (${count})`;
    });
  });
  const empty = area.querySelector("[data-filter-empty]") ||
    document.querySelector(`[data-filter-empty="${input.dataset.tableFilter}"]`);
  if (empty) empty.hidden = !query || visible !== 0;
}
document.querySelectorAll("[data-table-filter]").forEach(filterTable);
document.addEventListener("input", event => {
  if (event.target.matches("[data-table-filter]")) filterTable(event.target);
});
document.querySelectorAll("[data-menu-toggle]").forEach(button => {
  button.addEventListener("click", () => {
    const open = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(open));
    document.querySelector("[data-main-menu]").classList.toggle("is-open", open);
  });
});
  const actionConfirmationTimers = new WeakMap();

  function resetActionConfirmation(button) {
    const form = button.closest("form");
    const value = form?.querySelector("[data-action-confirm-value]");
    if (value) value.value = "";
    button.classList.remove("is-confirming");
    button.dataset.actionReady = "false";
    button.setAttribute("aria-label", button.dataset.actionInitialLabel || "Aktion");
    const timer = actionConfirmationTimers.get(button);
    if (timer) window.clearTimeout(timer);
    actionConfirmationTimers.delete(button);
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action-confirm]");
    if (!button) return;
    if (button.dataset.actionReady === "true") {
      const timer = actionConfirmationTimers.get(button);
      if (timer) window.clearTimeout(timer);
      return;
    }

    event.preventDefault();
    const form = button.closest("form");
    const value = form?.querySelector("[data-action-confirm-value]");
    if (!form || !value) return;
    value.value = "true";
    button.dataset.actionReady = "true";
    button.dataset.actionInitialLabel ||=
      button.querySelector(".action-initial-label")?.textContent.trim() || "Aktion";
    button.classList.add("is-confirming");
    const prompt =
      button.querySelector(".action-confirm-label")?.textContent.trim() || "Wirklich ausführen?";
    button.setAttribute(
      "aria-label",
      `${prompt} Zum Bestätigen binnen fünf Sekunden erneut anklicken.`
    );
    actionConfirmationTimers.set(
      button,
      window.setTimeout(() => resetActionConfirmation(button), 5000)
    );
  });

let liveSubmitting = false;
let pageLeaving = false;
document.addEventListener("submit", event => {
  if (event.defaultPrevented) return;
  const path = new URL(event.target.action, location.href).pathname;
  if (["/timer/save", "/timer/delete", "/aufnahmen/delete"].includes(path) ||
      /^\/admin\/receivers\/\d+\/test$/.test(path)) {
    event.preventDefault();
    if (!liveSubmitting && !event.target.dataset.receiverActionUsed) submitReceiverAction(event.target);
    return;
  }
  liveSubmitting = true;
  pageLeaving = true;
  const button = event.target.querySelector("[data-busy-label]");
  if (button) {
    button.disabled = true;
    button.textContent = button.dataset.busyLabel;
  }
});

document.querySelectorAll("[data-user-access-form]").forEach(form => {
  const role = form.querySelector('[name="role"]');
  const mode = form.querySelector("[data-access-mode]");
  const grants = form.querySelector("[data-receiver-grants]");
  const choices = [...form.querySelectorAll("[data-receiver-access]")];
  const receiver = form.querySelector("[data-default-receiver]");
  function updateAccess() {
    const admin = role.value === "admin";
    const permissions = form.querySelector("[data-receiver-permissions]");
    permissions.hidden = admin;
    permissions.disabled = admin;
    const all = admin || mode.value !== "assigned";
    grants.hidden = all;
    choices.forEach(choice => { choice.disabled = all; });
    [...receiver.options].forEach(option => {
      const grant = choices.find(choice => choice.dataset.receiverAccess === option.value);
      option.disabled = Boolean(option.value) && !all && (!grant || grant.value === "none");
    });
    if (receiver.selectedOptions[0]?.disabled) receiver.value = "";
  }
  role.addEventListener("change", updateAccess);
  mode.addEventListener("change", updateAccess);
  choices.forEach(choice => choice.addEventListener("change", updateAccess));
  updateAccess();
});

// At most one request; slow HDDs never cause an accumulating request queue.
let liveLoading = false;
let receiverPageLoading = false;
let filterComposing = false;
document.addEventListener("compositionstart", event => {
  if (event.target.matches("[data-table-filter]")) filterComposing = true;
});
document.addEventListener("compositionend", event => {
  if (event.target.matches("[data-table-filter]")) filterComposing = false;
});
function liveBlocked() {
  const area = document.querySelector("[data-live-page]");
  return receiverPageLoading || liveSubmitting || filterComposing || document.hidden || !area ||
    document.querySelector(".is-confirming") ||
    (area.contains(document.activeElement) &&
      document.activeElement.matches("input:not([data-table-filter]), select"));
}
async function refreshLivePage() {
  if (liveLoading || liveBlocked()) return;
  const area = document.querySelector("[data-live-page]");
  if (!area.dataset.receiverId) return;
  liveLoading = true;
  try {
    const url = new URL(location.href);
    url.searchParams.delete("done");
    url.searchParams.set("live_receiver", area.dataset.receiverId);
    const directory = area.querySelector('[name="directory"]')?.value;
    if (directory) url.searchParams.set("directory", directory);
    const response = await fetch(url, {cache: "no-store", headers: {"X-Live-Refresh": "1"}});
    if (response.redirected) { location.assign(response.url); return; }
    if ([403, 409].includes(response.status)) { location.reload(); return; }
    if (!response.ok || liveBlocked()) return;
    const doc = new DOMParser().parseFromString(await response.text(), "text/html");
    const replacement = doc.querySelector("[data-live-page]");
    if (!replacement || replacement.dataset.receiverId !== area.dataset.receiverId || liveBlocked()) return;
    const history = area.querySelector(".timer-history");
    const updatedHistory = replacement.querySelector(".timer-history");
    if (history && updatedHistory) updatedHistory.open = history.open;
    const filters = new Map([...area.querySelectorAll("[data-table-filter]")]
      .map(input => [input.dataset.tableFilter, input.value]));
    const active = document.activeElement;
    const focusedFilter = area.contains(active) && active.matches("[data-table-filter]")
      ? {target: active.dataset.tableFilter, start: active.selectionStart,
        end: active.selectionEnd, direction: active.selectionDirection} : null;
    const updatedFilters = [...replacement.querySelectorAll("[data-table-filter]")];
    updatedFilters.forEach(input => { input.value = filters.get(input.dataset.tableFilter) || ""; });
    area.replaceWith(replacement);
    updatedFilters.forEach(filterTable);
    if (focusedFilter) {
      const input = updatedFilters.find(input => input.dataset.tableFilter === focusedFilter.target);
      if (input) {
        input.focus({preventScroll: true});
        input.setSelectionRange(focusedFilter.start, focusedFilter.end, focusedFilter.direction);
      }
    }
  } catch (_) {
    // A transient failure retains the last successful snapshot; retry next tick.
  } finally { liveLoading = false; }
}
window.setInterval(refreshLivePage, 5000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) refreshLivePage(); });

// Bouquet changes only read receiver data; the draft remains local until Save.
function initializeTimerSelection(root = document) {
  root.querySelectorAll("[data-timer-selection]").forEach(form => {
    const bouquet = form.querySelector("[data-timer-bouquet]");
    const sender = form.querySelector("[data-timer-service]");
    const name = form.querySelector('[name="name"]');
    const save = form.querySelector('[data-busy-label]');
    const message = form.querySelector("[data-timer-selection-message]");
    let previousSender = sender.selectedOptions[0]?.textContent || "";
    let controller;
    let loading = false;
    function updateName() {
      const next = sender.selectedOptions[0]?.textContent || "";
      if (!name.value.trim() || name.value === previousSender) name.value = sender.value ? next : "";
      previousSender = next;
    }
    sender.addEventListener("change", updateName);
    bouquet.addEventListener("change", async () => {
      controller?.abort();
      controller = new AbortController();
      const currentController = controller;
      const group = bouquet.value;
      loading = true;
      sender.disabled = true;
      save.disabled = true;
      message.textContent = "Lade Daten von Receiver...";
      try {
        const url = new URL("/timer/channels", location.origin);
        url.searchParams.set("receiver_id", form.dataset.receiverId);
        url.searchParams.set("bouquet", group);
        const headers = form.hasAttribute("data-timer-copy")
          ? {"X-Timer-Action": form.querySelector('[name="action_token"]').value} : {};
        const response = await fetch(url, {cache: "no-store", headers, signal: currentController.signal});
        if (response.redirected) { location.assign(response.url); return; }
        if (!response.ok) throw new Error("Die Senderliste konnte nicht geladen werden. Bitte das Bouquet erneut auswählen.");
        const data = await response.json();
        if (controller !== currentController || bouquet.value !== group) return;
        sender.replaceChildren(...data.services.map((service, index) => new Option(service.name, service.reference, false, index === 0)));
        if (!data.services.length) sender.add(new Option("Keine aufnehmbaren Sender verfügbar", ""));
        sender.disabled = !data.services.length;
        save.disabled = !data.services.length;
        message.textContent = data.services.length ? "" : "Dieses Bouquet enthält keine aufnehmbaren Sender.";
        updateName();
      } catch (error) {
        if (error.name !== "AbortError" && controller === currentController) message.textContent = error.message;
      } finally {
        if (controller === currentController) loading = false;
      }
    });
    form.addEventListener("submit", event => {
      if (loading || sender.disabled || !sender.value) {
        event.preventDefault();
        message.textContent = "Bitte zunächst einen verfügbaren Sender auswählen.";
      }
    });
  });
}

function initializeReceiverContent(root) {
  root.querySelectorAll("[data-table-filter]").forEach(filterTable);
  initializeTimerSelection(root);
}

async function submitReceiverAction(form) {
  const page = form.closest("[data-page-content]");
  if (!page) return;
  liveSubmitting = true;
  form.dataset.receiverActionUsed = "true";
  const data = new FormData(form);
  const button = form.querySelector("[data-busy-label]");
  if (button) { button.disabled = true; button.textContent = button.dataset.busyLabel; }
  const message = document.createElement("p");
  message.className = "notice loading-message";
  message.setAttribute("role", "status");
  message.textContent = "Lade Daten von Receiver...";
  page.prepend(message);
  try {
    const response = await fetch(form.action, {
      method: "POST", body: data, cache: "no-store", headers: {"Accept": "text/html"}
    });
    if (!form.isConnected || pageLeaving) return;
    if (response.redirected) { pageLeaving = true; location.assign(response.url); return; }
    if (!response.headers.get("Content-Type")?.includes("text/html")) throw new Error();
    const doc = new DOMParser().parseFromString(await response.text(), "text/html");
    const replacement = doc.querySelector("[data-page-content]");
    if (!replacement || !form.isConnected || pageLeaving) throw new Error();
    page.replaceWith(replacement);
    document.title = doc.title;
    initializeReceiverContent(replacement);
  } catch (_) {
    if (!form.isConnected || pageLeaving) return;
    message.className = "notice notice-error";
    message.setAttribute("role", "alert");
    message.textContent = "Keine eindeutige Antwort vom Webserver. Bitte die Liste prüfen. " +
      "Der Auftrag wird nicht automatisch wiederholt.";
    form.querySelectorAll("input, select, textarea, button").forEach(field => { field.disabled = true; });
    const path = new URL(form.action, location.href).pathname;
    const link = document.createElement("a");
    link.className = "button button-quiet";
    link.href = path.startsWith("/aufnahmen/") ? "/aufnahmen" :
      path.startsWith("/admin/") ? "/admin/receivers" : "/timer";
    link.textContent = "Liste prüfen";
    message.append(" ", link);
  } finally { if (!pageLeaving) liveSubmitting = false; }
}

async function loadReceiverPage() {
  const pending = document.querySelector("[data-receiver-load]");
  if (!pending || receiverPageLoading || liveSubmitting) return;
  receiverPageLoading = true;
  const panel = pending.querySelector("[data-loading-panel]");
  const message = pending.querySelector("[data-loading-message]");
  const retry = pending.querySelector("[data-load-retry]");
  panel.setAttribute("aria-busy", "true");
  message.textContent = "Lade Daten von Receiver...";
  retry.hidden = true;
  try {
    const response = await fetch(location.href, {
      cache: "no-store",
      headers: {"Accept": "text/html", "X-Receiver-Data": "1",
        "X-Receiver-Id": pending.dataset.receiverId}
    });
    if (response.redirected) { location.assign(response.url); return; }
    if (response.headers.get("X-Receiver-Changed") === "1") { location.reload(); return; }
    if (!response.headers.get("Content-Type")?.includes("text/html")) throw new Error();
    const doc = new DOMParser().parseFromString(await response.text(), "text/html");
    const replacement = doc.querySelector("[data-page-content]");
    if (!replacement || replacement.querySelector("[data-receiver-load]")) throw new Error();
    if (!pending.isConnected || liveSubmitting) return;
    document.querySelector("[data-page-content]").replaceWith(replacement);
    document.title = doc.title;
    initializeReceiverContent(replacement);
  } catch (_) {
    if (!pending.isConnected) return;
    panel.setAttribute("aria-busy", "false");
    message.textContent = "Die Daten konnten nicht geladen werden. Bitte die Verbindung prüfen.";
    retry.hidden = false;
  } finally { receiverPageLoading = false; }
}

document.addEventListener("click", event => {
  if (event.target.closest("[data-load-retry]")) loadReceiverPage();
});
initializeTimerSelection();
loadReceiverPage();
