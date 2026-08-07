# Week 2

Week 2 のテーマはマルチパーティ計算(MPC)です。MPCのトイモデルを作り、秘密分散やシェアを用いた計算の仕組みを習得します。また、秘匿回路に用いられる紛失通信（Oblivious Transfer; OT）を実装し、OTからBoolean MPCの秘密ANDゲートを構成します。

## この週のゴール

**Arithmetic MPC**
- 秘密分散とシェアを用いた計算の仕組みを理解する。
- 算術回路を秘密分散で計算する Arithmetic MPC を理解する。

**Boolean MPC**
- Oblivious Transfer（OT）の役割と仕組みを理解する。
- ブール回路を秘匿回路（Garbled Circuit）で計算する代表的な Boolean MPC を理解する。

## 演習問題

- [`toy-mpc`](problems/toy-mpc/README.md) — Arithmetic MPC と Boolean MPC のトイモデルを実装する。

## 提出先

Python の解答は次の場所に置きます。

```text
week2/submissions/<github-username>/toy-mpc/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

編集してよいのは `week2/submissions/<github-username>/` 以下だけです。
`problems/`、`.github/`、`scripts/` は編集しないでください。

## 提出の流れ（スクリプト）

> 事前に、Git・Python・（推奨）GitHub CLI が必要です。準備はリポジトリ直下の
> README [「0. 必要な環境」](../README.md#0-必要な環境) を参照してください。

github-username はスクリプトが自動判定します（`gh` または fork の `origin` から）。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week2 toy-mpc

# 2. solution.py を実装し、テスト（コマンドは 1. の出力にも表示されます）
bash scripts/test-python-submission.sh week2 toy-mpc <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week2 toy-mpc
```

## 手動でやる場合

```bash
# テンプレートのコピー
mkdir -p week2/submissions/<github-username>/toy-mpc/python
cp -R week2/problems/toy-mpc/python/template/. \
  week2/submissions/<github-username>/toy-mpc/python/

# テスト
bash scripts/test-python-submission.sh week2 toy-mpc <github-username>
```

PR title は `[week2] <github-username>` の形式にします。初回のみの準備（fork・clone・
upstream 登録）と提出手順の詳細は、リポジトリ直下の [README](../README.md) を参照して
ください。
