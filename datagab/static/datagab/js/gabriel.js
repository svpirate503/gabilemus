const nav = document.getElementById("nav");
const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 4);
onScroll();
window.addEventListener("scroll", onScroll, { passive: true });

const form = document.getElementById("contact-form");
const panel = document.getElementById("contact-panel");
const status = document.getElementById("form-status");
const send = form.querySelector(".send");

const clearErrors = () => {
  form.querySelectorAll(".field").forEach((field) => field.classList.remove("is-invalid"));
  form.querySelectorAll(".field-error").forEach((node) => { node.textContent = ""; });
  status.textContent = "";
};

const showErrors = (errors) => {
  Object.entries(errors).forEach(([field, message]) => {
    const note = form.querySelector(`[data-for="${field}"]`);
    const input = form.elements[field];
    if (note) note.textContent = message;
    if (input && input.closest) input.closest(".field")?.classList.add("is-invalid");
    if (field === "form") status.textContent = message;
  });
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  send.classList.add("is-loading");
  send.textContent = "Sending";
  try {
    const response = await fetch(form.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
        "Accept": "application/json",
      },
      body: new FormData(form),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      showErrors(payload.errors || { form: "The message could not be sent." });
      if (window.turnstile) turnstile.reset();
      return;
    }
    panel.classList.add("is-sent");
    panel.querySelector(".success").hidden = false;
    form.reset();
  } catch (error) {
    status.textContent = "The message could not be sent. Try again in a moment.";
    if (window.turnstile) turnstile.reset();
  } finally {
    send.classList.remove("is-loading");
    send.textContent = "Send message";
  }
});
