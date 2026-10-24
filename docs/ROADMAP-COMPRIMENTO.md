# Depois dos 3 metros: 4 m e comprimento configurável

Estado em **23/10/2026**. Este documento é um plano de investigação: não altera driver, perfis, limites, firmware ou configuração da impressora e não instrui aplicar um ajuste de 4 m à V5 atual.

## O que sabemos

- O limite original dos perfis era **1200 mm**. O teste físico anterior relatado foi **1350 mm**, aproximadamente 1,3 m, via USB: não confundir esse marco com o limite original.
- O usuário confirmou em **23/10/2026** que a Epson L3250 **realmente imprimiu 3000 mm**. Os detalhes de aplicativo, resolução, conexão e método desse novo teste não foram informados.
- Os perfis V5 continuam em **3276,7 mm** no campo métrico e **129,00 polegadas (3276,6 mm)** no equivalente imperial. Assim, 4 m estão acima de ambos os valores atuais.
- **4 m não foram validados**. Comprimento arbitrário é uma hipótese de pesquisa, não promessa de imprimir tantos metros quanto se queira.

## Limites identificados e lacunas

### 1. O pacote ajusta perfis, não implementa um novo driver raster

O [manifesto](../pacote/manifest.json) fixa `patched_max_length_tenths_mm = 32767` e `patched_max_length_hundredths_inch = 12900`. Os CFX fornecidos contêm os três atributos descritos em [Funcionamento](FUNCIONAMENTO.md). O instalador aplica arquivos pré-construídos de hashes conhecidos; não há um parâmetro de comprimento livre.

DLLs, VIF, firmware e protocolo de impressão não são reescritos. Alterar um CFX isoladamente também rompe a correspondência dos hashes esperados: uma eventual versão futura precisa atualizar payloads, manifests, hashes e testes de forma coerente, preservando verificação, backup e restauração.

### 2. O limite de 16 bits da interface Windows é relevante

Na estrutura pública Windows [DEVMODEW](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-devmodew), `dmPaperLength` é um `short` com sinal em décimos de milímetro. O maior positivo é **32767**, isto é, **3276,7 mm**. Uma página de 4 m precisa representar **40000** nessas unidades: não cabe nesse campo como valor positivo. Isso é uma barreira da representação padrão, não prova do limite mecânico ou do firmware Epson.

O driver pode ter dados privados, acessados por `dmDriverExtra`, mas a existência dessa área na API não comprova que esta versão Epson aceite nela comprimentos maiores. É necessário identificar o caminho efetivamente usado, sem truncamento, overflow ou retorno silencioso ao A4. Não basta substituir 32767 por 40000 no XML ou reinterpretar o campo como sem sinal.

A função `Show-Capabilities` em [Install-L3250.ps1](../pacote/Install-L3250.ps1) lê `DC_MAXEXTENT` separando duas palavras **sem sinal** (`ToUInt16`) e verifica apenas se o comprimento anunciado é pelo menos 3000 mm. Essa consulta não prova a aceitação do DEVMODE, a escala de saída ou a impressão. Seu formato de leitura permite representar valores até 6553,5 mm, mas isso **não é um limite validado de impressão** nem supera a restrição do campo `dmPaperLength`.

### 3. Protocolo e firmware: ainda não caracterizados

O repositório não contém um emissor próprio de comandos Epson nem um rasterizador que demonstre como o comprimento total e os avanços de papel são codificados. Não há evidência aqui para afirmar qual campo/comando do protocolo limita a página, se aceita bandas contínuas ou quais são os limites do firmware. A análise futura deve identificar unidades, larguras de campos, contadores, avanço vertical e encerramento da página no caminho efetivo de saída. Não atribuir uma falha ao firmware sem isolar antes aplicativo, API e driver.

### 4. Raster, memória e fila

Para largura e resolução fixas, o número de linhas raster cresce com o comprimento; a quantidade bruta de pixels cresce com o produto das resoluções horizontal e vertical. Impressão por bandas pode reduzir o pico de memória, mas não elimina limites de coordenadas, fila, spool, transporte ou firmware. Não há código neste pacote que comprove esse processamento por bandas ou meça memória do driver.

A proteção de **64 MiB** em `L3250-Spooler.cs` limita buffers de **inventário de drivers/filas**. Ela não é um limite do raster, do trabalho de impressão ou da memória da impressora. O consumo real precisa ser medido no Windows e no aplicativo escolhidos.

### 5. Alimentação e resultado físico

O teste de 3 m demonstra um caso real, não alimentação contínua garantida. Maior comprimento exige observar tração, alinhamento, arraste, suporte do material, interrupções e precisão de escala. Não foram informados novos parâmetros físicos para prescrever material, montagem, velocidade ou resolução. Não extrapolar o teste para 30 m, nem confundir várias páginas consecutivas com uma única página contínua sem emendas.

## Plano incremental, sem aumentar limites nesta atualização

1. **Registrar a referência de 3 m.** Anotar, com o usuário, versão efetivamente instalada, aplicativo, tamanho solicitado/aceito, escala, resolução, conexão, material e comprimento medido. Preservar a configuração funcional e seu backup. O resultado já relatado permanece registrado mesmo sem esses detalhes.
2. **Investigar a passagem de 3276,7 mm.** Antes de qualquer impressão de 4 m, verificar o caminho do aplicativo ao driver, a validação/normalização do DEVMODE e eventuais dados privados. Determinar se existe uma representação suportada acima do `short` positivo e se o raster/protocolo a preserva. Se o tamanho voltar ao A4, for reduzido ou truncado, parar e localizar a camada responsável.
3. **Preparar uma versão experimental separada, somente se viável.** Em uma tarefa futura autorizada, implementar e testar a solução apropriada com valores de fronteira, conversões mm/polegadas, capacidade real, hashes, rollback e compatibilidade Win7/PS2. Se forem necessários envio raster próprio ou divisão em bandas/páginas, avaliar soluções existentes e a diferença entre continuidade real e paginação antes de desenvolver. Não sobrescrever a V5 funcional.
4. **Só então propor o teste físico de 4 m.** Com autorização e acompanhamento do usuário, usar uma referência simples de escala e marcas de comprimento, tamanho aceito sem redução, e registrar início/fim, medida física, cortes, avanços, qualidade, memória e tamanho da fila. Uma aceitação no painel, um PDF de 4 m ou um trabalho concluído no spooler não bastam: o critério é o resultado físico medido. Esta tarefa não realizou nem agendou esse teste.
5. **Parametrizar uma faixa comprovada, não “infinito”.** Depois das fronteiras técnicas e dos testes, considerar entrada de comprimento em mm/m com conversão consistente, validação numérica, teto explícito e rejeição de valores fora da faixa. Limites de aplicativo, API, protocolo, memória, fila e alimentação continuam valendo. Comprimentos maiores precisam de validação incremental própria.

**Conclusão:** o marco humano de 3 m está confirmado. O próximo objetivo é 4 m, mas a V5 atual não o oferece; primeiro é necessário resolver ou contornar corretamente a barreira de representação e validar todo o caminho. “Comprimento configurável” deve significar uma faixa explicitamente suportada, nunca uma garantia de comprimento ilimitado.
