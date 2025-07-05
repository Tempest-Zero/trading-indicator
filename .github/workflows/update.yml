name: snapshot-once

on:
  workflow_dispatch:    # manual trigger
  schedule:             # runs every 5 minutes (UTC)
    - cron: '*/5 * * * *'

jobs:
  update:
    runs-on: ubuntu-latest
    timeout-minutes: 4

    steps:
      # 1) Check out the repo and enable push via GITHUB_TOKEN
      - uses: actions/checkout@v4
        with:
          persist-credentials: true

      # 2) Install Python 3.10
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      # 3) Install dependencies
      - name: Install dependencies
        run: pip install requests

      # 4) Run the snapshot script
      - name: Generate agg_snapshot.csv
        run: python snapshot_once.py

      # 5) Commit & push CSV if it changed
      - name: Commit and push CSV
        run: |
          git config --global user.name  "snapshot-bot"
          git config --global user.email "bot@example.com"
          if git status --porcelain agg_snapshot.csv | grep .; then
            git add agg_snapshot.csv
            git commit -m "auto snapshot $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
            git push
          else
            echo "No changes to commit"
          fi
