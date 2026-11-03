# Recursos gráficos da BIOS enviada como Wagner

**242 imagens originais, extraídas dos bancos Images-A/B/C e preservadas byte a byte.**

- [Baixar todas as imagens, catálogo e prévias em ZIP](Wagner-Recursos-Graficos-Originais.zip?raw=true).
- [Abrir o catálogo visual com seis folhas numeradas](CATALOGO.md).
- [Abrir a pasta de imagens originais](imagens/).
- [Inventário com dimensões, hashes e posições nos bancos](inventario.json) · [CSV](catalogo.csv) · [Hashes](SHA256SUMS.txt).

As imagens vêm do arquivo `CA23-GABRIEL-24mhz-BIOSPORTOKNOWIN-JS11V1.0-JWAGNERVAZ.rom` enviado pelo usuário. O Setup da imagem contém `X99D4JWAGNER`. Não foram incluídos a ROM completa, NVRAM, Descriptor, ME/SPS nem executáveis EFI.

## Por onde começar a edição

O [fundo de 1024 × 576](imagens/1024x576-b8410dd03f0a4281.jpg) contém o cabeçalho X99 e o texto TECHNOLOGY. O [fundo Classic de 1920 × 1080](imagens/1920x1080-5b69ebfb18c44077.jpg) contém a moldura vermelha. Outros elementos são sobrepostos pela interface; use as folhas numeradas para localizar ícones, botões e faixas.

O nome exibido pode vir de uma imagem ou de texto do firmware. `X99D4JWAGNER` foi identificado como string no módulo Setup; alterar as imagens não modifica essa string. Não foi confirmado em qual recurso ou caminho de renderização aparece cada parte da marca na tela em execução. As imagens publicadas não tiveram nomes, textos ou marcas removidos nesta etapa.

## Como guardar sua edição

Faça uma cópia do original e mantenha o nome do arquivo para identificar a imagem de origem. Preserve largura/altura, formato PNG/JPEG e transparência, quando presente. Guarde as edições separadas dos originais para podermos comparar e conferir o tamanho final. O sufixo de hash no nome identifica o arquivo original; uma edição terá outro hash.

O pacote serve para editar recursos gráficos. **Ainda não há adaptação funcional da interface para a Machinist 002, e editar as imagens não as reinsere automaticamente na BIOS.** Índices, comprimentos dos bancos, compressão, dados e callbacks ainda precisam ser tratados na integração.

As folhas são apenas miniaturas de consulta. Os arquivos em imagens/ têm os bytes originais e foram conferidos com os hashes e dimensões do inventário da extração.
