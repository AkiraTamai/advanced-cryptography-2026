# Week 6

Week 6 のテーマは Programmable Cryptography Stack Design（zkVM / vFHE / co-SNARK）です。
ZK・MPC の基礎は履修済みである前提で、この週では**それらを組み合わせて作るアプリケーション**と
**primitive の"中で／上で"走る計算**を、実際に手を動かして実装します。

Week 6 の問題は次の 2 つです。

- `co-snark-prove`: Python で、co-SNARK の証明者が **MPC 上で走らせる計算**（線形結合＋Beaver 乗算）を実装する問題。秘密分散プリミティブは支給され、その上で prover を組み立てます。
- `zkvm-exploit`: Rust で、zkVM の**中で走る guest プログラム**（Proof of Exploit）と public/witness 設計を実装する問題。zkVM 本体は動かしません。

## 提出先

Python の `co-snark-prove` は次の場所に提出してください。

```text
week6/submissions/<github-username>/co-snark-prove/python/
```

Rust の `zkvm-exploit` は次の場所に提出してください。

```text
week6/submissions/<github-username>/zkvm-exploit/rust/
```

編集してよいのは次のディレクトリ以下だけです。

```text
week6/submissions/<github-username>/
```

`problems/`、`.github/`、`scripts/` は編集しないでください。

Python の提出ディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

`co-snark-prove` はサードパーティ製パッケージを必要としません。`requirements.txt` は空
（またはコメントのみ）で提出してください。`solution.py` 上部の支給済み秘密分散プリミティブは
編集しないでください。

Rust の提出ディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

## Python テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/co-snark-prove/python
cp -R week6/problems/co-snark-prove/python/template/. \
  week6/submissions/<github-username>/co-snark-prove/python/
```

## Rust テンプレートのコピー

```bash
mkdir -p week6/submissions/<github-username>/zkvm-exploit/rust
cp -R week6/problems/zkvm-exploit/rust/template/. \
  week6/submissions/<github-username>/zkvm-exploit/rust/
```

## ローカルテスト

Python:

```bash
bash scripts/test-python-submission.sh week6 co-snark-prove <github-username>
```

Rust:

```bash
bash scripts/test-rust-submission.sh week6 zkvm-exploit <github-username>
```

## Pull Request

PR title は次の形式にしてください。

```text
[week6] <github-username>
```

CI が成功すれば、提出は完了です。
