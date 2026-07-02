# lookup-argument

## 概要

この問題では、arkworks の `ark_bn254::Fr` を使って、ZK のルックアップ論法（lookup argument）・
permutation 論法に共通する核となる部品を Rust で実装します。

講義（zkVM）で扱ったとおり、Jolt のような lookup-centric な back-end は、
「witness の各要素が特定のテーブルに含まれているか」「2 つのベクトルが同じ多重集合（multiset）か」
といった検査を、要素ごとの比較ではなく **乱数点での多項式評価 1 回** に落とし込むことで高速に検証します
（Plonk の permutation 論法や Plookup、Lasso のルックアップもこの考え方が土台になっています）。

この問題では、その核心である「fingerprint（指紋）」による多重集合等価性チェックを実装します。

## 目標

ベクトル `v = (v_0, ..., v_{n-1})` に対して、ランダムなチャレンジ `γ` を使った

```text
fingerprint(v, γ) = Π_i (γ - v_i)
```

という一変数多項式評価が、なぜ「2 つのベクトルが同じ多重集合かどうか」を高い確率で判定できるのか
（Schwartz-Zippel 補題）を、実装を通じて体感します。

## 課題

`src/lib.rs` で次の 3 つの関数を実装してください。

- `grand_product`
- `fingerprint`
- `is_permutation_check`

公開されている関数シグネチャは変更しないでください。

## Rust API

テンプレートでは次のように型が定義されています。

```rust
use ark_bn254::Fr;
use ark_ff::One;

pub type F = Fr;
```

次の関数を実装してください。

```rust
pub fn grand_product(vals: &[F]) -> F
```

`vals` の全要素の積を返します。`vals` が空のときは `F::one()` を返します。

次の関数を実装してください。

```rust
pub fn fingerprint(vals: &[F], challenge: F) -> F
```

`vals` の各要素 `v` について `(challenge - v)` の積を返します。`vals` が空のときは `F::one()` を返します。

次の関数を実装してください。

```rust
pub fn is_permutation_check(a: &[F], b: &[F], challenge: F) -> bool
```

`a` と `b` が同じ長さで、かつ `fingerprint(a, challenge) == fingerprint(b, challenge)` であるときに
`true` を返します。それ以外は `false` を返します。

## 例

`grand_product` の例:

```text
grand_product([2, 3, 4]) = 2 * 3 * 4 = 24
```

`fingerprint` の例:

```text
fingerprint([1, 2, 3], challenge=10) = (10-1) * (10-2) * (10-3) = 9 * 8 * 7 = 504
```

`is_permutation_check` の例:

```text
a = [1, 2, 3], b = [3, 1, 2] は同じ多重集合なので、任意の challenge で true。
a = [1, 1, 2], b = [1, 2, 2] は多重度が異なるので false。
```

## エッジケース

- `grand_product(&[])` は `F::one()` を返してください。
- `fingerprint(&[], challenge)` は `F::one()` を返してください（`challenge` の値によらず）。
- `a` と `b` の長さが異なる場合、`is_permutation_check` は常に `false` を返してください。
  **注意**: 長さが異なっていても偶然 `fingerprint` の値が一致することがあります
  （例: `fingerprint([], 100) = 1` かつ `fingerprint([99], 100) = 100 - 99 = 1`）。
  そのため、長さの比較を `fingerprint` の比較より先に（もしくは同時に）行う必要があります。
- 空のベクトル同士 `is_permutation_check(&[], &[], challenge)` は `true` を返してください。

## 提出先

Rust の解答は次の場所に提出してください。

```text
week6/submissions/<github-username>/lookup-argument/rust/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

## ローカルテスト

リポジトリのルートで次を実行してください。

```bash
bash scripts/test-rust-submission.sh week6 lookup-argument <github-username>
```

## ルール

- この問題は Rust のみです。
- 有限体の型として `ark_bn254::Fr` を使ってください。
- 依存クレートは `ark-ff`、`ark-bn254` のみ使用できます。
- `week6/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week6/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください。
