name: Auto Nhiem Vu (Acc 4)

on:
  schedule:
    - cron: '10 17 * * *'  # 00:10 GMT+7 (17:10 UTC)
  workflow_dispatch:

jobs:
  run-daily:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests telethon colorama

      - name: Chay Bot Nhiem Vu Acc 4
        env:
          TELEGRAM_SESSION_B64_ACC4: ${{ secrets.TELEGRAM_SESSION_B64_ACC4 }}
        run: |
          python auto_kiemtien4.py
