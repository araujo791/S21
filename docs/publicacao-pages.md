# Reconfigurar a publicação do GitHub Pages

O site e o histórico foram preservados. O workflow `.github/workflows/pages.yml` publica os arquivos estáticos da branch `main` sem o build Jekyll automático. Ele pode ser executado manualmente e substitui execuções anteriores do mesmo workflow.

## Ativação pelo proprietário

1. No repositório, abra **Settings → Pages → Build and deployment**.
2. Em **Source**, selecione **GitHub Actions** no lugar de **Deploy from a branch**. Essa configuração não pode ser aplicada por um `git push`.
3. Em **Actions → Publicar site S21**, selecione **Run workflow → main → Run workflow**.
4. Confirme que os jobs `build` e `deploy` terminaram com sucesso antes de considerar a publicação concluída.

Se a interface oferecer **Unpublish site**, é possível retirar a publicação antiga antes de executar o fluxo novo; o endereço ficará indisponível até a nova publicação terminar. Isso não apaga o código. Não exclua o repositório e não reescreva seu histórico para tentar corrigir uma fila de execução.

A nova configuração não cancela uma execução antiga administrada pelo GitHub nem garante contornar uma indisponibilidade da plataforma. Se o novo workflow também permanecer em fila, registre no suporte do GitHub os links das execuções. Não crie sucessivos commits apenas para gerar novas tentativas.

## Formulário

GitHub Pages não executa PHP. O envio do formulário depende da publicação na HostGator, conforme `HOSTGATOR.md`. O artefato do Pages contém apenas o HTML, CSS, JavaScript e imagens; não publica o processador PHP nem sua configuração. Não use o Pages para testar entrega de e-mail.
