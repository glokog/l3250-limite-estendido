> Relatorio tecnico original, anterior ao relato de impressao de 1350 mm. Consulte [a validacao atual](VALIDACAO.md) para o estado desta publicacao.

# L3250 V5: perfis em ProgramData e cache CFB

## Resultado e limite de validação

Foi produzido um instalador experimental que atualiza os perfis CFX de trabalho
na pasta de dados Epson, além dos CFX registrados no spooler, e retira o CFB
selecionado após salvar uma cópia verificada. Não foi executado no Windows do
usuário nem numa impressora. O desbloqueio efetivo permanece condicionado ao
DC_MAXEXTENT depois da aplicação, ao salvamento de 210 × 3000 mm no painel e,
se necessário, à impressão física. Não atribuir o problema ao firmware.

A carga XML de limites é idêntica à V3/V4. A diferença da V5 é a descoberta dos
perfis de execução e a invalidação seletiva do cache persistente. Não foi
introduzido `ctmver`: apenas aumentar a versão nos CFX do spooler não resolveria
um CFX diferente em ProgramData e complicaria a reversão para um CFB mais novo.

## Evidência recebida

O D1 do usuário registrou os dois CFX V3 no spooler e DLLs compatíveis com o
instalador 3.80.05.00 analisado, mas DC_MAXEXTENT de 215,9 × 1200 mm. O usuário
confirmou que reiniciou e que o limite continuou. D1 não inspecionou os perfis
de ProgramData nem o CFB. DocumentProperties voltou para A4 inclusive para
1200 mm: a consulta DEVMODE não isolou uma recusa específica de 3000 mm.

## Análise estática local

As referências abaixo são VA preferidas (image base 0x180000000), observadas
com objdump e o leitor PE local `l3250/inspect_native_local.py`, não evidências
de execução nem saídas de decompilador REA. Os providers profundos REA estavam
indisponíveis; não foi alegada decompilação ou execução do driver no Linux.

Alvos preservados:

- Config DLL `E_WU1YA0.DLL` / instalada `E_YUICYWE.DLL`, SHA256
  `6335cd6ab5ea8e826b57e333764d0f24a19e972a4b119dc90e27eace333ec8b8`.
- VIF `E_WM1YWE.VIF` / instalado `E_YVIFYWE.VIF`, SHA256
  `1179402f182daa5c5e309014aef51bb0f693aaafcafcb138428f61c78a9a292e`.

Cadeia relevante:

1. VIF `[CommonDrvInfo]`: `DriverNameForInstall="EPSON L3250 Series"`,
   `CFGXFile=E_TCXYWE.CFX`, variantes W/E e A/A, `CFGBFile=E_TCXYWE.CFB`.
   VIF intacto em `l3250/data-expanded`; conteúdo decodificado em `.vif.txt`.
2. `0x1801df828` consulta id 0x2b (DriverNameForInstall) e chama `0x180086834`.
   Essa rotina usa `SHGetSpecialFolderPathW` com id 0x23, acrescenta `EPSON` e
   o nome de instalação do driver. Evidência: `vif-directory.asm` e
   `profile-paths.asm`. Caminho resultante usual no Win7:
   `C:\ProgramData\EPSON\EPSON L3250 Series`.
3. `0x1801e0bc0`, arquivo `vif-path.asm`: ids 1..3 (incluindo CFGXFile)
   resolvem no diretório de dados; id 0x12 (CFGBFile) acrescenta `ConvBinData`.
   Consequentemente o alvo de cache limitado é
   `...\ConvBinData\E_TCXYWE.CFB`.
4. `0x1800a83bc`, `profile-file-source.asm`: abre CFB e CFX e compara versões.
   `0x1800a1ccc`, `profile-version.asm`, lê a versão CFB no DWORD de offset
   0x2c do cabeçalho; para XML procura `ctmver="` nos primeiros 256 bytes.
   Ausência de atributo produz versão zero. CFX originais/V3 não o contêm.
