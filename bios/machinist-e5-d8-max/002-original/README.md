# Machinist E5-D8 Max — componentes originais da BIOS 002

**Origem: BIOS do proprietário, X99D8 Ver:002 de 20/12/2022. Nenhum componente foi extraído da BIOS 006.**

[Baixar componentes originais em ZIP](E5-D8-MAX-001b-Componentes-Originais.zip?raw=true) · [Manifesto com offsets e hashes](manifesto.json) · [SHA-256 dos arquivos](SHA256SUMS.txt)

## Conteúdo

| Parte | Tamanho | Intervalo absoluto no chip SPI |
| --- | --- | --- |
| Descriptor Intel original | 4 KiB | 0x000000–0x000FFF |
| Região ME/SPS original | 8.384.512 bytes | 0x001000–0x7FFFFF |
| Dois volumes de NVRAM originais | 512 KiB | 0x800000–0x87FFFF |
| Volume BootFV original | 2.490.368 bytes | 0xDA0000–0xFFFFFF |

O ZIP inclui também 17 arquivos FFS identificados de CPU, plataforma e apoio à memória: 11 SEC/PEI e seis DXE. Os módulos separados compartilham conteúdo com o BootFV; não se deve concatená-los para construir uma ROM. Há instruções e hashes de cada componente dentro do arquivo.

Todos os BIN/FFS são fatias exatas do backup `CH341-BKP-Bios-Machinist-E5-D8-Max - 001b_ORIGINAL.rom`, preservadas sem atualização de microcódigo ou alteração de configurações. O pacote publicado é idêntico ao entregue ao proprietário.

## Verificações realizadas

- Descriptor idêntico ao extraído por FPT.
- Quatro volumes UEFI e 309 arquivos FFS, sem erros de checksum ou descompressão detectados pelos analisadores utilizados.
- Quatro microcódigos com checksum válido. O microcódigo v4 permanece em 0B000038 e o 306F2 em 3D.
- Hash do módulo BUP do SPS correspondente ao manifesto.
- Código da BIOS idêntico ao das duas leituras internas de 8 MiB; 154 bytes diferentes apenas na área de NVRAM.
- Cada componente exportado conferido byte a byte com a origem; hashes e integridade do ZIP verificados.

Persistem avisos do analisador sobre ACM não interpretado e um identificador JEDEC da tabela VSCC desconhecido. Não foram validados todos os módulos do SPS, nem demonstrada a autenticidade do chip inteiro. Não houve teste de restauração e ainda falta comparar outra leitura completa independente.

## Uso e limites

Material de preservação e análise, publicado por solicitação expressa do proprietário. A recomendação de privacidade no LEIA-ME original do ZIP antecede essa solicitação. NVRAM e SPS contêm dados específicos da unidade e não são modelos genéricos para outras placas.

Não foi isolado e validado um MRC independente nem provado que os módulos selecionados contêm todo o código ou todas as dependências de CPU/memória. O BootFV inclui outros módulos e dados para preservar o contêiner original.

**Este pacote não é uma imagem completa de 16 MiB pronta para gravação, não é uma atualização e não comprova compatibilidade de transplante para a BIOS 006 ou outra placa.** Os arquivos do aplicativo Convenant BIOS Tools e o site S21 são independentes deste material.
