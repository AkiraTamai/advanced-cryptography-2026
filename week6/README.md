# Week 6

Week 6 のテーマは Programmable Cryptography Stack Design（zkVM / vFHE）です。
講義で扱った「VM 抽象を支えるルックアップ論法」と「FHE の準同型性の核である LWE」を、
実際に手を動かして実装します。

Week 6 の問題は次の 2 つです。

- `lookup-argument`: Rust で ZK のルックアップ／permutation 論法の核となる fingerprint（乱数点評価によるマルチ集合等価性チェック）を実装する問題
- `lwe-toggle`: Python で LWE（Learning With Errors）ベースの 1-bit 対称鍵暗号化・復号・準同型加算を実装する問題

## 提出先

Rust の `lookup-argument` は次の場所に提出してください。

```text
week6/submissions/<github-username>/lookup-argument/rust/
```

Python の `lwe-toggle` は次の場所に提出してください。

```text
week6/submissions/<github-username>/lwe-toggle/python/
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

`lwe-toggle` はサードパーティ製パッケージを必要としません。`requirements.txt` は空（またはコメントのみ）で提出してください。

## Rust テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/lookup-argument/rust
cp -R week6/problems/lookup-argument/rust/template/. \
  week6/submissions/<github-username>/lookup-argument/rust/
```

## Python テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/lwe-toggle/python
cp -R week6/problems/lwe-toggle/python/template/. \
  week6/submissions/<github-username>/lwe-toggle/python/
```

## ローカルテスト

Rust:

```bash
bash scripts/test-rust-submission.sh week6 lookup-argument <github-username>
```

Python:

```bash
bash scripts/test-python-submission.sh week6 lwe-toggle <github-username>
```

## Pull Request

PR title は次の形式にしてください。

```text
[week6] <github-username>
```

CI が成功すれば、提出は完了です。