5. `0x1800a8c5e`..`0x1800a8c79`: quando ambas as versões são válidas, só
   seleciona XML por versão se XML > CFB. Sem CFB, seleciona XML. `0x1800a8d13`
   carrega binário, `0x1800a8e29` carrega XML, `0x1800a8f79` e virtual +0x40
   convertem e gravam cache em condições adequadas.
6. Há também preferência possível por `EPCFGXFileInfo/EPCFGXFileData`, lidos
   via GetPrinterDataW, dependendo de versão e flags. A V5 não apaga esses
   dados. Sua presença no computador do usuário ainda é desconhecida.
7. A cadeia de DC_MAXEXTENT chega a `0x1800891fc`, com limites obtidos do
   perfil e possíveis condicionais adicionais. Não foi demonstrado um único
   imediato 12000 que devesse ser alterado numa DLL. As DLLs ficam intactas.

Conclusão: há base estática concreta para corrigir a localização do ajuste e
regenerar o cache. Ainda não é prova de que esse cache seja a única causa no
computador do usuário, nem prova de impressão de uma folha de três metros.

## Implementação

- Verifica identidade de duas DLLs e do VIF antes de alterar arquivos.
- Aceita somente hashes de CFX original, V1/V2 ou V3/V4/V5 conhecidos.
- Inclui CFX existentes no diretório exato de dados; exige o perfil base
  E_TCXYWE.CFX antes de qualquer transação. Não cria perfis desconhecidos.
- Salva originais de fábrica e bytes anteriores à transação em backups.
- Exige filas vazias, para spooler, aplica CFX, verifica todos os hashes e
  salva/retira apenas E_TCXYWE.CFB. Não limpa UCB, USB ou outros modelos.
- Rejeita caminhos de dados/cache redirecionados por reparse point.
- Cache permanece preservado se falhar a cópia ou a verificação do backup.
  Falha ao retirar cache desfaz os CFX que foram alterados na transação.
- Restauração V5 devolve CFX originais e invalida cache atual com backup;
  falha antes de concluir devolve os CFX aos bytes anteriores à restauração.
- Perfis não reconhecidos num driver já encontrado interrompem, sem abrir
  automaticamente o instalador Epson como tentativa de correção.
- Códigos 0/1/2 e correção de processo elevado da V4 preservados.
- Após aplicar, consulta DC_MAXEXTENT e registra o estado do cache novamente.

## Validação

Testes de integração em PowerShell moderno no Linux. Serviços, inventários,
UAC e retorno de capacidade Windows são simulados; operações de arquivo são
reais. Não confundir esses testes com execução no Windows 7/PowerShell 2.0.

- `tools/validate_l3250_win7.ps1`: parser, restrições PS2, hashes, estruturas
  nativas, manifesto, substituição atômica, rollback, inventários e filas.
- `tools/validate_l3250_exit.ps1`: 11 cenários de saída, incluindo elevação
  cancelada, retorno ausente, falha de encerramento e limite pendente.
- `tools/validate_l3250_cache.ps1`: 10 cenários da entrada real do instalador:
  instalação, repetição sem alterações CFX pendentes, retirada de cache
  negada, hash desconhecido, perfil ausente, VIF diferente, fila ocupada,
  restauração, falha na restauração e cache redirecionado. Confere backup
  CFB byte a byte e preservação de USB.
- Builder verifica hashes do instalador, payloads, XML e integridade ZIP.

Logs: `l3250/validation-v5-installer.txt`, `validation-v5-exit.txt`,
`validation-v5-cache.txt`. Hashes de entrega: `l3250/package-build-win7-v5.json`.

Referências Microsoft para a interpretação do diretório compartilhado:
[CSIDL e FOLDERID_ProgramData](https://learn.microsoft.com/en-us/windows/win32/shell/csidl),
[caminho típico C:\ProgramData](https://learn.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables),
[constante 0x0023 no código .NET](https://referencesource.microsoft.com/mscorlib/microsoft/win32/win32native.cs.html).
Essas fontes esclarecem a API Windows; a seleção dos arquivos Epson decorre
da análise local descrita acima.
