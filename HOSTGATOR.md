# Publicação na HostGator

O site usa HTML/CSS/JavaScript e PHP 8.2 ou superior para enviar o formulário. Não precisa de banco de dados ou Composer. GitHub Pages não executa PHP.

1. No cPanel, selecione PHP 8.2 ou superior para o domínio e habilite HTTPS.
2. Envie `index.html`, as pastas `assets/` e `images/`, `contato.php` e `contato-config.php` para a pasta do domínio (geralmente `public_html/`). Mantenha a estrutura. Não envie `.git/`, testes ou outros arquivos de desenvolvimento. Faça backup de um site existente antes de substituí-lo.
3. Crie/confirme uma caixa de e-mail real no domínio hospedado. Edite `contato-config.php`: `sender` deve ser uma caixa desse domínio autorizada pela HostGator, e `recipient` é o endereço que receberá as mensagens. Ambos estão inicialmente como `contato@s21.com.br`, seguindo o endereço do site. **Se hospedar em outro domínio, ajuste o remetente.** Atualize também os contatos visíveis no HTML caso necessário.
4. No cPanel, confira o roteamento de e-mail e os registros SPF/DKIM recomendados pela hospedagem. Se o domínio usa e-mail em outro provedor, ajuste o roteamento conforme as orientações da HostGator.
5. Abra o site por HTTPS, preencha o formulário e confira a caixa de entrada e o spam do destinatário. Responder à mensagem deve direcionar a resposta ao e-mail do visitante.

O formulário usa `mail()` do PHP e o transporte local da hospedagem. Não coloca senha de e-mail no código. Se `mail()` estiver bloqueado no seu plano, será necessário configurar envio por SMTP autenticado; solicite os parâmetros à HostGator e guarde a senha fora do repositório. Não desative verificações de TLS.

O retorno de sucesso significa que o servidor aceitou encaminhar a mensagem; não garante a entrega na caixa de entrada. O teste de entrega só pode ser concluído depois da publicação e da configuração de e-mail do domínio.

## Comportamento e proteção

- Validação de dados e consentimento no PHP, assunto limitado às opções do formulário e destinatário fixo.
- Remetente do domínio; endereço do visitante somente no `Reply-To`, com proteção contra injeção de cabeçalhos.
- Token de sessão, cookies HttpOnly/SameSite e campo invisível para reduzir spam. O navegador precisa de JavaScript e cookies.
- Até cinco tentativas válidas por IP a cada 15 minutos, inclusive falhas de envio. Não é proteção completa contra ataques distribuídos.
- Limite de tentativas em arquivos temporários, sem gravar o conteúdo do contato. PHP precisa de diretórios temporários e de sessão graváveis, normalmente já disponíveis na hospedagem. Não use permissões 777.
- Em caso de falha, os campos ficam preenchidos para nova tentativa. Para emergências, o visitante é orientado a ligar.

## Desenvolvimento local

Com PHP instalado, execute na raiz do projeto:

```sh
php -S 127.0.0.1:8000 -t .
```

O servidor Python ou uma hospedagem estática servem o visual, mas não processam o formulário. Para validar sintaxe: `php -l contato.php`, `php -l contato-config.php` e `node --check assets/script.js`. Não execute testes de envio usando uma caixa real sem autorização.
