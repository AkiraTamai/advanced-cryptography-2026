# Week 1

Week 1 のテーマは Programmable Cryptography の全体像です。ZK・MPC・FHE に共通する
土台である「算術回路」を、小さな Python のライブラリで実際に組み立てて理解します。

## この週のゴール

- 回路とは「すべて 0 になるべき制約の集まり」であること、witness とは「各信号に
  入れる値」であることを、手を動かして掴む。
- 制約が足りない回路（アンダー制約）がなぜ脆弱になるのかを、回路を組む側と、その
  穴を突く側の両方から理解する。

## 演習問題

- [`proof-of-exploit`](problems/proof-of-exploit/README.md): アクセス制御の回路を
  正しく組み（Part A）、わざと制約を 1 つ抜いた回路の穴を突く（Part B）。Python の
  `solution.py` を書くだけで解けます。

## 提出先

Python の解答は次の場所に置きます。

```text
week1/submissions/<github-username>/proof-of-exploit/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

編集してよいのは `week1/submissions/<github-username>/` 以下だけです。
`problems/`、`.github/`、`scripts/` は編集しないでください。

## テンプレートのコピー

```bash
mkdir -p week1/submissions/<github-username>/proof-of-exploit/python
cp -R week1/problems/proof-of-exploit/python/template/. \
  week1/submissions/<github-username>/proof-of-exploit/python/
```

## ローカルテスト

```bash
bash scripts/test-python-submission.sh week1 proof-of-exploit <github-username>
```

## Pull Request

PR title は次の形式にします。

```text
[week1] <github-username>
```

初回のみの準備（fork・clone・upstream 登録）と提出の手順は、リポジトリ直下の
[README](../README.md) を参照してください。
