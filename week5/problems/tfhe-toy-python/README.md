# tfhe-toy-python

## 概要

この問題では、Week 5 の講義で扱った TFHE / Programmable Bootstrapping の流れを、
**トーラスを使わない整数 mod q の toy model** として Python で実装します。

本物の TFHE ライブラリではありません。

この課題では、平文空間を `Z_p` とし、bitを

```text
bit 0 -> p - 1
bit 1 -> 1
```

とエンコードします。`p - 1 = -1 mod p` なので、HomNAND の線形前処理は

```text
1 - m1 - m2 mod p
```

になります。

> [!WARNING]
> **このコードは教育用です。安全な暗号実装ではありません。パラメータは極小です。**

この課題では、処理順序を追いやすくするため、次の小さいパラメータを使います。

- `p = 8`, `q = 32`, `delta = 4`: 平文 `m in Z_p` に `delta=q/p` を掛けて暗号文空間 `Z_q` へ配置します。
- `N = 16`: Blind Rotation の前に、LWE 暗号文の係数を `Z_q` から回転量の空間 `Z_(2N)` へリスケーリングします。この設定では`q=2N`なので値は変わりません。
- `noise_bound = 1`: データ用の LWE/RLWE 暗号文には `e in {0, 1}` のノイズを入れます。復号時は `Delta*m` に最も近い平文へ丸めます。
- `evaluation_key_noise_bound = 0`: Bootstrapping Key と Key Switching Key はノイズなしで作ります。
- `B = 2`, `l = 5`: `q = 32 = 2^5` として、`G^{-1}` を external product と Key Switching の両方で使います。
- NTT などの高速化は省略: 多項式積や external product は、処理の流れを見やすくするためにナイーブなループで実装しています。

## 標準TFHEとの違い

この課題はTFHEの処理順序を確認するためのtoy実装であり、標準TFHEとは次の点が異なります。

| 項目                 | この課題                   | 標準TFHE                                                           |
| -------------------- | -------------------------- | ------------------------------------------------------------------ |
| 係数の表現           | 非負整数を使う整数mod `q`  | トーラスまたはその離散表現                                         |
| bitのエンコード      | `0 -> p-1`, `1 -> 1`       | 論文のHomNANDでは`0`と`1/4`を使用                                  |
| データ暗号文のノイズ | `e in {0,1}`から一様に選ぶ | セキュリティパラメータに応じた誤差分布を使う                       |
| 評価鍵のノイズ       | 簡略化のため`0`            | Bootstrapping KeyとKey Switching Keyもノイズを持つ暗号文として作る |
| パラメータ           | `p=8, q=32, N=16, k=4`     | 必要な安全性と実装方式に応じて選ぶ                                 |

この違いにより、この課題のコードには暗号学的安全性がありません。実用パラメータや完全な実装は、末尾の「発展的な参考先」を参照してください。

## 課題

`solution.py` の未実装箇所を埋め、公開テストを通してください。未実装箇所は
`NotImplementedError`で示されています。

### Part 1 -- 多項式環と LWE / RLWE の基本

```python
normalize(value, q)
scale_plaintext(message, params)
rescale_q_to_2n(value, params)
rescale_lwe_ciphertext(ciphertext, params)
dot_mod(left, right, q)
poly_add(left, right, params)
poly_sub(left, right, params)
poly_mul(left, right, params)
generate_lwe_secret_key(params, rng)
generate_rlwe_secret_key(params, rng)
encrypt_lwe(scaled_message, secret_key, params, rng)
decrypt_lwe(ciphertext, secret_key, params)
encrypt_rlwe(scaled_message, secret_key, params, rng)
decrypt_rlwe(ciphertext, secret_key, params)
```

平文は `0 <= m < p`、暗号文の係数は `0 <= x < q` の非負整数として扱います。
bit 0 の平文 `p-1` は、`Z_p` 上では `-1` と同じ剰余です。
トーラス表現は使いません。

`encrypt_lwe`には`Z_p`上の平文`m`を直接渡しません。呼び出し側で
`delta`を掛け、`Z_q`へ配置した値を渡します。

```python
message = encode_bit(bit, params)
ciphertext = encrypt_lwe(params.delta * message, secret_key, params, rng)
```

`encrypt_rlwe`も同様に、呼び出し側で各係数へ`delta`を掛け、`Z_q`へ配置した
多項式を渡します。

```python
message_poly = [3, 1, 4, 1] + [0 for _ in range(params.n - 4)]
ciphertext = encrypt_rlwe(scale_plaintext_poly(message_poly, params), secret_key, params, rng)
```

### Part 2 -- RGSW / CMUX

```python
gadget_weights(params)
gadget_decompose(value, params)
gadget_decompose_poly(poly, params)
rgsw_encrypt_bit(bit, rlwe_secret_key, params, rng)
external_product(control, ciphertext, params)
cmux(control, false_ciphertext, true_ciphertext, params)
```

`gadget_decompose` は、次の式

```text
r = Σ r_i * q / B^{i+1}
```

