# Validação e resultados conhecidos

## Resultado físico informado

O registro anterior do projeto informa que o responsável aplicou a **V5** na Epson L3250 conectada por **USB** e imprimiu **1350 mm**, superando os **1200 mm** originais. Esse relato não confirmou impressão de 3 metros.

## Validações do desenvolvimento original

Os registros preservados descrevem testes em PowerShell moderno no Linux, com operações reais de arquivo e simulações de serviços, inventário, UAC e capacidades Windows.

- Parser, restrições de compatibilidade PS2, manifest, hashes, estruturas nativas, substituição atômica e rollback.
- Onze cenários de saída, incluindo elevação cancelada, retornos ausentes e limite pendente.
- Dez cenários de perfis/cache: instalação, repetição, retirada de cache negada, hash desconhecido, perfil ausente, VIF diferente, fila ocupada, restauração, falha de restauração e cache redirecionado.
- Verificação byte a byte do backup CFB e preservação das configurações USB.
- Integridade dos ZIPs, identidade do instalador original e limites XML.

O [relatório original V5](RELATORIO-V5.md) foi escrito antes da confirmação manual. Sua declaração de que não houve teste na impressora descreve aquele momento da investigação.

## Conferência para esta publicação

Os dois ZIPs foram preservados sem alteração e novamente conferidos por SHA-256 e CRC. Os hashes de todos os arquivos internos foram comparados com o `SHA256SUMS.txt` de cada pacote. As identidades CFX, os três atributos alterados e a cópia do instalador original foram conferidos com o manifesto.

| Arquivo | Bytes | SHA-256 |
| --- | --- | --- |
| L3250_3m_WIN7_PS2_EXPERIMENTAL_V5.zip | 72231692 | `a3b6ba5ae0b8f2f778986499ac912dc6402ae1ce73b283b520203c84ce867dbe` |
| L3250_CORRECAO_PREFERENCIAS_V5.zip | 52347 | `52339ec3922a9355f8b096fb47a196b3a8d97d1bbffd9e24be2ee19a4693a290` |

Nenhuma impressora ou instalação Windows foi modificada durante esta publicação.

## Pendências

A execução automatizada em Windows 7/PowerShell 2.0 e a impressão física de 3000 mm não foram demonstradas pelos testes Linux. Outros drivers, modelos, sistemas e conexões não foram validados. O teto configurado não garante o comportamento do firmware ou de todos os aplicativos de impressão.

O manifesto do pacote mantém o estado original de build experimental. O relato manual posterior está registrado nesta página e no README.
