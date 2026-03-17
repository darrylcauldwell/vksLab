# VKS Lab

VMware Kubernetes Service (VKS) lab environment — infrastructure-as-documentation for a home lab running vSphere with Tanzu.

## Documentation

| Document | Description | PDF |
|----------|-------------|-----|
| [Conceptual Design](docs/markdown/conceptual-design.md) | Purpose, objectives, and high-level architecture | [PDF](docs/pdf/conceptual-design.pdf) |
| [Logical Design](docs/markdown/logical-design.md) | Architecture overview and service topology | [PDF](docs/pdf/logical-design.pdf) |
| [Physical Design](docs/markdown/physical-design.md) | VLANs, subnets, and hardware layout | [PDF](docs/pdf/physical-design.pdf) |
| [Delivery Guide](docs/markdown/deliver.md) | Step-by-step deployment instructions | [PDF](docs/pdf/deliver.pdf) |
| [Operations Guide](docs/markdown/operate.md) | Standard operating procedures and troubleshooting | [PDF](docs/pdf/operate.pdf) |

## Config Files

| File | Description |
|------|-------------|
| [`configs/veos-startup.cfg`](configs/veos-startup.cfg) | Complete Arista vEOS startup-config (VLANs, SVIs, NAT, port-forward, BGP) |
| [`configs/vcf-bringup.json`](configs/vcf-bringup.json) | VCF deployment parameter workbook template (passwords as `<CHANGE-ME>`) |

## Getting Started

Start with the [Delivery Guide](docs/markdown/deliver.md) for deployment instructions.

## Generating PDFs Locally

Requires [Pandoc](https://pandoc.org/) with XeLaTeX and the [Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) template:

```bash
docker run --rm -v "$(pwd):/data" pandoc/extra:latest \
  docs/markdown/conceptual-design.md -o docs/pdf/conceptual-design.pdf \
  --template eisvogel --pdf-engine=xelatex --toc --toc-depth=3 --number-sections \
  --metadata-file=docs/markdown/metadata/design.yaml
```

PDFs are also generated automatically by CI on every push to `main` and committed back to the repo.
