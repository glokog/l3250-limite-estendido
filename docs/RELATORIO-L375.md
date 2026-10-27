# Epson L375: revisão REA e pacote experimental V1

## Pacote

Foi gerado um pacote para o driver Windows x64 Epson L375 2.60.00.00. Os dois CFX regionais foram ajustados de 1117,6 mm para 4624 mm (`46240` décimos de mm e `18205` centésimos de polegada). O campo CFX 230, já presente na L375, perdeu o marcador `S="f"`; o valor padrão e o marcador de reset foram preservados. A V1 não importa os campos 213–215 da L3250.

O pacote deixa cópias dos CFX originais para restauração, confere os hashes do driver e dos perfis, atualiza os arquivos ativos e renova o cache CFB. Não substitui as DLLs da L375.

## Observações estáticas

- O INF informa `DriverVer=10/09/2025,2.60.00.00`, identifica “EPSON L375 Series” e mapeia `E_TCXN8A.CFX` / `E_TCXN8E.CFX` a `E_JC1N9A.CFX` / `E_JC1N9E.CFX`.
- O VIF associa o driver à pasta `%ProgramData%\EPSON\EPSON L375 Series` e usa `E_TCXN8E.CFB` como cache compilado.
- Nos CFX originais, o campo 230 usa o rótulo 20145 (“Métodos de expansão sem margens”), tem escolhas 0/1 e está na lista de reset. O atributo `S="f"` aparece na L375, mas não na definição comparável da L4260.
- A DLL `E_WU1MA0.DLL` contém os nomes de classe `CComboBorderlessWidthUserPaperSize`, `CRadioBorderlessSelectUserPaperSize` e `CPageBorderlessCommon`. A varredura literal não encontrou `CCheckBorderlessSelectUserPaperSize`, presente nas DLLs comparadas da L3250/L4260.
- Os campos 213–215, usados pelos CFX recentes da L3250/L4260 para controle básico e expansão, não estão declarados na L375. A versão da L375 usa configuração e classes diferentes; importar aqueles campos sem descompilação e teste de interface seria especulativo.

## Evidência REA e limites

O parser de recursos PE do REA registrou:

- Instalador L375: `ev_faced32cf996f227baceebb92b9d037c799d9d7b631892a33e91d0b893f5f51d`.
- DLL de configuração `E_WU1MA0.DLL`: `ev_a5e6735e508ba5f10d411d92829f63c6c5d2066530f6e634633f9289dfa8c45e`.
- DLL de interface `E_WI0MAE.DLL`: `ev_0c6a618ce218f215e0193929fbf23cc4c346af52deeb510c17a5a297642289b7`.
- Recursos em português `E_WI0MAE.0416.DLL`: `ev_35bc17fdf73eb62e15ef6ae2f62fd16190c20f09e5f5eecd94128fd30d26eee1`.

A busca nativa do REA não pôde descompilar a DLL: Ghidra não está configurado e o Java disponível é 17, abaixo do JDK 21 exigido; Hopper não está instalado e IDA não está configurado. A remoção de `S="f"` segue a definição da L4260 e é uma inferência estática. Ainda falta confirmar que o painel da L375 mostra a opção e que o driver aplica o modo de borda ao papel personalizado.

O [manual oficial da L375](https://files.support.epson.com/docid/cpd4/cpd43154.pdf) documenta tamanho de papel definido pelo usuário, mas não confirma a opção sem borda para papel personalizado ou impressão de 4624 mm. Não houve teste no Windows nem na impressora.

## Arquivos gerados

- Completo: `dist/L375_4624mm_BORDERLESS_EXPERIMENTAL_V1.zip` — SHA-256 `de1fcb597252e0a9c8e6fa18960830b17c279da33d49b1139f5631c707ae4da2`.
- Atualização para driver já instalado: `dist/L375_CORRECAO_PREFERENCIAS_V1.zip` — SHA-256 `f821b6581a3e2aabcdd24584cd43b7e6ea4da33b31685e04ddcb1daaa01afc82`.
- Os membros ZIP e os hashes dos CFX foram conferidos durante a geração.


## Correção posterior (27/10/2026)

O limite em polegadas estava em `18189` centésimos (181,89 in = 4620,0 mm, não 4624).
Com isso `Show-ProfileLimit` exigia ≥ 4624 mm e `verificar.cmd` sempre terminaria em código 2.
Passou a `18205` (182,05 in = 4624,07 mm). Também foi incluída a régua `teste-4600mm.pdf`
e o passo 7 do LEIA-ME (testar 3000 mm e depois 4600 mm). Os pacotes anteriores não tinham
sido publicados. Os validadores PowerShell não foram reexecutados (pwsh ausente no ambiente);
as mudanças nos scripts de instalação desde a V5 são só constantes e textos.

Novos arquivos:

- `L375_4624mm_BORDERLESS_EXPERIMENTAL_V1.zip` — SHA-256 `9dbd86069e5c2aa2ae417f70c737e420610117296be61b38f3149b1c066c0b2a`.
- `L375_CORRECAO_PREFERENCIAS_V1.zip` — SHA-256 `b3cbb3071353715d082d12650e3c0f26f609a6ebc1fef62ff2b108d84a9435a1`.
