# claude-memoria-por-cliente

Memória por cliente para o [Claude Code](https://claude.com/claude-code), sem banco, sem API e sem gastar token.

*[English below](#english)*

Quem atende vários clientes com o Claude Code esbarra sempre no mesmo problema: ou você enfia tudo num arquivo gigante que ele lê toda vez, ou separa por cliente e ele não sabe qual abrir. Este repositório resolve com duas peças pequenas:

- **`porteiro.mjs`**: um hook `UserPromptSubmit`. Antes de o Claude responder, ele lê o seu pedido e, se aparecer o nome de um cliente que tem arquivo em `_memoria/clientes/`, avisa o Claude para ler esse arquivo. Os gatilhos vêm do nome do arquivo: `ana-padaria.md` dispara com "ana", "padaria" ou "ana-padaria". Ele ignora acento e maiúscula. Cliente novo é só criar o arquivo.
- **`mapa.py`**: lista as ligações `[[nome]]` entre os arquivos de memória e aponta os **órfãos**, arquivos em que nenhum outro arquivo aponta e que por isso ficam esquecidos. Com `--html`, gera um grafo interativo.

Uso isso todo dia na operação da minha agência no Rio, com mais de 20 clientes.

## Como usar

1. Copie `porteiro.mjs` para a raiz do seu projeto.
2. Crie `_memoria/clientes/` com um `.md` por cliente (nome em minúsculas, com hífen).
3. Registre o hook em `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "node \"${CLAUDE_PROJECT_DIR}/porteiro.mjs\"", "timeout": 5 } ] }
    ]
  }
}
```

4. Reabra o Claude Code. Pergunte "o que falta pra padaria?" e ele já abre o arquivo certo.

Para usar outra pasta, defina `MEMORIA_DIR` (ex.: `docs/clientes`).

Mapa:

```
python mapa.py                 # resumo no terminal
python mapa.py --html          # gera mapa.html
python mapa.py --raiz exemplo  # roda na pasta de exemplo
```

Requisitos: Node 18+ e Python 3.8+. Não tem dependência para instalar (o HTML do mapa carrega o d3 por CDN).

## Testar

```
node teste.mjs
```

A pasta `exemplo/` traz um projeto pronto com três clientes fictícios. Abra o Claude Code dentro dela para ver o porteiro funcionando.

---

## English

Per-client memory for Claude Code. No database, no API calls, zero tokens spent on lookup.

- **`porteiro.mjs`** ("doorman") is a `UserPromptSubmit` hook. If your prompt mentions a client that has a file in `_memoria/clientes/`, it tells Claude to read that file before answering. Triggers come from the file name (`ana-padaria.md` matches "ana", "padaria" or "ana-padaria"), accent and case insensitive. A new client is just a new file.
- **`mapa.py`** ("map") lists the `[[name]]` links between memory files and flags **orphans**, files nothing links to, which is how memory gets forgotten. `--html` renders an interactive graph.

Setup: copy `porteiro.mjs` to your project root, create `_memoria/clientes/*.md`, register the hook as shown above, restart Claude Code. Set `MEMORIA_DIR` to use a different folder. Run `node teste.mjs` for the self-check, and open Claude Code inside `exemplo/` for a working demo.

MIT license.
