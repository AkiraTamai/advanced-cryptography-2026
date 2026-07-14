# co-snark-prove

## 概要

この問題では、**co-SNARK** の核心——「SNARK の証明者アルゴリズムを、witness を秘密分散したまま
MPC で協調実行する」——のうち、**証明者が MPC 上で走らせる計算そのもの**を Python で実装します。

秘密分散の基本操作（`share` / `reconstruct` / `add_shares` / `scale_shares` / `beaver_multiply`）は
**すでに学習済みの道具**として `solution.py` の上部に**実装済みで支給**されます。この問題で MPC を
再実装することはありません。あなたが書くのは、それらを**部品として組み合わせた prover** です。

```text
通常:      π ← Prove(pk, x; w)             // 単一の証明者が witness w 全体を保持
co-SNARK:  [w] = (w_1, ..., w_N)           // witness を秘密分散
           π ← MPC-Prove(pk, x; [w])       // ← ここを実装する
verify:    Verify(vk, x, π)                // 通常 SNARK と全く同一（無変更）
```

講義で扱ったとおり、SNARK 証明者の主計算（MSM・FFT）は体 F 上の**線形演算**であり、線形演算は
秘密分散された値の上で**各 party がローカルに、通信なしで**計算できます。**secret × secret の乗算**
だけが通信（Beaver 乗算 = open を含む 1 ラウンド）を要します。

## トイ prover の定義

この問題の prover は、witness `w = (w_0, ..., w_{n-1})` と公開係数ベクトル `coeffs_a` / `coeffs_b`
から、証明 `(A, B, C)` を計算します。

```text
A = Σ_j coeffs_a[j] · w_j        // 線形結合 → share 上でローカル（通信不要）
B = Σ_j coeffs_b[j] · w_j        // 線形結合 → share 上でローカル（通信不要）
C = A · B                        // secret × secret → Beaver 乗算 1 ラウンド
```

これは実際の SNARK 証明者を**本質的な形に縮約**したものです。実際の prover は多数の線形結合
（MSM/FFT）と少数の積からなり、線形部分は share 上で無料、積の箇所だけが Beaver を要します。
**正しい co-SNARK prover は witness を `reconstruct` しません**——open されるのは最終的な証明要素だけです。

## 目標

- 線形演算（線形結合）が `scale_shares` / `add_shares` だけで、**各 party ローカルに**完結することを実装で確認する。
- prover 全体を秘密分散された witness の上で走らせ、**secret × secret の乗算だけ**が Beaver を要することを体感する。
- 復元した証明 `(A, B, C)` が、単一証明者が平文で計算した証明と**完全に一致する**ことを確認する。

## 課題

`solution.py` で次の 2 つの関数を実装してください。上部の秘密分散プリミティブ（支給）は編集しないでください。

- `linear_combination_shares`
- `mpc_prove`

## Python API

```python
def linear_combination_shares(
    coeffs: list[int],
    wire_shares: list[list[int]],
    modulus: int,
) -> list[int]:
```

`Σ_j coeffs[j] · w_j` の share ベクトルを返します。`wire_shares[j]` は wire `w_j` の share ベクトル
（すべての wire は同じ party 数）。`scale_shares` と `add_shares` **だけ**で構成してください（通信不要）。

```python
def mpc_prove(
    coeffs_a: list[int],
    coeffs_b: list[int],
    wire_shares: list[list[int]],
    beaver_triple: tuple[list[int], list[int], list[int]],
    modulus: int,
) -> tuple[list[int], list[int], list[int]]:
```

秘密分散された witness の上で prover を走らせ、証明要素の share ベクトル `(A, B, C)` を返します。
`beaver_triple` は `(a_shares, b_shares, c_shares)`（`c = a · b` を満たす）で、`A · B` の 1 回の乗算に使います。

## 例

```text
modulus = 97,  witness w = [3, 5]
coeffs_a = [1, 2]  ->  A = 1·3 + 2·5 = 13
coeffs_b = [4, 1]  ->  B = 4·3 + 1·5 = 17
C = A · B = 13·17 = 221 = 27 (mod 97)
proof = (13, 17, 27)

2 者への分散例:
  w_0 = 3 -> [1, 2],   w_1 = 5 -> [2, 3]
  A_shares = 1·[1,2] + 2·[2,3] = [5, 8]     reconstruct = 13
  B_shares = 4·[1,2] + 1·[2,3] = [6, 11]    reconstruct = 17
Beaver triple a=5 [1,4], b=9 [4,5], c=45 [20,25]:
  d = 13 - 5 = 8,  e = 17 - 9 = 8
  z_0 = 20 + 8·4 + 8·1 + 8·8 = 124 = 27 (mod 97)
  z_1 = 25 + 8·5 + 8·4       = 97  = 0  (mod 97)
  reconstruct([27, 0]) = 27 = 13·17 (mod 97)
```

## エッジケース

- `linear_combination_shares` の返り値は share ベクトル（長さ = party 数）で、`reconstruct` すると
  平文の線形結合に一致してください。
- 線形結合が `0`（mod modulus）になる場合や、`A` または `B` が `0` の場合も、`C = A · B` が正しく `0` に
  なるようにしてください。
- `mpc_prove` は witness を `reconstruct` してはいけません（プライバシーの前提が壊れます）。

## 提出先

```text
week6/submissions/<github-username>/co-snark-prove/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

この問題はサードパーティ製パッケージを必要としません。`requirements.txt` は空（またはコメントのみ）にしてください。

## ローカルテスト

```bash
bash scripts/test-python-submission.sh week6 co-snark-prove <github-username>
```

## ルール

- この問題は Python のみです。
- 標準ライブラリのみ使用できます。サードパーティ製パッケージは使用できません。
- `week6/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week6/submissions/<github-username>/` 以下だけです。
- `solution.py` 上部の**支給済み秘密分散プリミティブは編集しないでください**。関数シグネチャも変更しないでください。
