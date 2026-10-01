/* Contact form enhancement. Submission itself is a normal POST (works without JS). */
export function initContact() {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const feedback = document.querySelector("[data-form-errors], [data-form-success]");
  if (feedback) {
    window.setTimeout(() => {
      feedback.scrollIntoView({ block: "center" });
      feedback.focus({ preventScroll: true });
    }, 250);
  }

  const button = form.querySelector("[data-submit]");
  const label = form.querySelector("[data-submit-label]");
  form.addEventListener("submit", () => {
    if (!button || button.classList.contains("is-busy")) return;
    button.classList.add("is-busy");
    button.setAttribute("aria-busy", "true");
    if (label && form.dataset.sendingLabel) label.textContent = form.dataset.sendingLabel;
  });

  // Clear the error state of a field as soon as the user edits it.
  form.querySelectorAll(".field.has-error input, .field.has-error select, .field.has-error textarea").forEach((input) => {
    input.addEventListener(
      "input",
      () => {
        input.closest(".field")?.classList.remove("has-error");
        input.removeAttribute("aria-invalid");
      },
      { once: true }
    );
  });
}
