# lwe-toggle

## 概要

この問題では、Python の標準ライブラリだけを使って、FHE（vFHE）を支える困難性仮定である
**LWE（Learning With Errors）** に基づく 1-bit 対称鍵暗号化・復号・そして
**準同型加算（homomorphic addition）** を実装します。

講義の Trade-off 表にあるとおり、FHE の信頼前提は LWE の困難性であり、
「暗号文同士は自然に合成できる（`Eval(ct, f) -> ct_out`）」という性質が FHE の核心です。
ここで実装する `lwe_add` はまさにその最小例（1-bit の XOR）であり、
「この演算が正しく行われたことをどう検証するか」が vFHE（Greco / EagleEye）の課題になります。

## 目標

- 秘密鍵ベクトル `sk` とランダムベクトル `a`、ノイズ `e` から LWE 暗号文を作る方法を学びます。
- 暗号文を復号するときに、ノイズがあっても正しいビットを復元できる「丸め復号」の考え方を学びます。
- 2 つの暗号文を成分ごとに足すだけで、平文の XOR が得られる（=準同型性）ことを確認します。

## 課題

`solution.py` で次の 3 つの関数を実装してください。

- `lwe_encrypt`
- `lwe_decrypt`
- `lwe_add`

公開されている関数シグネチャは変更しないでください。

## Python API

次の関数を実装してください。

```python
def lwe_encrypt(bit: int, secret_key: list[int], a: list[int], e: int, modulus: int) -> int:
```

1-bit の平文 `bit`（0 または 1）を暗号化し、暗号文の `b` 成分を返します。
暗号文全体は `(a, b)` ですが、`a` は呼び出し側がすでに持っているため、この関数は `b` だけを返します。

```text
b = (a・sk + e + bit * (modulus // 2)) mod modulus
```

ここで `a・sk` は内積 `sum(a[i] * sk[i])` です。

```python
def lwe_decrypt(a: list[int], b: int, secret_key: list[int], modulus: int) -> int:
```

暗号文 `(a, b)` を復号し、平文ビット（0 または 1）を返します。

```text
diff = (b - a・sk) mod modulus
```

を計算し、`diff` が `0` に近ければ `0`、`modulus // 2` に近ければ `1` を返してください。
「近さ」は mod `modulus` の**円環上の距離**（circular distance）で判定してください。
例えば `modulus = 97` のとき、`diff = 96` は `0` からの円環距離が `1`（`97 - 96 = 1`）であり、
非円環的な単純比較（`diff > 48` かどうか）で判定すると誤ります。

```python
def lwe_add(
    ct1: tuple[list[int], int],
    ct2: tuple[list[int], int],
    modulus: int,
) -> tuple[list[int], int]:
```

2 つの暗号文 `(a1, b1)` と `(a2, b2)` を成分ごとに mod `modulus` で足し合わせた
新しい暗号文 `(a1 + a2 mod modulus, b1 + b2 mod modulus)` を返します。

## 例

```text
sk = [3, 1, 4, 1], a = [5, 9, 2, 6], modulus = 97
a・sk = 5*3 + 9*1 + 2*4 + 6*1 = 15 + 9 + 8 + 6 = 38

lwe_encrypt(0, sk, a, e=0, modulus=97) = 38
lwe_encrypt(1, sk, a, e=0, modulus=97) = (38 + 48) mod 97 = 86

lwe_decrypt(a, 38, sk, 97) = 0
lwe_decrypt(a, 86, sk, 97) = 1
```

## エッジケース

- `e` は負の値になり得ます。Python の `%` は正の剰余を返すので、そのまま使えます。
- ノイズが大きすぎない限り（本問題のテストで使うノイズの範囲では）、復号は常に正しいビットを返す必要があります。
- `lwe_add` の後に `lwe_decrypt` した結果は、元の 2 つのビットの XOR と一致してください
  （`0+0=0`, `0+1=1`, `1+0=1`, `1+1=0` — mod 2 の加算として `modulus // 2` の係数が循環するため）。

## 提出先

Python の解答は次の場所に提出してください。

```text
week6/submissions/<github-username>/lwe-toggle/python/
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
bash scripts/test-python-submission.sh week6 lwe-toggle <github-username>
```

## ルール

- この問題は Python のみです。
- 標準ライブラリのみ使用できます。サードパーティ製パッケージは使用できません。
- `week6/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week6/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください。
