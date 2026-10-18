# Convenant BIOS Tools — aplicativo nativo

**Versão 0.2.0: janela própria em Qt Widgets, aberta por executável. Não usa navegador, WebView ou servidor HTTP.**

- **[Baixar Windows x64 — executável portátil](downloads/Convenant-BIOS-Tools-0.2.0-Windows-x64.zip?raw=true)**
- **[Baixar CachyOS x64 — executável portátil](downloads/Convenant-BIOS-Tools-0.2.0-CachyOS-x64.tar.gz?raw=true)**

## Windows 10/11 x64

1. Baixe e extraia **todo** o ZIP do Windows.
2. Abra **Convenant-BIOS-Tools.exe**. Mantenha `runtime`, `tools` e os demais arquivos juntos dele. Não precisa instalar Python.
3. Para acessar o chip, copie sua pasta completa do FPT compatível para `tools/FPT` ou selecione `fptw64.exe` pela janela do programa.

## CachyOS x86-64

Extraia o pacote TAR.GZ do CachyOS e abra **Convenant-BIOS-Tools**. O pacote inclui Python, Qt e suas bibliotecas; não precisa instalar pacotes Python. Alternativamente:

```bash
./Convenant-BIOS-Tools
```

Para acessar o controlador interno, são necessários `flashrom` e `polkit` do sistema. O programa solicita autorização somente nas operações de hardware.

## Recursos

Identificação da plataforma; backups de BIOS, descriptor, SPS e chip completo quando permitido; duas leituras e comparação de hashes; análise UEFI e microcódigos; comparação de bytes separada da NVRAM; extração da região BIOS; gerador experimental de microcódigos para a base 002; gravação restrita da BIOS com backups prévios e conferência posterior.

A versão 006 e perfis desconhecidos continuam bloqueados para gravação. Não há apagamento integral, gravação de descriptor/SPS ou opção de força. O programa analisa BINs do CH341, mas não controla o NeoProgrammer. Nenhum FPT, backup de usuário ou dado de placa acompanha os pacotes.

[Manual completo](docs/convenant-bios-tools.md) · [Verificação dos pacotes](downloads/SHA256SUMS-0.2.0.txt) · [Testes nativos](docs/evidencias/convenant-native-validation.json)

Os testes de interface e do executável Linux foram realizados sem acesso físico à flash. O Windows foi compilado e suas dependências conferidas; sua execução nativa ainda precisa ser validada no Windows. Não houve gravação física nem teste de boot/desempenho.

## Código-fonte

```bash
python3 -m pip install -r requirements-native.txt
python3 convenant_bios_tools.py
```

Os arquivos particulares ficam em `dados-convenant/`, ignorada pelo Git. A versão 0.1.0 nos downloads é histórica e usava navegador; use a 0.2.0. O site da S21 na raiz do repositório permanece independente.
