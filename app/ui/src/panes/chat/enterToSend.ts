/**
 * Enter sends the chat message; Shift+Enter adds a line. Enter while
 * characters are being composed (an input method choosing a character)
 * belongs to that, and sends nothing. The form's own submit handler
 * (sendMessage.ts) skips empty text, and the input is disabled while a
 * message is being sent, so neither needs a check here.
 */

export function installEnterToSend(
  input: HTMLTextAreaElement,
  form: HTMLFormElement,
): void {
  input.addEventListener("keydown", (event) => {
    // Safari reports the Enter that ends composing as keyCode 229.
    const composing = event.isComposing || event.keyCode === 229;
    if (event.key !== "Enter" || event.shiftKey || composing) return;
    event.preventDefault();
    form.requestSubmit();
  });
}
