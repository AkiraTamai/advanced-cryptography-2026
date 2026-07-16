# Week 1

Week 1 は **Programmable Cryptography Overview** の週です。ZK / MPC / FHE を貫く
共通の中間表現である「算術回路（＝有限体上の多項式制約の集合）」を、Circom を学ぶ
前に極小の Python DSL で体験します。

## この週のゴール

- 回路 ＝ F_p 上の制約の集合、witness ＝ 各信号への割当、という基本を掴む。
- **アンダー制約（under-constrained）が脆弱性になる**ことを、防御側（健全な回路を
  組む）と攻撃側（壊れた回路を破る）の両方から理解する。講義の Proof-of-Exploit /
  Circuit-Breaker と地続きです。

## 演習問題

- [`proof-of-exploit`](problems/proof-of-exploit/README.md): Python でアクセス制御
  回路を **健全かつ完全** に実装し（Part A）、わざとアンダー制約にした回路を破る
  witness を作る（Part B）。**Python の `solution.py` を書くだけ**で完結します。

## 提出先

```text
week1/submissions/<github-username>/proof-of-exploit/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

編集してよいのは次のディレクトリ以下だけです。

```text
week1/submissions/<github-username>/
```

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

PR title は次の形式にしてください。

```text
[week1] <github-username>
```

提出手順の詳細は、リポジトリ直下の [README](../README.md) を参照してください。
