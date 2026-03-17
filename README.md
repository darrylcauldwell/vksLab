# VKS Lab

VMware Kubernetes Service (VKS) lab environment — infrastructure-as-documentation for a home lab running vSphere with Tanzu.

## Documentation

| Document | Description | PDF |
|----------|-------------|-----|
| [Conceptual Design](docs/conceptual-design.md) | Purpose, objectives, and high-level architecture | [PDF](docs/conceptual-design.pdf) |
| [Logical Design](docs/logical-design.md) | Architecture overview and service topology | [PDF](docs/logical-design.pdf) |
| [Physical Design](docs/physical-design.md) | VLANs, subnets, and hardware layout | [PDF](docs/physical-design.pdf) |
| [Delivery Guide](docs/deliver.md) | Step-by-step deployment instructions | [PDF](docs/deliver.pdf) |
| [Operations Guide](docs/operate.md) | Standard operating procedures and troubleshooting | [PDF](docs/operate.pdf) |

## Getting Started

Start with the [Delivery Guide](docs/deliver.md) for deployment instructions.

## Generating PDFs Locally

Requires [Pandoc](https://pandoc.org/) with XeLaTeX and the [Eisvogel](https://github.com/Wandmalfarbe/pandoc-latex-template) template:

```bash
docker run --rm -v "$(pwd):/data" pandoc/extra:latest \
  docs/conceptual-design.md -o docs/conceptual-design.pdf \
  --template eisvogel --pdf-engine=xelatex --toc --toc-depth=3 --number-sections \
  --metadata-file=docs/metadata/design.yaml
```

PDFs are also generated automatically by CI on every push to `main` and committed back to the repo.