に対応します。テンプレートでは `q = 32`, `B = 2`, `l = 5` なので、たとえば `29` は

```text
29 = 1 * 16 + 1 * 8 + 1 * 4 + 0 * 2 + 1 * 1
g^{-1}(29) = [1, 1, 1, 0, 1]
```

と分解されます。

`external_product` では、`G^{-1}(RLWE_s(m')) RGSW_s(m)` に対応するように、RLWE 暗号文の `a(X)` と `b(X)` をそれぞれ多項式として Gadget Decomposition します。

`cmux` は次の式

```text
 MUX(b, a_0, a_1) = b * (a_1 - a_0) + a_0
```

を暗号文上で実行します。

### Part 3 -- PBS と HomNAND

```python
make_evaluation_key(lwe_secret_key, rlwe_secret_key, params, rng)
blind_rotate(ciphertext, test_polynomial, bootstrapping_key, params)
sample_extract(ciphertext, params)
key_switch(ciphertext, key_switching_key, params)
programmable_bootstrap(ciphertext, evaluation_key, params)
hom_nand(left, right, evaluation_key, params)
```

この実装では、Programmable Bootstrapping を次の順に分けています。

1. Blind Rotation: 入力 LWE 暗号文と bootstrapping key から、回転後のテスト多項式の RLWE 暗号文を作る
2. Sample Extraction: RLWE 暗号文の定数項を、`a''=(a'_0,-a'_{N-1},..., -a'_1)`, `b'_0` という LWE 暗号文として取り出す
3. Key Switching: 取り出した LWE 暗号文の `a''` を Gadget Decomposition し、Key Switching Key を使って元の LWE 鍵へ戻す

`EvaluationKey` には `bootstrapping_key` と `key_switching_key` だけを入れます。`rlwe_secret_key` は本来公開されない秘密鍵なので、評価鍵には含めません。

`noise_bound = 1` は、データ暗号文を暗号化するときにサンプルするノイズの上限です。演算途中の累積ノイズが常に`1`以下でなければならない、という意味ではありません。たとえばHomNANDの線形前処理では2つの入力ノイズが合わさるため、距離が`2`になる場合があります。それでも回転番号がテスト多項式の同じ出力区間に残るため、HomNANDは正常に動きます。

Bootstrapping KeyとKey Switching Keyは、toyパラメータで処理を成立させるため、ノイズなしで作ります。そのため、Blind Rotation中のCMUXとKey Switchingは評価鍵に由来する新しいノイズを追加しません。

bit 1とbit 0は`Z_q`上の`Delta`と`q-Delta`に配置されます。この2点から復号境界までの距離は`Delta=4`です。

Sample Extractionは新しいノイズを加えません。Blind Rotation後のRLWE暗号文の定数項にあったノイズが、そのまま抽出後のLWE暗号文へ移ります。

## パラメータ

テンプレートでは次を使います。

```text
k                  = 4
p                  = 8
n                  = 16
q                  = 32
delta              = 4
noise_bound        = 1
evaluation_key_noise_bound = 0
B                  = 2
l                  = 5
bit 0 in Z_p       = 7
bit 1 in Z_p       = 1
bit 0 in Z_q       = 28
bit 1 in Z_q       = 4
HomNAND constant in Z_p = 1
NAND test polynomial coefficients in Z_p = [1, 1, ..., 1]
```

HomNAND では、まず `Z_p` 上の `1 - m1 - m2` に対応するLWE暗号文を計算し、
その結果に対して programmable bootstrapping を行います。

| bit1 | bit2 | `m1` | `m2` | ノイズなしの `1 - m1 - m2 mod 8` | NAND output |
| ---- | ---- | ---- | ---- | -------------------------------- | ----------- |
| 0    | 0    | 7    | 7    | 3                                | 1           |
| 1    | 0    | 1    | 7    | 1                                | 1           |
| 0    | 1    | 7    | 1    | 1                                | 1           |
| 1    | 1    | 1    | 1    | 7                                | 0           |

テスト多項式は `V(X)=1+X+...+X^(N-1)` です。Blind Rotation の
negacyclicな符号反転により、定数項は `1` または `p-1` になります。

### パラメータに関する注意

この課題では、既定のパラメータを変更しないでください。公開テストは
`ToyTFHEParams()` の既定値に合わせて作られています。

特に次の関係を仮定しています。

- `delta = q / p = 4`
- `q = 2N = 32`
- `q = B^l = 2^5`
- データ暗号文のノイズは `e in {0, 1}`
- Bootstrapping Key と Key Switching Key のノイズは `0`

これらを変えると、復号の丸め、Blind Rotation の回転量、Gadget Decomposition、
Key Switching Key の重みが同時に変わります。実装が正しくても、課題のテストとは
別の問題を解いている状態になるため、提出では既定値のままにしてください。

`noise_bound = 1` は、暗号化時に加えるノイズの上限です。HomNAND の線形前処理や
CMUX の途中で現れる累積ノイズが常に `1` 以下である、という意味ではありません。
この toy パラメータでは、出力の丸めが壊れない範囲に収まるようにテストを設計しています。
