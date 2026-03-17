PANDOC := pandoc
PDF_ENGINE := xelatex
TEMPLATE := eisvogel

DESIGN_DOCS := docs/conceptual-design.pdf docs/logical-design.pdf docs/physical-design.pdf
DELIVER_DOC := docs/deliver.pdf
OPERATE_DOC := docs/operate.pdf

ALL_PDFS := $(DESIGN_DOCS) $(DELIVER_DOC) $(OPERATE_DOC)

PANDOC_FLAGS := --template $(TEMPLATE) --pdf-engine=$(PDF_ENGINE) --toc --toc-depth=3 --number-sections

.PHONY: pdf clean install-deps

pdf: $(ALL_PDFS)
	@echo "All PDFs generated successfully."

docs/conceptual-design.pdf: docs/conceptual-design.md docs/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/metadata/design.yaml

docs/logical-design.pdf: docs/logical-design.md docs/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/metadata/design.yaml

docs/physical-design.pdf: docs/physical-design.md docs/metadata/design.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/metadata/design.yaml

docs/deliver.pdf: docs/deliver.md docs/metadata/deliver.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/metadata/deliver.yaml

docs/operate.pdf: docs/operate.md docs/metadata/operate.yaml
	$(PANDOC) $< -o $@ $(PANDOC_FLAGS) --metadata-file=docs/metadata/operate.yaml

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
