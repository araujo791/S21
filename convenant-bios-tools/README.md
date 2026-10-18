# Convenant BIOS Tools

Ferramenta portátil para Windows e CachyOS: identificação, backups, análise e comparação de firmware, geração experimental de microcódigos para a base 002 e gravação restrita da região BIOS com verificações.

**[Baixar Convenant BIOS Tools 0.1.0 — Windows + CachyOS (ZIP, 16 MB)](downloads/Convenant-BIOS-Tools-0.1.0-Windows-CachyOS.zip?raw=true)**

O ZIP inclui Python portátil para Windows e UEFIExtract para os dois sistemas. Não contém FPT, backups de BIOS ou dados de placas de usuários.

## Windows

1. Baixe e extraia todo o ZIP do programa.
2. Copie sua pasta completa do Intel FPT compatível para `tools/FPT`, incluindo `fptw64.exe` e seus arquivos auxiliares da mesma versão.
3. Abra **Abrir-Convenant-BIOS-Tools.bat**. A interface abre no navegador local; não precisa instalar Python.

## CachyOS

Na pasta extraída:

```bash
bash abrir-convenant-bios-tools.sh
```

Requer Python 3.10 ou posterior. Para operações no chip, também são necessários flashrom e polkit:

```bash
sudo pacman -S --needed python flashrom polkit
```

## Verificações e limites

- Backups de BIOS (8 MiB), descriptor (4 KiB), SPS e chip completo (16 MiB), conforme permissões do controlador.
- Duas leituras por operação, sem sobrescrever backups anteriores.
- Comparação de hashes, bytes e bits, separando o código da NVRAM.
- UEFIExtract, checksums FV/FFS e microcódigos; teste limitado do hash BUP SPS em imagens reconhecidas.
- Gravação somente da região BIOS, em perfis 002 conhecidos, com preparação, confirmação e leitura posterior.
- A versão 006 e perfis desconhecidos não estão liberados para gravação. A ferramenta não força acesso ao SPS, não grava descriptor/SPS e não controla o NeoProgrammer.

Passaram 26 testes automatizados e oito verificações de navegador no Linux. A execução nativa no Windows, a gravação física, o boot e ganhos de desempenho não foram testados. A candidata com microcódigos é experimental. Análise estática não certifica recuperação integral.

[Manual completo](docs/convenant-bios-tools.md) · [Evidência dos testes](docs/evidencias/convenant-validation.json) · [SHA-256 do pacote](downloads/SHA256SUMS.txt)

## Código-fonte

Esta pasta contém somente os componentes da ferramenta. O site existente na raiz do repositório permanece independente. Para executar a partir do código com Python instalado:

```bash
python3 convenant_bios_tools.py
```

Para a experiência portátil com runtime e analisadores incluídos, use o ZIP acima. Os arquivos locais ficam em `dados-convenant/`, ignorada pelo Git.
