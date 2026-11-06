// node teste.mjs: sai com erro se o porteiro quebrar
import assert from "node:assert";
import { relevantes } from "./porteiro.mjs";

const arq = ["ana-padaria.md", "oficina-tavares.md", "clinica-sorriso.md"];
assert.deepEqual(relevantes("o que falta pra Ana?", arq), ["ana-padaria.md"]);
assert.deepEqual(relevantes("status da padaria", arq), ["ana-padaria.md"]);
assert.deepEqual(relevantes("manda o relatório da Clínica", arq), ["clinica-sorriso.md"]);
assert.deepEqual(relevantes("compara oficina-tavares e ana", arq), ["ana-padaria.md", "oficina-tavares.md"]);
assert.deepEqual(relevantes("comprei banana", arq), []); // "ana" dentro de palavra não conta
assert.deepEqual(relevantes("bom dia", arq), []);
console.log("ok");
