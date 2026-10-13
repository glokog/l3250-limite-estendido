# Funcionamento do ajuste V5

## Perfis

O driver base usa os perfis `E_TCXYWE.CFX` e `E_TCXYWA.CFX`. A V5 aplica três mudanças em cada perfil reconhecido:

| Atributo XML | Original | V5 |
| --- | --- | --- |
| F[f=7]/E[e=261]@K | 12000 | 32767 |
| F[f=11]/E[e=0]/V@x | 12000 | 32767 |
| F[f=13]/E[e=0]/V@x | 4724 | 12900 |

Nos campos métricos, os valores representam décimos de milímetro: **1200 → 3276,7 mm**. O campo em polegadas passa a **129,00 in**, equivalente a 3276,6 mm. Os demais bytes dos perfis permanecem preservados.

A mudança abrange o comprimento; não aumenta a largura declarada de 215,9 mm.

## Aplicação e cache

A investigação da V5 identificou os perfis de trabalho e o cache persistente:

```text
C:\ProgramData\EPSON\EPSON L3250 Series\E_TCXYWE.CFX
C:\ProgramData\EPSON\EPSON L3250 Series\E_TCXYWA.CFX
C:\ProgramData\EPSON\EPSON L3250 Series\ConvBinData\E_TCXYWE.CFB
```

O script confere a identidade de duas DLLs e do VIF, aceita apenas hashes CFX conhecidos e exige o perfil de trabalho necessário. Com filas vazias e spooler parado, salva backup, atualiza os CFX, verifica os arquivos e preserva/retira somente o cache CFB selecionado. O driver pode então regenerar o cache a partir dos perfis.

Falhas na transação acionam restauração dos bytes anteriores quando aplicável. A reversão V5 usa o backup preservado. A rotina não altera DLLs, INF, catálogos, DriverStore, firmware ou preferências USB.

A estrutura e os hashes estão em [manifest.json](../pacote/manifest.json). Os scripts estão em [pacote](../pacote/); a análise estática detalhada está no [relatório original V5](RELATORIO-V5.md).

## Limite de interpretação

O teto do perfil, a resposta de capacidade do Windows e o comprimento realmente impresso são medidas diferentes. A confirmação física disponível é **1350 mm via USB**. A V5 continua experimental para 3000 mm; não fornece uma solução validada de página contínua de 30 metros.
