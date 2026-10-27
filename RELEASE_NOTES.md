# Epson L3250 — V7 experimental (4624 mm + sem margem como na L4260)

**Windows 7 x64 · PowerShell 2.0 ou superior · driver Epson 3.80.05.00**

- Papel definido pelo usuário até **4624 mm**.
- **Sem margem igual ao driver da L4260**: A4, Carta, 13×18 e 20×25 cm, além de 9×13, 10×15, 100×148 e 16:9; papel definido pelo usuário sem margem de **182 a 215,9 mm de largura** e **257 a 4624 mm de comprimento**.
- A DLL de configuração da L3250 e a da L4260 têm código idêntico (seções iguais byte a byte); a V7 copia do CFX da L4260 as marcas de tamanho sem margem, retira 8 regras que bloqueavam esses tamanhos e acrescenta a faixa de sem margem do papel do usuário. As tabelas de expansão da margem continuam as da L3250.
- Atualiza por cima da V6. Não altera DLLs, registro, assinaturas ou DriverStore.

**Situação:** ainda não testada no Windows nem impressa. No driver original a Epson só libera sem margem na L3250 até 10,16 cm de largura; o responsável já imprimia sem margem mais largo na L3250 usando o driver da L4260. Observe se aparecem manchas de tinta no verso do papel.

Pacote independente e não oficial; os arquivos Epson mantêm os termos de origem.
