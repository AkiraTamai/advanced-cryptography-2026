# air-trace-check

## 概要

この問題では、arkworks の `ark_bn254::Fr` を使って、zkVM が証明対象を算術化する仕組み
（**AIR: Algebraic Intermediate Representation**）の核となるチェックを Rust で実装します。

講義で扱ったとおり、zkVM は次の流れで「任意プログラムの実行」を証明可能にします。

```text
trace T ∈ F^(n×w)                          // n steps × w cols
∀i: C(T[i], T[i+1]) = 0                    // transition: 隣接行が ISA 規則に従う
    T[0] = init, out(T[n-1]) = y           // boundary: 入出力を固定
正しい実行 ⟺ 制約多項式が Z_H(X) = Π(X-ω^i) で割り切れる
```

この問題では、単一列（w=1）のトレースに対して、transition 制約と boundary 制約を直接チェックする関数を実装します。
これは実際の STARK/SNARK が「乱数点評価 + 多項式コミットメントで簡潔に」証明する内容を、
簡潔化せず素朴にそのまま計算したものだと考えてください。

命令セットには、講義で扱った LeanVM の最小 ISA（ADD / MUL / DEREF / JUMP の 4 命令）のうち、
レジスタ演算にあたる **ADD と MUL** を使います（DEREF・JUMP はメモリ・制御フローを伴うため、この問題の範囲外です）。

## 目標

- 「1 命令 = 1 つの transition 制約」という AIR の考え方を、具体的な ADD/MUL 命令列で体感します。
- 「正しい実行とは、境界条件と全ステップの遷移規則を同時に満たすトレースである」という定義を実装します。

## 課題

`src/lib.rs` で次の 3 つの関数を実装してください。

- `check_transitions`
- `check_boundary`
- `is_valid_execution`

公開されている関数シグネチャは変更しないでください。`Instruction` 列挙型と `step` 関数はすでに実装済みです。

## Rust API

テンプレートでは次のように型が定義されています。

```rust
use ark_bn254::Fr;

pub type F = Fr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Instruction {
    Add(F),
    Mul(F),
}
```

`Instruction::Add(k)` は「現在の状態に `k` を足す」、`Instruction::Mul(k)` は「現在の状態に `k` を掛ける」命令です
（`step` 関数として実装済みです）。

次の関数を実装してください。

```rust
pub fn check_transitions(trace: &[F], program: &[Instruction]) -> bool
```

`trace.len() == program.len() + 1` を満たし、かつ各 `i` について
`trace[i+1]` が `program[i]` を `trace[i]` に適用した結果と一致するとき `true` を返します。
それ以外は `false` を返します（長さが一致しない場合も `false`）。

```rust
pub fn check_boundary(trace: &[F], init: F, expected_output: F) -> bool
```

`trace` が空でなく、`trace[0] == init` かつ `trace[trace.len()-1] == expected_output` のとき `true` を返します。
`trace` が空の場合は `false` を返します。

```rust
pub fn is_valid_execution(trace: &[F], program: &[Instruction], init: F, expected_output: F) -> bool
```

`check_transitions` と `check_boundary` の両方が成り立つときのみ `true` を返します。

## 例

```text
program = [Add(2), Mul(3), Add(-1)]
trace   = [5, 7, 21, 20]

step 0: Add(2):  5 + 2  = 7
step 1: Mul(3):  7 * 3  = 21
step 2: Add(-1): 21 - 1 = 20

check_transitions(trace, program) = true
check_boundary(trace, init=5, expected_output=20) = true
is_valid_execution(trace, program, 5, 20) = true
```

## エッジケース

- `program` が空で `trace` が 1 行だけのとき（命令のない実行）、`check_transitions` は
  `trace.len() == 0 + 1` を満たすので `true` を返してください（遷移チェック対象がないため vacuously true）。
- `trace` が空（0 行）のとき、`check_transitions` と `check_boundary` はどちらも `false` を返してください。
  実行には少なくとも 1 行（初期状態）が必要です。
- `trace.len() != program.len() + 1` のとき、`check_transitions` は `false` を返してください。

## 提出先

Rust の解答は次の場所に提出してください。

```text
week6/submissions/<github-username>/air-trace-check/rust/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

## ローカルテスト

リポジトリのルートで次を実行してください。

```bash
bash scripts/test-rust-submission.sh week6 air-trace-check <github-username>
```

## ルール

- この問題は Rust のみです。
- 有限体の型として `ark_bn254::Fr` を使ってください。
- 依存クレートは `ark-ff`、`ark-bn254` のみ使用できます。
- `week6/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week6/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください（`Instruction` 列挙型・`step` 関数も変更しないでください）。
