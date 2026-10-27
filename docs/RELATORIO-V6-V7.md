# L3250 V6: sem borda e limite de 4624 mm

## Resultado

O pacote experimental V6 foi gerado para Windows 7 x64 / PowerShell 2.0. Nos dois CFX regionais da L3250, ele:

- aumenta os limites de comprimento de 1200 mm para 4624 mm (`46240` décimos de mm; `18205` centésimos de polegada);
- adiciona o campo CFX 230, “Borderless Enlargement Methods”, e seu marcador de reset, conforme a estrutura da L4260;
- preserva os binários originais da L3250 e aceita os hashes do CFX original e da V5 na atualização.

## Observações estáticas

- Os campos 213, 214 e 215 já existem no CFX L3250 e correspondem aos controles básicos de sem borda e expansão. Suas definições comparadas com o CFX L4260 são idênticas.
- O campo 230, rótulo de recurso 20145, só foi encontrado no CFX L4260. Ele tem duas escolhas (0 e 1) e consta também na lista de reset. Nenhuma linha `<P>` do CFX L4260 referencia diretamente o campo 230.
- A DLL de configuração L3250 e a da L4260 contêm os mesmos nomes de classe relacionados a papel personalizado sem borda, incluindo `CComboBorderlessWidthUserPaperSize` e `CPageBorderlessCommon`. Isso vem de uma busca literal nos bytes; não demonstra que essas rotinas sejam executadas para qualquer tamanho de papel.
- Os CFX V6 gerados mantêm as definições básicas 213–215 e acrescentam o campo 230 e o reset. Não alteram a DLL da impressora.

## Evidência REA e limites

O parser de recursos PE do REA examinou os instaladores e as DLLs de recursos. IDs de evidência relevantes:

- Instalador L4260: `ev_152dfd1d1e944cb3a3b627e97e50ac2babef2f21b9455973c983b0a779e5d7cc`.
- Recursos da DLL de interface L4260 (`E_WI0YEE.DLL`): `ev_d1de28684f4782ea4b89fa22d5ef5e95e4e8c4c32766536006e23a88c2f97e1c`.
- Recursos da DLL de interface L3250 (`E_WI0YEE.DLL`): `ev_9770519b9a485c067016300c6500b537b3565363c16183d24a1cda34d4ee92ba`.
- A análise PE anterior da DLL de configuração L4260 (`E_WU1YA0.DLL`) registrou `ev_a9332bb2278fbda840e434008fc2993d41f3975b0dbec323cfb7f18183059031`.

A descompilação nativa não ficou disponível: Ghidra não está configurado e o Java instalado é 17, enquanto o provedor exige JDK 21 ou superior; Hopper não está instalado e IDA não está configurado. Por isso, a presença do campo 230 no painel depois da instalação e seu efeito em tempo de execução permanecem por confirmar no Windows.

## Limites de uso

