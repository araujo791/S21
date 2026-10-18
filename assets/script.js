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
document.querySelector('#contact-form').addEventListener('submit', event => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const body = `Nome: ${data.get('nome')}\nEmpresa: ${data.get('empresa') || 'Não informada'}\nE-mail: ${data.get('email')}\nTelefone: ${data.get('telefone')}\n\n${data.get('mensagem')}`;
  const url = 'mailto:contato@s21.com.br?subject=' + encodeURIComponent('Contato S21 — ' + data.get('assunto')) + '&body=' + encodeURIComponent(body);
  document.querySelector('#form-status').textContent = 'Mensagem preparada. Conclua o envio no seu aplicativo de e-mail. Se ele não abrir, escreva para contato@s21.com.br.';
  window.location.href = url;
});
