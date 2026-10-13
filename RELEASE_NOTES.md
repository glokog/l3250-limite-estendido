# Epson L3250 — V5 experimental

Ajuste do comprimento de papel para **Windows 7 x64 / PowerShell 2.0 ou superior**, com driver base Epson **3.80.05.00**.

## Downloads

- `L3250_3m_WIN7_PS2_EXPERIMENTAL_V5.zip`: pacote completo, com instalador Epson original.
- `L3250_CORRECAO_PREFERENCIAS_V5.zip`: correção menor para o driver compatível já instalado.
- `SHA256SUMS`: integridade dos ZIPs.

## Comprimento e validação

Os perfis passam de **1200 para 3276,7 mm**. O responsável confirmou uma impressão de **1350 mm via USB**. A impressão de **3000 mm continua experimental**, sem confirmação física no registro disponível.

A V5 atualiza perfis reconhecidos no spooler e na pasta de dados Epson, preserva backup e renova o cache CFB específico. Os ZIPs e seus arquivos internos foram conferidos; os pacotes originais foram mantidos sem alteração.

## Instalar e restaurar

Extraia todo o ZIP, feche aplicativos/preferências, aguarde a fila ficar vazia e execute `instalar.cmd` como administrador. Use `abrir-preferencias.cmd` para criar o tamanho e `verificar.cmd` para consultar o limite. `restaurar.cmd` desfaz o ajuste usando o backup V5.

[Guia completo](https://github.com/glokog/l3250-limite-estendido/blob/main/docs/INSTALACAO.md) · [Validação](https://github.com/glokog/l3250-limite-estendido/blob/main/docs/VALIDACAO.md)

Pacote independente e não oficial; os arquivos Epson mantêm os termos de origem.