A Epson documenta sem borda na L3250 para papel fotográfico 4 × 6 pol. (102 × 152 mm). A presença do controle no driver não comprova sem borda em papel longo. O manual da [L3250](https://files.support.epson.com/docid/cpd6/cpd60185.pdf) lista essa restrição; a página de [especificações da L3250](https://files.support.epson.com/docid/cpd6/cpd61841/source/specifications/references/l3250/spex_paper_spc_l3250.html) também traz o limite de mídia personalizada do produto.

O valor de 4624 mm foi aplicado ao limite configurável solicitado. A impressão física em 4624 mm e a nova opção de ampliação sem borda ainda não foram testadas. O usuário informou que a L3250 já imprimiu em 3 m na versão anterior.

## Pacotes gerados

- Completo: `dist/L3250_4624mm_WIN7_PS2_EXPERIMENTAL_V6.zip` — SHA-256 `b6bfa033d53831bd89f12a06409a085dbca30ae18959b9eb4b449c57ccbed19d`.
- Atualização para driver já instalado: `dist/L3250_CORRECAO_PREFERENCIAS_V6.zip` — SHA-256 `d9df009e4f326a467957893d6bb4c589677fe4f6fa0a9d3e83ca2291519c037f`.
- Os dois arquivos foram abertos após a geração, seus membros ZIP passaram a verificação de integridade, e os hashes dos CFX coincidem com o manifesto.


## Correção posterior (27/10/2026)

O limite em polegadas estava em `18189` centésimos (181,89 in = 4620,0 mm, não 4624).
Com isso `Show-ProfileLimit` exigia ≥ 4624 mm e `verificar.cmd` sempre terminaria em código 2.
Passou a `18205` (182,05 in = 4624,07 mm). Também foi incluída a régua `teste-4600mm.pdf`
e o passo 7 do LEIA-ME (testar 3000 mm e depois 4600 mm). Os pacotes anteriores não tinham
sido publicados. Os validadores PowerShell não foram reexecutados (pwsh ausente no ambiente);
as mudanças nos scripts de instalação desde a V5 são só constantes e textos.

Novos arquivos:

- `L3250_4624mm_WIN7_PS2_EXPERIMENTAL_V6.zip` — SHA-256 `8bd6a0da82c40cee4156494ef2292ed508ef580006250bb1cfe4e3bdc9ed279d`.
- `L3250_CORRECAO_PREFERENCIAS_V6.zip` — SHA-256 `ed31e69613639089ecbb0c47445a65913f1d8e9606d78d77e875f103a1730e02`.

## Perfil ausente em ProgramData (27/10/2026, REA + Ghidra 12.1.4)

Log do usuário (Win7 SP1, PS 2.0): CFX do spooler encontrados, `C:\ProgramData\EPSON\EPSON L3250 Series\E_TCXYW?.CFX` ausentes; o V6 abortava em `Assert-RuntimeProfiles`.

Decompilação REA de `E_WU1YA0.DLL` (sha256 6335cd6a…):
- `FUN_1800a83bc` (ev_f72abac0…): abre CFB (id 0x12) e CFX de dados (id 1). Se **ambos** faltam, abre id **0x15** (`local_108 = 1`), carrega o XML e grava um CFB novo em `ConvBinData` (`FUN_1801daabc` cria a pasta se `GetFileAttributesW` falhar). Se só o CFB existe, ele é usado sem consultar o CFX do spooler.
- `FUN_1801dfd20` (ev_95095f7e…): ids 1, 0x15, 0x17 e 0x36 → `[CommonDrvInfo] CFGXFile`.
- `FUN_1801e0bc0`: id 0x15 cai no ramo `"%s%s"` com `param_1[3]`; `FUN_1801df828` (ev_c25806f0…) preenche `param_1[3]` via `FUN_1801dfaec` (ev_6de15d87…), que divide o caminho do VIF em drive+diretório. Portanto id 0x15 = `<pasta do VIF no spooler>\E_TCXYWE.CFX`.
- As três chamadas de `CopyFileW` (ev_ada63fa9…) tratam `EPAUDF01.AUD` e `trace.log`; nenhuma copia CFX para ProgramData.

Conclusão: sem perfis em ProgramData, ajustar os CFX do spooler e retirar o CFB é suficiente para o driver regenerar o cache com 4624 mm. O instalador V6 (e o L375 V1, por analogia, sem análise REA própria) passou a seguir esse caminho e lista a pasta EPSON no log.

## V7: sem margem como na L4260 (27/10/2026)

- `.text`, `.data`, `.pdata`, `.rsrc` e `.reloc` de `E_WU1YA0.DLL` da L3250 (6335cd6a…) e da L4260 (529c4423…) são idênticos byte a byte; a diferença de comportamento vem só do CFX.
- Correção de rótulo: o campo 230 (r=20145) é **"Check Paper Width Before Printing"** nas strings de `E_WI0YEE.DLL` (decodificadas via REA `inspect_pe_resources`), não um método de sem margem. A V6 o acrescentou por engano; a V7 não o inclui.
- Sem margem no CFX: campo 213 (Borderless), 214 (Expansion), 215 (Enlargement Methods), tabelas `<BD>` por classe `p/P` e a origem `se/sr` "Rear Feed-Borderless". A L3250 só liberava 89–101,6 mm (9x13, 10x15, 100x148, 16:9).
- V7 copia da L4260: `p="2" P="2"` em A4, Carta, 13x18 e 20x25 (campos 9 e 35), retira as 8 regras `<P>` que proibiam 213=1 nesses tamanhos e acrescenta `Dw="1820" Dh="2570" DW="2159" DH="46240"` ao papel definido pelo usuário. As tabelas `<BD>` continuam as da L3250. O usuário informou que já imprimia sem margem na L3250 usando o driver da L4260.

## L375 V2

O CFX da L375 2.60 não define o campo 213, não tem `<BD>`, nem `p/P`, nem `se/sr`; só presets ocultos (`S="f"`) mencionam 213. Não há sem margem a liberar. A V1 tinha retirado `S="f"` do campo 230 achando que era sem margem; a V2 mantém o campo oculto como no original e só aplica o limite de 4624 mm (aceita CFX original e V1).

## V8 e L375 V3 (27/10/2026)

- **L3250 V8:** marca `p/P` (classe 1 para 9x13, 10x15 e 100x148; classe 2 para os demais) em todos os tamanhos alimentáveis dos campos 9 e 35, exceto os maiores que a impressora (`L="t"`) e o definido pelo usuário; remove todas as regras `<P>` com `213=1` e tamanho (campo 9 ou 35); papel do usuário sem margem com `Dw/Dh` iguais ao mínimo do driver (54 × 86 mm) até 215,9 × 4624 mm. Aceita CFX original, V6 e V7 (o manifesto passou a aceitar mais de um hash anterior, separados por `;`).
- **L375:** os dados ESC/P-R da Epson (`epson-inkjet-printer-escpr` 1.8.8) listam 0 tamanhos sem margem para a L375, 4 para a L3250 e 8 para a L4260. Mesmo assim, a UI da L375 (`E_WI0MAE.DLL`, decodificada via REA `inspect_pe_resources`) tem a caixa "Borderless" (2793) e o botão de expansão (2794) na tela Principal, e as opções "Borders/Borderless" (6306/6307) no papel do usuário; a DLL de configuração contém `CPageBorderlessCommon`, `CRadioBorderlessSelectUserPaperSize` e os nomes `BD/BE/Dw/DH/se/sr`. `C1/C2` são "PrinterCapsInk1/2" e `PC` é "PrinterCapsCommon" (id 0x40), não verificado bit a bit.
- **L375 V3:** copia do CFX da L4260 (`z="103"`, igual ao da L375) `BE/BD`, campos 213–215 (sem o `m="38"` do 213) e suas entradas de reset; origem 261 ganha `se="292" sr="87"` ("Rear Feed-Borderless", string 2487) e `Dw/Dh/DW/DH` (89 × 127 até 215,9 × 4624 mm); `p/P` em todos os tamanhos alimentáveis. Aceita CFX original, V1 e V2. Não testada: o firmware pode aceitar, ignorar ou imprimir além da borda sem absorvedor.
