# BIOS 002 com logo Covenant — experimental

[Baixar o ZIP](E5-D8-MAX-002-LOGO-COVENANT-EXPERIMENTAL.zip?raw=true) · [SHA-256 do ZIP](SHA256SUMS.txt)

**Sua base original X99D8 Ver:002 de 20/12/2022, com alteração somente do logo. Nenhum componente veio da BIOS 006.**

![Prévia do logo inserido](previa-logo.png)

## Arquivos no ZIP

- `E5-D8-MAX-002-LOGO-COVENANT-EXPERIMENTAL-SPI-16MiB.bin`: imagem completa do chip, 16.777.216 bytes.
- `E5-D8-MAX-002-LOGO-COVENANT-EXPERIMENTAL-BIOS-8MiB.bin`: somente a região BIOS, 8.388.608 bytes.
- Logo BMP de 568 × 317 pixels, prévia PNG, FFS do logo, manifesto, verificação independente, hashes e LEIA-ME.

Os dois BINs têm escopos diferentes. O de 8 MiB não substitui uma imagem completa do chip de 16 MiB; o de 16 MiB não serve para uma operação que espera somente a região BIOS.

## Mudança e verificação

A arte enviada pelo proprietário foi reduzida proporcionalmente e convertida em BMP RGB de 24 bits, sem corte ou geração de novos elementos. O novo logo foi colocado no espaço livre confirmado do mesmo volume UEFI. Um PAD vazio ocupa o slot antigo; os outros módulos mantêm seus endereços. O inventário passa de 309 para 310 FFS devido a essa entrada PAD adicional.

Descriptor, SPS, NVRAM, FIT, volume de inicialização e os outros 308 FFS foram preservados byte a byte. Todos os microcódigos permanecem originais: o v4 continua em **0B000038** e o 306F2 em **3D**. Esta versão não inclui a atualização 49/040 preparada separadamente.

A candidata passou na análise UEFI e descompressão sem novos erros. O logo foi extraído novamente e comparado byte a byte ao BMP preparado; a imagem também foi decodificada com um segundo leitor. O arquivo de 8 MiB é exatamente a região BIOS do arquivo de 16 MiB. Permanecem os avisos preexistentes sobre ACM não interpretado e um identificador JEDEC desconhecido na tabela VSCC. O BUP do SPS mantém o hash correspondente ao manifesto; os demais módulos SPS não foram todos validados.

## Limites

**Experimental: sem teste de boot, exibição na placa, verificação de assinaturas ou gravação física.** Os testes estáticos não garantem inicialização nem apresentação do logo. Guardar o backup original e confirmar outra leitura completa independente continua recomendado.

O ZIP contém dados específicos da unidade de origem, inclusive NVRAM e SPS, e foi publicado por solicitação do proprietário. Não é uma BIOS universal para outras placas de mesmo nome. O Convenant BIOS Tools 0.2 usa perfis restritos e pode recusar esta variante porque o logo altera o fingerprint; não contornar as verificações.

O pacote publicado é idêntico ao entregue na conversa. Os componentes originais continuam disponíveis [na pasta 002-original](../002-original/README.md).
