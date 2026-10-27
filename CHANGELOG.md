# Histórico

## L375 V2 experimental — 27/10/2026

- Mantém **4624 mm** e deixa o campo "Verificar largura do papel antes de imprimir" oculto, como no original.
- O driver 2.60 da L375 não tem sem margem (sem campo 213, tabelas de expansão ou origem sem margem); nada a liberar.
- Atualiza por cima da L375 V1. README e relatórios atualizados para as duas impressoras.

## L3250 V7 experimental — 27/10/2026

- **Sem margem como no driver da L4260**: A4, Carta, 13×18 e 20×25 cm, e papel definido pelo usuário sem margem de 182 a 215,9 mm de largura e até 4624 mm de comprimento.
- A DLL de configuração da L3250 e a da L4260 têm código idêntico; a V7 copia as regras de sem margem do CFX da L4260 (marcas p/P, 8 regras removidas, faixa Dw/Dh/DW/DH).
- Não acrescenta mais o campo 230. Atualiza por cima da V6. Ainda não testada.

## L375 V1 experimental — 27/10/2026

- Limite do papel definido pelo usuário de 1117,6 para **4624 mm** no driver Epson L375 2.60.00.00.
- Mostrava o campo 230 achando que era sem margem; corrigido na L375 V2.

## L3250 V6 experimental — 27/10/2026

- Limite do papel definido pelo usuário de 1200 para **4624 mm** (182,05 pol.).
- Sem perfis em ProgramData, ajusta os CFX do driver no spooler; o driver regenera o cache (confirmado com REA + Ghidra).
- Atualiza por cima da V5; réguas de teste de 1500, 3000 e 4600 mm.
- 4624 mm confirmado nas preferências do driver pelo responsável.
- Acrescentava o campo 230, que é "Verificar largura do papel antes de imprimir" (não sem margem); retirado na V7.

## 23/10/2026 — marco físico de 3 metros (documentação)

- Usuário confirmou que a Epson L3250 realmente imprimiu **3000 mm**.
- Mantido o marco anterior de 1350 mm (cerca de 1,3 m) via USB; o limite original do perfil era 1200 mm.
- Documentados os obstáculos para 4000 mm e o plano de comprimento configurável, ambos ainda não validados.
- Nenhuma alteração em driver, perfis, limites, scripts, manifests ou pacotes de release.

## V5 experimental

- Aplicação em perfis CFX reconhecidos do spooler e da pasta de dados Epson.
- Backup verificado e renovação seletiva do cache E_TCXYWE.CFB.
- Preservação das correções de elevação e retorno introduzidas na V4.
- Limites métricos de 3276,7 mm e equivalente de 129,00 polegadas.
- Restauração com backup V5 e rollback em falhas.
- Impressão manual de 1350 mm informada pelo responsável.

As revisões V1–V4 foram etapas anteriores da investigação. Esta publicação distribui a V5.
