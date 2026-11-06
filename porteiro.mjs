#!/usr/bin/env node
// Porteiro: hook UserPromptSubmit do Claude Code.
// Le o prompt (stdin) e, se citar um cliente que tem arquivo em
// _memoria/clientes/, injeta "leia _memoria/clientes/X.md" no contexto.
//
// Os gatilhos saem do nome do arquivo, nada fica fixo no codigo:
// "ana-padaria.md" vira "ana-padaria", "ana" e "padaria". Qualquer um acerta.
//
// Pasta configuravel pela variavel MEMORIA_DIR (padrao: _memoria/clientes).
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

export function normalizar(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export function gatilhos(nomeArquivo) {
  const slug = nomeArquivo.replace(/\.md$/, "");
  const partes = slug.split("-").filter((p) => p.length >= 3); // ignora "de", "os"
  return [slug, ...partes].map(normalizar);
}

export function relevantes(prompt, arquivos) {
  const p = normalizar(prompt);
  const palavras = new Set(p.split(/[^a-z0-9-]+/).filter(Boolean));
  return arquivos.filter((a) =>
    gatilhos(a).some((g) => palavras.has(g) || (g.includes("-") && p.includes(g)))
  );
}

function main() {
  let payload;
  try {
    payload = JSON.parse(readFileSync(0, "utf-8"));
  } catch {
    return;
  }
  const prompt = payload.prompt || "";
  if (!prompt.trim()) return;

  const raiz = process.env.CLAUDE_PROJECT_DIR || payload.cwd || process.cwd();
  const pastaRel = process.env.MEMORIA_DIR || "_memoria/clientes";
  let arquivos;
  try {
    arquivos = readdirSync(join(raiz, pastaRel)).filter((f) => f.endsWith(".md"));
  } catch {
    return;
  }

  const achados = relevantes(prompt, arquivos);
  if (!achados.length) return;

  const lista = achados.map((f) => `${pastaRel}/${f}`).join(", ");
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: `Relevante: leia ${lista} antes de responder (o porteiro detectou esse cliente no prompt).`,
      },
    })
  );
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/").split("/").pop())) {
  main();
}
