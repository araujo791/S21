const menu=document.querySelector('.menu'),nav=document.querySelector('nav');
menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Fechar menu':'Abrir menu');nav.classList.toggle('open',open);});
nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{menu.setAttribute('aria-expanded','false');nav.classList.remove('open');}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'){menu.setAttribute('aria-expanded','false');nav.classList.remove('open');}});
const serviceIds=[4,8,3,5,7,1,6,2];
document.querySelectorAll('[data-service]').forEach(a=>{a.href='https://s21emergencia.com.br/site/servicos-interna.php?servico='+serviceIds[Number(a.dataset.service)];a.target='_blank';a.rel='noopener';});
document.querySelector('form').addEventListener('submit',e=>{e.preventDefault();const d=new FormData(e.currentTarget);const body=`Nome: ${d.get('nome')}\nE-mail: ${d.get('email')}\nTelefone: ${d.get('telefone')}\n\n${d.get('mensagem')}`;location.href='mailto:contato@s21.com.br?subject='+encodeURIComponent('Contato pelo site S21')+'&body='+encodeURIComponent(body);document.querySelector('#form-status').textContent='Conclua o envio no seu aplicativo de e-mail. Se ele não abrir, escreva para contato@s21.com.br.';});
