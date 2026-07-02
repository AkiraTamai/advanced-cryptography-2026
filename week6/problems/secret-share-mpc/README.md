# secret-share-mpc

## 概要

この問題では、Python の標準ライブラリだけを使って、co-SNARK が使う MPC の核である
**加法的秘密分散（additive secret sharing）** と、その上で secret×secret の乗算を可能にする
**Beaver 乗算プロトコル** を実装します。

講義で扱ったとおり、co-SNARK は SNARK の証明者アルゴリズムを、witness を秘密分散したまま
複数の当事者（party）が協調して実行することで実現します。

```text
通常:      π ← Prove(pk, x; w)             // 単一の証明者が witness w 全体を保持
co-SNARK:  [w] = (w_1, ..., w_N)            // witness を N 者へ秘密分散
           π ← MPC-Prove(pk, x; [w])        // share 上で同じ π を協調生成
verify:    Verify(vk, x, π)                 // 通常 SNARK と全く同一（無変更）
```

この構成が成立する鍵は、SNARK 証明者の主計算（MSM・FFT）が体 F 上の**線形演算**であり、
線形演算は秘密分散された値の上で**各 party がローカルに、通信なしで**計算できることです。
一方、**secret × secret の乗算**だけは通信（他 party との連携）が必要で、
そこで使われるのが Beaver 乗算プロトコルです。

## 目標

- 加法的秘密分散の share/reconstruct を実装し、「どの 1 つの share を見ても秘密は分からない」ことを確認します。
- 線形演算（加算・スカラー倍）が各 party のローカル計算だけで完結する（＝通信不要）ことを実装で確認します。
- secret×secret の乗算だけがなぜ特別な手続き（Beaver 乗算）を必要とするのかを実装を通じて理解します。

## 課題

`solution.py` で次の 5 つの関数を実装してください。

- `share`
- `reconstruct`
- `add_shares`
- `scale_shares`
- `beaver_multiply`

公開されている関数シグネチャは変更しないでください。

## Python API

```python
def share(secret: int, randomness: list[int], modulus: int) -> list[int]:
```

`secret` を `len(randomness) + 1` 個の share に加法的に分散します。
`randomness` の要素をそのまま最初の `len(randomness)` 個の share とし、
最後の 1 個は `(secret - sum(randomness)) % modulus` とします。
返り値のすべての share は `[0, modulus)` の範囲の値にしてください。

```python
def reconstruct(shares: list[int], modulus: int) -> int:
```

`sum(shares) % modulus` を返します（全 party の share を持ち寄って秘密を復元する操作）。

```python
def add_shares(shares_a: list[int], shares_b: list[int], modulus: int) -> list[int]:
```

2 つの share ベクトルを成分ごとに mod `modulus` で足します。**通信は不要**（各 party が自分の 2 つの share を足すだけ）。

```python
def scale_shares(shares: list[int], scalar: int, modulus: int) -> list[int]:
```

share ベクトルの各要素を公開のスカラー `scalar` 倍し mod `modulus` します。これも**通信は不要**。

```python
def beaver_multiply(
    x_shares: list[int],
    y_shares: list[int],
    a_shares: list[int],
    b_shares: list[int],
    c_shares: list[int],
    modulus: int,
) -> list[int]:
```

事前に配られた **Beaver triple** `(a, b, c)`（`c = a * b mod modulus` を満たす秘密分散済みの乱数トリプル）を使って、
2 つの秘密 `x`, `y` の積 `x * y` の share を計算します。

手順:

1. `d = (reconstruct(x_shares) - reconstruct(a_shares)) % modulus`（`x - a` を全員で open する）
2. `e = (reconstruct(y_shares) - reconstruct(b_shares)) % modulus`（`y - b` を全員で open する）
3. 各 party `i` はローカルに `z_i = (c_i + d * b_i + e * a_i) % modulus` を計算する
4. **party 0 だけ** `z_0` にさらに `d * e` を足す（`d*e` の重複加算を避けるため）

これは `x*y = (a+d)(b+e) = ab + a*e + d*b + d*e = c + a*e + d*b + d*e` という代数的な恒等式に基づいています。

## 例

```text
modulus = 97
x = 6 (shares = [2, 4]), y = 7 (shares = [3, 4])
Beaver triple: a = 5 (shares = [1, 4]), b = 9 (shares = [4, 5]), c = a*b = 45 (shares = [20, 25])

d = (6 - 5) % 97 = 1
e = (7 - 9) % 97 = 95   # -2 mod 97

z_0 = (20 + 1*4 + 95*1 + 1*95) % 97 = 20
z_1 = (25 + 1*5 + 95*4) % 97       = 22

reconstruct([20, 22], 97) = 42 = 6 * 7
```

## エッジケース

- `share` が返す各要素は必ず `[0, modulus)` の範囲にしてください（`randomness` に負の値や `modulus` 以上の値が渡されても）。
- `add_shares` と `scale_shares` の返り値も必ず `[0, modulus)` の範囲にしてください
  （成分ごとの加算・乗算が `modulus` を超えることがあります）。
- `x` または `y` が `0` のとき、`beaver_multiply` の結果を復元すると `0` になります。
- どの 1 つの share だけを見ても、秘密がいくつであるかは分かりません
  （同じ share 値から異なる秘密が再構成できます）。

## 提出先

Python の解答は次の場所に提出してください。

```text
week6/submissions/<github-username>/secret-share-mpc/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

この問題はサードパーティ製パッケージを必要としません。`requirements.txt` は空（またはコメントのみ）にしてください。

## ローカルテスト

リポジトリのルートで次を実行してください。

```bash
bash scripts/test-python-submission.sh week6 secret-share-mpc <github-username>
```

## ルール

- この問題は Python のみです。
- 標準ライブラリのみ使用できます。サードパーティ製パッケージは使用できません。
- `week6/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week6/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください。
