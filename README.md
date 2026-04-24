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

## Ansible Automation

Ansible roles and playbooks automate all 9 deployment phases. Runs from the operator's laptop via SSH ProxyJump through the gateway, with secrets from 1Password.

### Setup

```bash
# Install Ansible collections
ansible-galaxy collection install -r ansible/collections/requirements.yml

# Install VMware VCF SDK (for Phase 4+ domain management)
pip install vmware-vcf

# Or, for development:
pip install -e /path/to/vmware-vcf
```

### Running Playbooks

```bash
# Run full deployment (all 9 phases)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml

# Run a single phase
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/phase3_esxi.yml

# Dry run
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/phase3_esxi.yml --check
```

See [`ansible/`](ansible/) for roles, custom VCF modules, and inventory configuration.

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
