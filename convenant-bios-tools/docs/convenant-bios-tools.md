# Convenant BIOS Tools

Ferramenta portátil local para Windows x64 e CachyOS x86-64. A versão 0.1 reúne leitura do chip, análise, comparação e gravação restrita da região BIOS da Machinist E5-D8 Max. Não há conta, telemetria ou envio de firmware para servidores externos.

## Abrir no Windows

1. Extraia **todo** o ZIP para uma pasta gravável, fora da pasta compactada.
2. Copie sua pasta completa do Intel FPT para `tools/FPT`, mantendo `fptw64.exe` e seus arquivos auxiliares da mesma versão. Apenas uma cópia é detectada automaticamente; se houver várias, escolha o caminho na aba Ferramentas.
3. Dê dois cliques em **Abrir-Convenant-BIOS-Tools.bat**. O pacote de distribuição inclui Python portátil; não precisa instalar Python ou pacotes pip.
4. A interface abre no navegador padrão. Mantenha a janela do lançador aberta. A autorização de administrador é solicitada ao iniciar cada operação de hardware.

O Intel FPT não é redistribuído aqui. Use sua cópia legítima e compatível com a plataforma. O programa não desativa antivírus, integridade de memória, Secure Boot ou bloqueios de drivers do Windows. Se o driver não carregar, o erro fica no log.

## Abrir no CachyOS

Na pasta extraída:

```bash
bash abrir-convenant-bios-tools.sh
```

Requer Python 3.10 ou posterior e navegador. Para operações de hardware, requer `flashrom` e `pkexec`/polkit. Se estiverem ausentes:

```bash
sudo pacman -S --needed python flashrom polkit
```

O lançador não precisa ser executado como root. Somente o processo responsável pelo hardware solicita elevação. O pacote inclui UEFIExtract para Linux x86-64 e Windows x64; os motores FPT e flashrom precisam estar disponíveis separadamente.

## Operações

| Área | Comportamento |
|---|---|
| Identificação | Modelo DMI, BIOS, CPU(s), memória; consulta do chip e permissões pelo motor selecionado |
| Backup BIOS | Duas leituras da região de 8 MiB, comparação SHA-256, análise estrutural e UEFIExtract |
| Backup completo | Duas tentativas de leitura dos 16 MiB; acesso negado é reportado, sem uso de força ou preenchimento artificial |
| Descriptor | Duas leituras de 4 KiB, conferência de mapa e permissões |
| SPS | Duas leituras da região isolada, quando o controlador permitir; integridade completa do SPS não é certificada |
| Análise de BIN | FV/FFS, microcódigos Intel, identificação, perfil e extração UEFI; em SPI completa, teste limitado do hash do BUP FTPR SPS |
| Comparação | Hashes, bytes e bits diferentes; comparação de BIOS separada da NVRAM e possibilidade de comparar região de 8 MiB com SPI de 16 MiB |
| Extração BIOS | Copia os 8 MiB indicados pelo descriptor, sem reparar o conteúdo |
| Microcódigos | Gerador experimental existente: 306F2/49 e 406F1/040 somente no código 002 revisado, com duas leituras idênticas e referências Intel de hash fixado |
| Gravação | Apenas BIOS de 8 MiB, com perfil conhecido 002, placa identificada E5-D8 Max, preparação, confirmação explícita e leitura posterior |

### Gravação

A preparação identifica a placa, consulta o motor, preserva duas leituras atuais idênticas e exige análise UEFI detalhada aprovada. A confirmação mostra hash e se a NVRAM será alterada. É necessário marcar a confirmação e digitar `GRAVAR BIOS`.

Antes de escrever, o processo elevado repete as verificações de tamanho, perfil, placa, hashes dos backups e candidata. Uma nova leitura deve coincidir com os backups da preparação. A preparação expira em dez minutos. Depois da gravação, uma nova leitura deve coincidir byte a byte com a candidata.

Não há gravação do descriptor/SPS, apagamento integral, desbloqueio genérico, comandos arbitrários ou opções de força. A variante 006 e outros perfis desconhecidos podem ser analisados, mas não gravados por esta versão. Isso decorre da compatibilidade ainda não demonstrada, incluindo o relato de falha v4 na conversa, e não apenas do número da versão.

O perfil 002 original já funcionou na máquina de referência; a candidata com microcódigos atualizados continua experimental, sem boot ou desempenho medidos. O nome da placa e a análise estática não comprovam todas as revisões físicas. Disponha de recuperação confiável antes de gravar. A ferramenta não testa nem controla CH341/NeoProgrammer; aceita os arquivos capturados por eles para análise.

## Arquivos e encerramento

Os arquivos ficam em `dados-convenant`, ao lado do lançador. Há `files` (BINs adicionados, metadados e relatórios) e `jobs` (backups originais, logs e resultados por operação). Saídas anteriores não são sobrescritas. Também é possível baixar arquivos pela interface. Relatórios JSON podem ser exportados no painel de resultados.

Os BINs podem conter identificadores, configurações e dados particulares da placa. Essa pasta é ignorada pelo Git e nunca incluída no pacote público. Nenhum backup fornecido na conversa acompanha o ZIP.

Use **Encerrar ferramenta** após a operação. Não feche, reinicie ou desligue durante uma gravação. Se houver falha de gravação/verificação, mantenha a máquina ligada e preserve o log; não há tentativa automática de restauração.

## Limites de validação

Os testes automatizados usam arquivos de referência locais e motores de hardware simulados. Testes de navegador exercitam a interface e os fluxos de análise/comparação. Não foram realizadas gravações na placa física. A execução nativa do Windows e suas solicitações UAC devem ser verificadas na máquina do usuário; a construção e os testes desta entrega ocorrem em Linux.

Um checksum correto ou duas leituras iguais não garantem recuperação integral. A verificação do SPS cobre somente o hash do BUP em um layout reconhecido; não autentica a assinatura do manifesto nem todos os seus módulos. O aviso ACM do UEFIExtract é mantido no relatório. Uma captura rejeitada não é reparada automaticamente.

## Desenvolvimento e pacote

O código usa somente a biblioteca padrão do Python. Para iniciar sem abrir o navegador:

```bash
python3 convenant_bios_tools.py --no-browser --data /tmp/convenant-dev
python3 -m unittest discover -s tests -p 'test_convenant.py' -v
```

Os testes com firmware real exigem `MACHINIST_BIOS_BASE` apontando para uma leitura própria válida de 8 MiB; sem isso, essa classe é marcada como ignorada, e os testes independentes continuam.

Para empacotar, use `scripts/empacotar-convenant.py --help`. O script recebe os três arquivos oficiais de runtime/analisadores, confere hashes fixados, copia somente uma lista explícita de fontes e gera manifesto SHA-256. Não baixa nem inclui FPT, microcódigos Intel ou firmware de usuário. As licenças de Python, UEFITool e seus avisos acompanham o ZIP.
