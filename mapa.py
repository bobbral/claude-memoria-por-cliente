"""
Mapa da memoria: varre _memoria/ e CLAUDE.md, extrai os links [[nome]]
entre arquivos e monta um grafo. Roda local, sem gastar token.

Um arquivo sem nenhum link chegando nele (orfao) e memoria solta no disco:
nada aponta pra ela, entao o Claude dificilmente vai abrir.

Uso (de dentro do projeto, ou com --raiz):
    python mapa.py               # resumo no terminal
    python mapa.py --html        # tambem gera mapa.html (grafo visual)
    python mapa.py --json        # tambem grava mapa.json
    python mapa.py --raiz ./exemplo
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path.cwd()
LINK_RE = re.compile(r"\[\[([a-z0-9-]+)\]\]")

SCAN_DIRS = ["_memoria"]
EXTRA_FILES = ["CLAUDE.md"]


def slug(path: Path) -> str:
    """id do no no grafo: nome do arquivo sem extensao"""
    return path.stem


def coletar_arquivos():
    arquivos = []
    for d in SCAN_DIRS:
        p = ROOT / d
        if p.exists():
            arquivos.extend(p.rglob("*.md"))
    for f in EXTRA_FILES:
        p = ROOT / f
        if p.exists():
            arquivos.append(p)
    return arquivos


def categoria(path_rel: str) -> str:
    """categoria do no, so pelo caminho do arquivo, pra colorir e descrever no grafo"""
    if path_rel == "CLAUDE.md":
        return "sistema"
    if path_rel.startswith("_memoria/clientes/"):
        return "cliente"
    return "nucleo"


DESCRICAO_CATEGORIA = {
    "nucleo": "Memória central do negócio",
    "cliente": "Cliente ou produto",
    "sistema": "Regra de operação (CLAUDE.md)",
}


def montar_grafo():
    arquivos = coletar_arquivos()
    nos = {}  # slug -> path relativo
    links = []  # (origem, destino)

    for f in arquivos:
        s = slug(f)
        nos[s] = str(f.relative_to(ROOT)).replace("\\", "/")

    for f in arquivos:
        origem = slug(f)
        texto = f.read_text(encoding="utf-8", errors="ignore")
        for destino in LINK_RE.findall(texto):
            links.append((origem, destino))

    recebidos = {s: 0 for s in nos}
    for origem, destino in links:
        if destino in recebidos:
            recebidos[destino] += 1

    orfaos = sorted(s for s, c in recebidos.items() if c == 0)

    return {"nos": nos, "links": links, "orfaos": orfaos}


def imprimir_resumo(grafo):
    print(f"{len(grafo['nos'])} arquivos, {len(grafo['links'])} links\n")
    for origem, destino in sorted(grafo["links"]):
        alvo = grafo["nos"].get(destino, "??? (link quebrado)")
        print(f"  {origem} -> {destino}  ({alvo})")

    print(f"\n{len(grafo['orfaos'])} arquivo(s) sem nenhum link apontando pra ele:")
    for s in grafo["orfaos"]:
        print(f"  - {grafo['nos'][s]}")


def gerar_html(grafo, destino: Path):
    grau = {s: 0 for s in grafo["nos"]}
    for o, d in grafo["links"]:
        if o in grau:
            grau[o] += 1
        if d in grau:
            grau[d] += 1

    nos_js = json.dumps(
        [
            {
                "id": s,
                "path": p,
                "orfao": s in grafo["orfaos"],
                "grau": grau[s],
                "cat": categoria(p),
                "desc": DESCRICAO_CATEGORIA[categoria(p)],
            }
            for s, p in grafo["nos"].items()
        ],
        ensure_ascii=False,
    )
    links_js = json.dumps(
        [{"source": o, "target": d} for o, d in grafo["links"] if d in grafo["nos"]],
        ensure_ascii=False,
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Mapa da memoria</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
  html, body {{ margin:0; height:100%; background:#060608; overflow:hidden; }}
  body {{ font-family:-apple-system,system-ui,sans-serif; }}
  svg {{ width:100vw; height:100vh; cursor:grab; }}
  svg:active {{ cursor:grabbing; }}
  .link {{ stroke:#2a2a30; stroke-width:1px; transition:opacity .15s; }}
  .link.hi {{ stroke:#6b6b78; }}
  .node circle {{
    stroke:#060608; stroke-width:1.5px; transition:opacity .15s, filter .15s;
  }}
  .node text {{
    fill:#9a9aa4; font-size:10.5px; paint-order:stroke;
    stroke:#060608; stroke-width:3px; pointer-events:none;
    opacity:0; transition:opacity .15s;
  }}
  .node.hi text, .node.vizinho text, .node:hover text {{ opacity:1; fill:#e8e8ee; }}
  .node.hi circle {{ filter:drop-shadow(0 0 6px currentColor); }}
  .node.dim circle {{ opacity:0.10; }}
  .node.dim text {{ opacity:0; }}
  .link.dim {{ opacity:0.04; }}
  .hint {{
    position:fixed; top:14px; left:16px; color:#6a6a74; font-size:12px;
    font-family:-apple-system,system-ui,sans-serif; line-height:1.6;
  }}
  .legenda {{ display:flex; gap:14px; margin-top:6px; flex-wrap:wrap; }}
  .legenda span {{ display:inline-flex; align-items:center; gap:5px; }}
  .dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
  #tooltip {{
    position:fixed; pointer-events:none; background:#131318; color:#e8e8ee;
    border:1px solid #2a2a32; border-radius:8px; padding:9px 12px;
    font-size:12.5px; max-width:260px; opacity:0; transition:opacity .1s;
    box-shadow:0 8px 24px rgba(0,0,0,.4); z-index:10;
  }}
  #tooltip b {{ display:block; font-size:13.5px; margin-bottom:2px; }}
  #tooltip .cat {{ font-size:11px; opacity:.65; margin-bottom:5px; display:block; }}
</style></head>
<body>
<div class="hint">
  arraste pra mover · roda pra zoom · clique fixa destaque, clique vazio limpa
  <div class="legenda">
    <span><i class="dot" style="background:#4fd1c5"></i>núcleo</span>
    <span><i class="dot" style="background:#c792ea"></i>cliente/produto</span>
    <span><i class="dot" style="background:#7a8cff"></i>sistema</span>
    <span><i class="dot" style="background:#d9534f"></i>órfão (sem link chegando)</span>
  </div>
</div>
<div id="tooltip"></div>
<svg></svg>
<script>
const nos = {nos_js};
const links = {links_js};

// mapa de vizinhos precisa dos ids originais (string), antes do d3.forceLink
// mutar source/target dos links pra objeto de no
const vizinhos = new Map(nos.map(n => [n.id, new Set([n.id])]));
links.forEach(l => {{ vizinhos.get(l.source)?.add(l.target); vizinhos.get(l.target)?.add(l.source); }});

const CORES = {{ nucleo: "#4fd1c5", cliente: "#c792ea", sistema: "#7a8cff" }};
const cor = d => d.orfao ? "#d9534f" : CORES[d.cat];

const svg = d3.select("svg");
const tooltip = d3.select("#tooltip");
const gZoom = svg.append("g");
const w = window.innerWidth, h = window.innerHeight;

const raioBase = d => 5 + Math.sqrt(d.grau) * 4;

// distancia/forca do grafo escala com o zoom: zoom in (k alto) afasta os nos
// e revela espaco; zoom out (k baixo) comprime a rede. k comeca em 1.
let k = 1;

const sim = d3.forceSimulation(nos)
  .force("link", d3.forceLink(links).id(d => d.id).distance(90).strength(0.6))
  .force("charge", d3.forceManyBody().strength(-320))
  .force("center", d3.forceCenter(w/2, h/2))
  .force("collide", d3.forceCollide(d => raioBase(d) + 14));

function reescalarForcas() {{
  // clamps evitam distancia/forca degenerar nos extremos do zoom (0.15 a 5)
  const f = Math.min(Math.max(k, 0.4), 2.5);
  sim.force("link").distance(90 * f);
  sim.force("charge").strength(-320 * f);
  sim.force("collide").radius(d => (raioBase(d) + 14) * Math.max(f, 0.6));
  sim.alpha(0.35).restart();
}}

const link = gZoom.append("g").selectAll("line").data(links).join("line").attr("class","link");
const node = gZoom.append("g").selectAll("g").data(nos).join("g")
  .attr("class", "node")
  .call(d3.drag()
    .on("start", (e,d) => {{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
    .on("drag", (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
    .on("end", (e,d) => {{ if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }}));

node.append("circle").attr("r", raioBase).attr("fill", cor).style("color", cor);
node.append("text").text(d => d.id).attr("x", d => raioBase(d) + 4).attr("y", 4);

let fixado = null;

function aplicarDestaque(id) {{
  if (id === null) {{
    node.classed("dim", false).classed("hi", false).classed("vizinho", false);
    link.classed("dim", false).classed("hi", false);
    return;
  }}
  const conectados = vizinhos.get(id);
  node.classed("dim", n => !conectados.has(n.id))
      .classed("hi", n => n.id === id)
      .classed("vizinho", n => conectados.has(n.id) && n.id !== id);
  link.classed("dim", l => l.source.id !== id && l.target.id !== id)
      .classed("hi", l => l.source.id === id || l.target.id === id);
}}

node
  .on("mouseenter", (e, d) => {{
    if (!fixado) aplicarDestaque(d.id);
    tooltip.style("opacity", 1).html(
      `<b>${{d.id}}</b><span class="cat">${{d.desc}}</span>${{d.path}}`
    );
  }})
  .on("mousemove", (e) => {{
    tooltip.style("left", (e.clientX + 16) + "px").style("top", (e.clientY + 12) + "px");
  }})
  .on("mouseleave", () => {{
    if (!fixado) aplicarDestaque(null);
    tooltip.style("opacity", 0);
  }})
  .on("click", (e, d) => {{
    e.stopPropagation();
    fixado = (fixado === d.id) ? null : d.id;
    aplicarDestaque(fixado);
  }});

svg.on("click", () => {{ fixado = null; aplicarDestaque(null); }});

svg.call(d3.zoom().scaleExtent([0.15, 5]).on("zoom", e => {{
  gZoom.attr("transform", e.transform);
  // zoom in (k alto) afasta os nos na fisica; zoom out (k baixo) comprime.
  const novoK = e.transform.k;
  if (Math.abs(novoK - k) > 0.03) {{ k = novoK; reescalarForcas(); }}
}}));

sim.on("tick", () => {{
  link.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});
</script>
</body></html>"""
    destino.write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true", help="gera mapa.html")
    ap.add_argument("--json", action="store_true", help="grava mapa.json")
    ap.add_argument("--raiz", default=".", help="pasta do projeto (padrao: atual)")
    args = ap.parse_args()

    global ROOT
    ROOT = Path(args.raiz).resolve()

    grafo = montar_grafo()
    imprimir_resumo(grafo)

    if args.json:
        out = ROOT / "mapa.json"
        out.write_text(json.dumps(grafo, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSalvo em {out}")

    if args.html:
        out = ROOT / "mapa.html"
        gerar_html(grafo, out)
        print(f"\nSalvo em {out} (abra no navegador)")


if __name__ == "__main__":
    main()
