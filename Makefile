PANDOC := pandoc
PDF_ENGINE := xelatex
TEMPLATE := eisvogel

DESIGN_DOCS := docs/pdf/conceptual-design.pdf docs/pdf/logical-design.pdf docs/pdf/physical-design.pdf
DELIVER_DOC := docs/pdf/deliver.pdf
OPERATE_DOC := docs/pdf/operate.pdf

ALL_PDFS := $(DESIGN_DOCS) $(DELIVER_DOC) $(OPERATE_DOC)

PANDOC_FLAGS := --template $(TEMPLATE) --pdf-engine=$(PDF_ENGINE) --toc --toc-depth=3 --number-sections

.PHONY: pdf clean install-deps

pdf: $(ALL_PDFS)
	@echo "All PDFs generated successfully."

docs/pdf/conceptual-design.pdf: docs/markdown/conceptual-design.md docs/markdown/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/markdown/metadata/design.yaml

docs/pdf/logical-design.pdf: docs/markdown/logical-design.md docs/markdown/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/markdown/metadata/design.yaml

docs/pdf/physical-design.pdf: docs/markdown/physical-design.md docs/markdown/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/markdown/metadata/design.yaml

docs/pdf/deliver.pdf: docs/markdown/deliver.md docs/markdown/metadata/deliver.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/markdown/metadata/deliver.yaml

docs/pdf/operate.pdf: docs/markdown/operate.md docs/markdown/metadata/operate.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/markdown/metadata/operate.yaml

clean:
	rm -f $(ALL_PDFS)

install-deps:
	@echo "Install the following dependencies:"
	@echo ""
	@echo "  brew install pandoc"
	@echo "  brew install --cask mactex-no-gui"
	@echo ""
	@echo "Then install the Eisvogel template:"
	@echo "  Download from https://github.com/Wandmalfarbe/pandoc-latex-template/releases"
	@echo "  Copy eisvogel.latex to:"
	@echo "    mkdir -p ~/.local/share/pandoc/templates"
	@echo "    cp eisvogel.latex ~/.local/share/pandoc/templates/eisvogel.latex"
