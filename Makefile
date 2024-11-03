NPX=npx

preview:
	$(NPX) zenn preview

new:
	$(NPX) zenn new:article

lint:
	$(NPX) textlint --config ./textlintrc.json articles
