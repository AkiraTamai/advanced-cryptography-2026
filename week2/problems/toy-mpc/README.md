# toy-mpc

## 概要

マルチパーティ計算（MPC）のトイモデルを作り、秘密分散やshareを用いた計算の仕組みを習得します。また、秘匿回路に用いられる紛失通信（Oblivious Transfer; OT）を実装し、OTからBoolean MPCの秘密ANDゲートを構成します。

この週では、次の2種類の計算をコードで実装し比較します。

- **Arithmetic MPC**: 有限体上の加法的秘密分散とBeaver tripleを用いる計算
- **Boolean MPC**: XOR shareとOTを用いる秘匿回路の計算

## 課題

<!-- 課題内容を追加 -->

## 採点

<!-- 採点内容を追加 -->

## 提出先

```text
week2/submissions/<github-username>/toy-mpc/python/
```

このディレクトリに、必ず次を置きます。

```text
solution.py
requirements.txt
```

## 進め方（スクリプト）

github-username は自動判定されます。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week2 toy-mpc

# 2. solution.py を実装し、テスト
bash scripts/test-python-submission.sh week2 toy-mpc <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week2 toy-mpc
```

## ルール

- Python のみです。標準ライブラリだけで解けます（追加パッケージは不要）。
- 編集してよいのは `week2/submissions/<github-username>/` 以下だけです。
- `problems/`、`.github/`、`scripts/` は編集しないでください。
<!-- 必要なルールがあれば追加 -->
