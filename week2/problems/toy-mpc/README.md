# toy-mpc

## 概要

マルチパーティ計算（MPC）のトイモデルを作り、秘密分散やシェアを用いた計算の仕組みを習得します。また、秘匿回路に用いられる紛失通信（Oblivious Transfer; OT）を実装し、OTからBoolean MPCの秘密ANDゲートを構成します。

この週では、次の2種類の計算をコードで実装し比較します。

- **Arithmetic MPC**: 有限体上の加法的秘密分散とBeaver tripleを用いる計算
- **Boolean MPC**: XOR shareとOTを用いる秘匿回路の計算

## 前提知識

- Pythonの基本的な文法
- 整数の剰余演算
- Week 2 講義で扱う秘密分散、Beaver triple、OTの概要

課題内で必要な式とプロトコルの手順は問題文にも記載しています。

## 課題

<!-- 課題内容を追加 -->

`solution.py`の関数を実装します。`NotImplementedError`をすべて実装してください。`tests/given.py`にある定数と補助関数は編集せずに利用できます。

### Part A — Arithmetic MPC

以下を実装します。

- 加法的秘密分散と復元
- share上のlocalな加算
- Beaver tripleを用いた秘密値どうしの乗算

Part Aでは、有限体上の加法的秘密分散を使うArithmetic MPCのトイモデルを実装します。実装する関数は次の4つです。

```python
share(secret, randomness, modulus)
reconstruct(shares, modulus)
add_shares(left_shares, right_shares, modulus)
beaver_multiply(x_shares, y_shares, triple, modulus)
```


すべての値は有限体 `F_p` の要素として扱い、演算結果を `% modulus` で `0..modulus-1` に直してください。

### Part B — Oblivious Transfer and Boolean MPC

以下を実装します。

- 有限群上の1-out-of-2 OT
- OTを2回用いたGMW型の秘密AND

XOR share上のlocal XORには、提供済みの`xor_shares`を使用します。

Part Bでは、Boolean MPCのトイモデルを実装します。OTを使ってGMW型の秘密ANDを構成します。実装する関数は次の4つです。

```python
ot_receiver_request(sender_public, choice, receiver_secret)

ot_sender_encrypt(
    sender_secret,
    request,
    message_0,
    message_1,
)

ot_receiver_decrypt(
    sender_public,
    choice,
    receiver_secret,
    ciphertexts,
)

gmw_and(x_shares, y_shares, masks, ot_secrets)
```

## 採点（`tests/public.py`、内容は公開）

1. **Part A — 秘密分散**: 秘密を正しくshareに分割・復元でき、有限体の要素として正規化される。
2. **Part A — local加算**: 秘密を復元せずにshareどうしを加算でき、party数の不一致を拒否する。
3. **Part A — Beaver乗算**: 2-partyおよび3-partyで積を正しく計算し、masked differenceの2値だけを公開する。
4. **Part B — Oblivious Transfer**: receiverが選択した一方のメッセージを正しく復号でき、不正な入力を拒否する。
5. **Part B — GMW AND**: すべてのXOR shareの組合せについて秘密ANDを正しく計算し、2回のOTを使用する。

## 提出先

```text
week2/submissions/<github-username>/toy-mpc/python/
```

このディレクトリに、必ず次を置きます。

```text
solution.py
requirements.txt
```

## 進め方（スクリプト）

github-username は自動判定されます。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week2 toy-mpc

# 2. solution.py を実装し、テスト
bash scripts/test-python-submission.sh week2 toy-mpc <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week2 toy-mpc
```

## ルール

- Python のみです。標準ライブラリだけで解けます（追加パッケージは不要）。
- 編集してよいのは `week2/submissions/<github-username>/` 以下だけです。
- `problems/`、`.github/`、`scripts/` は編集しないでください。
<!-- 必要なルールがあれば追加 -->
