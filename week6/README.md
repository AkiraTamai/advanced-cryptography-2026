# Week 6

Week 6 のテーマは Programmable Cryptography Stack Design（zkVM / vFHE / co-SNARK）です。
講義で扱った「zkVM が実行を算術化する仕組み（AIR）」と「co-SNARK が使う MPC の核（秘密分散と Beaver 乗算）」を、
実際に手を動かして実装します。

Week 6 の問題は次の 2 つです。

- `air-trace-check`: Rust で zkVM の AIR（実行トレース → transition 制約 → boundary 制約）を実装する問題
- `secret-share-mpc`: Python で co-SNARK が使う加法的秘密分散と Beaver 乗算プロトコルを実装する問題

## 提出先

Rust の `air-trace-check` は次の場所に提出してください。

```text
week6/submissions/<github-username>/air-trace-check/rust/
```

Python の `secret-share-mpc` は次の場所に提出してください。

```text
week6/submissions/<github-username>/secret-share-mpc/python/
```

編集してよいのは次のディレクトリ以下だけです。

```text
week6/submissions/<github-username>/
```

`problems/`、`.github/`、`scripts/` は編集しないでください。

Rust の提出ディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

Python の提出ディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

`secret-share-mpc` はサードパーティ製パッケージを必要としません。`requirements.txt` は空（またはコメントのみ）で提出してください。

## Rust テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/air-trace-check/rust
cp -R week6/problems/air-trace-check/rust/template/. \
  week6/submissions/<github-username>/air-trace-check/rust/
```

## Python テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/secret-share-mpc/python
cp -R week6/problems/secret-share-mpc/python/template/. \
  week6/submissions/<github-username>/secret-share-mpc/python/
```

## ローカルテスト

Rust:

```bash
bash scripts/test-rust-submission.sh week6 air-trace-check <github-username>
```

Python:

```bash
bash scripts/test-python-submission.sh week6 secret-share-mpc <github-username>
```

## Pull Request

PR title は次の形式にしてください。

```text
[week6] <github-username>
```

CI が成功すれば、提出は完了です。
