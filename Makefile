PNPM=pnpm

install:
	$(PNPM) install

preview:
	$(PNPM) exec zenn preview

new:
	$(PNPM) exec zenn new:article

lint:
	$(PNPM) exec textlint --config ./textlintrc.json --ignore-path ./textlintignore articles

lint/fix:
	$(PNPM) exec textlint --config ./textlintrc.json --ignore-path ./textlintignore --fix articles

