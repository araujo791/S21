# Convenant BIOS Tools 0.2.0 — nativo

Aplicativo desktop Qt Widgets para Windows 10/11 x64 e CachyOS x86-64. Abre uma janela própria, sem navegador, WebView ou servidor HTTP. A versão 0.2.0 substitui a interface web da 0.1.0.

## Abrir

**Windows:** extraia todo o ZIP e abra `Convenant-BIOS-Tools.exe`. Não mova o EXE sozinho: mantenha `runtime`, `tools` e os arquivos do aplicativo na mesma pasta. Python e Qt já acompanham o programa. Para operações no chip, copie sua pasta completa do FPT compatível para `tools/FPT`, com `fptw64.exe` e arquivos auxiliares da mesma versão, ou use o botão de seleção na janela. O FPT não é redistribuído. O EXE não tem assinatura digital de editor; nenhuma proteção do Windows é desativada automaticamente.

**CachyOS:** extraia todo o TAR.GZ e abra `Convenant-BIOS-Tools`, mantendo `_internal` e `tools` juntos dele. O formato preserva os links entre bibliotecas do Linux. O Python e Qt estão incluídos. Se o gerenciador de arquivos não preservar a permissão de execução:

```bash
chmod +x Convenant-BIOS-Tools
./Convenant-BIOS-Tools
```

O binário usa bibliotecas Linux empacotadas e depende do ambiente gráfico e de uma glibc compatível do sistema; o alvo é CachyOS atualizado, não todas as distribuições Linux. Para acessar o controlador SPI:

```bash
sudo pacman -S --needed flashrom polkit
```

A interface funciona sem iniciar como administrador. Cada operação de hardware usa um processo separado e solicita autorização do sistema. A análise de arquivos não precisa de privilégios.

## Usar a janela

1. **Visão geral:** identifica placa, BIOS, CPU(s) e memória. Nenhuma leitura da flash ocorre ao iniciar.
2. **Backups:** consulta chip/permissões e faz duas leituras de BIOS (8 MiB), descriptor (4 KiB), SPS ou SPI completa (16 MiB). O acesso depende do descriptor; Error 26 é reportado sem uso de força.
3. **Analisar e comparar:** selecione arquivos pela janela nativa. Confere volumes, FFS, microcódigos e descompressão com UEFIExtract. Em SPI reconhecida, verifica o hash BUP do SPS. Compara hashes, bytes e bits; a comparação do código exclui os primeiros 512 KiB de NVRAM. Extrair BIOS apenas copia a região, sem reparar dados.
4. **Microcódigos:** selecione duas leituras BIOS próprias idênticas e as referências Intel fixadas. O gerador aceita apenas o código 002 revisado, preserva NVRAM e outros códigos, atualiza 306F2 para 49 e 406F1 para 0B000040 e gera candidata e manifesto experimentais. As referências não são baixadas automaticamente nem redistribuídas. Revisão Intel: bdc92abe5c499c3fd7988b76a128d05c9120a520, caminhos intel-ucode/06-3f-02 e intel-ucode-with-caveats/06-4f-01.
5. **Gravar BIOS:** somente região de 8 MiB e família de código 002 conhecida. A preparação faz dois backups atuais, exige igualdade e análise UEFI detalhada. A janela mostra o hash e alterações de NVRAM. Para confirmar, marque a declaração e digite `GRAVAR BIOS`. A preparação expira em dez minutos. O processo elevado verifica novamente a imagem e os backups, faz uma leitura atual e exige que coincida com a preparação. Depois de gravar, outra leitura deve coincidir byte a byte com a candidata.
6. **Ferramentas e arquivos:** selecione FPT, salve BINs, abra a pasta local e exporte o relatório JSON. Logs e detalhes ficam no painel inferior.

As bases 006 e desconhecidas não estão liberadas para gravação por esta versão. Não há gravação do descriptor/SPS, apagamento integral ou comandos arbitrários. O nome comercial da placa, presença de microcódigo e checksums não comprovam todas as revisões físicas. O programa não controla CH341/NeoProgrammer, mas analisa as capturas BIN produzidas por eles.

## Dados, erros e limites

Os arquivos permanecem em `dados-convenant`, junto do executável. `files` guarda BINs, metadados e relatórios; `jobs` guarda backups, logs e resultados de cada operação. Backups anteriores não são sobrescritos. A pasta é ignorada pelo Git e não entra no ZIP publicado.

A análise estática não garante boot, estabilidade ou recuperação integral. O teste SPS cobre somente o hash BUP em layout reconhecido, sem autenticar sua assinatura ou todos os módulos. A igualdade entre duas leituras não basta para certificar integridade. O aviso ACM do UEFIExtract permanece no relatório.

Não feche, desligue ou reinicie durante gravação. Se uma gravação ou a verificação falhar, preserve os logs e mantenha a máquina ligada. Não há restauração automática. O FPT pode ser impedido de carregar pelo Windows; a aplicação registra a falha sem desativar antivírus, integridade de memória, Secure Boot ou outras proteções.

Os testes usam capturas locais privadas e um controlador simulado para as escritas. O executável Linux foi aberto e verificado; o EXE Windows foi compilado como PE GUI e suas dependências foram conferidas, sem execução nativa nesta máquina Linux. Não houve gravação física nem teste de boot ou desempenho. Nenhum firmware privado está incluído nos pacotes.

## Desenvolvimento e compilação

Instale `requirements-native.txt` e execute `python3 convenant_bios_tools.py`. Para testes de janela sem monitor, use `QT_QPA_PLATFORM=offscreen`. As classes com firmware real exigem `MACHINIST_BIOS_BASE`; o teste de geração também requer `INTEL_UCODE_306F2` e `INTEL_UCODE_406F1`. Sem arquivos, esses casos são explicitamente ignorados.

Os scripts `compilar-exe-windows.py` e `empacotar-nativo.py` recebem diretórios e componentes explícitos. `requirements-build-native.txt` fixa Qt, PyInstaller e Zig. O Windows usa um lançador C compilado com Zig e runtime Python/Qt portátil. O Linux usa PyInstaller em modo diretório, com bibliotecas substituíveis. UEFIExtract acompanha ambos os pacotes. Os componentes e licenças de terceiros estão registrados em `licenses` e no manifesto SHA-256.

Para compilar o Linux, inclua como dado o arquivo `scripts/atualizar-microcodigo.py` no diretório `scripts`, usando caminho absoluto no argumento `--add-data` quando `--specpath` estiver fora do projeto. Nunca inclua `dados-convenant`, `inputs` ou firmware de usuário no empacotamento.
