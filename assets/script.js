const menu = document.querySelector('.menu');
const nav = document.querySelector('nav');
function setMenu(open) {
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
  nav.classList.toggle('open', open);
}
menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setMenu(false);
});
window.matchMedia('(min-width: 761px)').addEventListener('change', event => {
  if (event.matches) setMenu(false);
});
document.querySelector('#year').textContent = new Date().getFullYear();
const dialog = document.querySelector('#photo-dialog');
document.querySelectorAll('[data-image]').forEach(button => {
  button.addEventListener('click', () => {
    const image = dialog.querySelector('img');
    image.src = button.dataset.image;
    image.alt = button.dataset.caption;
    dialog.querySelector('p').textContent = button.dataset.caption;
    dialog.showModal();
    document.body.classList.add('modal-open');
  });
});
dialog.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const box = dialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
});
dialog.addEventListener('close', () => document.body.classList.remove('modal-open'));
const contactForm = document.querySelector('#contact-form');
const formStatus = document.querySelector('#form-status');
const submitButton = contactForm.querySelector('[type=submit]');
let sending = false;
async function loadContactToken() {
  const response = await fetch(contactForm.action, {
    headers: { Accept: 'application/json' }, credentials: 'same-origin', cache: 'no-store',
  });
  const data = await response.json();
  if (!response.ok || !data.token) throw new Error('Não foi possível iniciar o contato. Atualize a página ou ligue para a central.');
  contactForm.elements.token.value = data.token;
}
// O site pode continuar sendo visualizado em hospedagens estáticas; o envio requer PHP.
loadContactToken().catch(() => {});
contactForm.addEventListener('submit', async event => {
  event.preventDefault();
  if (sending) return;
  sending = true;
  submitButton.disabled = true;
  contactForm.setAttribute('aria-busy', 'true');
  formStatus.textContent = 'Enviando sua mensagem…';
  try {
    if (!contactForm.elements.token.value) await loadContactToken();
    const response = await fetch(contactForm.action, {
      method: 'POST', body: new FormData(contactForm),
      headers: { Accept: 'application/json' }, credentials: 'same-origin',
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      if (response.status === 403) contactForm.elements.token.value = '';
      throw new Error(data.message || 'Não foi possível enviar sua mensagem. Tente novamente.');
    }
    contactForm.reset();
    formStatus.textContent = data.message;
  } catch (error) {
    formStatus.textContent = error instanceof SyntaxError || error instanceof TypeError
      ? 'Não foi possível confirmar o envio. Tente mais tarde ou escreva para contato@s21.com.br.'
      : error.message;
  } finally {
    sending = false;
    submitButton.disabled = false;
    contactForm.removeAttribute('aria-busy');
  }
});
