# Week 3

Week 3 のテーマは楕円曲線暗号と Schnorr プロトコルです。有限体の演算から
始めて、その上に楕円曲線の群を作り、最後にシグマプロトコルと Fiat-Shamir
変換で Schnorr 署名を完成させます。

## 講義資料

- [Week 3 スライド](week3_zksnark_slides.pdf)

## この週のゴール

- 有限体 F_p の演算（特に拡張ユークリッドの互除法による逆元）を手を動かして
  実装する。
- 楕円曲線の点が「群」をなすこと（単位元・逆元・足し算）と、スカラー倍が
  double-and-add で高速に計算できることを理解する。
- シグマプロトコルの 3 手（コミット・チャレンジ・レスポンス）と、
  Fiat-Shamir 変換で対話証明が署名に変わる仕組みを理解する。
- nonce の使い回しで秘密鍵が漏れる理由（special soundness）を攻撃側からも
  確認する。

## 演習問題

- [`schnorr-from-scratch`](problems/schnorr-from-scratch/README.md): 有限体 →
  楕円曲線 → Schnorr 署名を下から積み上げる、ひとつなぎの穴埋め課題。
  最後は本物の曲線 secp256k1 上で署名を作ります。Python の `solution.py` を
  書くだけで解けます。

## 提出先

Python の解答は次の場所に置きます。

```text
week3/submissions/<github-username>/schnorr-from-scratch/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

編集してよいのは `week3/submissions/<github-username>/` 以下だけです。
`problems/`、`.github/`、`scripts/` は編集しないでください。

## 提出の流れ（スクリプト）

> 事前に、Git・Python・（推奨）GitHub CLI が必要です。準備はリポジトリ直下の
> README [「0. 必要な環境」](../README.md#0-必要な環境) を参照してください。

github-username はスクリプトが自動判定します（`gh` または fork の `origin` から）。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week3 schnorr-from-scratch

# 2. solution.py を実装し、テスト（コマンドは 1. の出力にも表示されます）
bash scripts/test-python-submission.sh week3 schnorr-from-scratch <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week3 schnorr-from-scratch
```

## 手動でやる場合

```bash
# テンプレートのコピー
mkdir -p week3/submissions/<github-username>/schnorr-from-scratch/python
cp -R week3/problems/schnorr-from-scratch/python/template/. \
  week3/submissions/<github-username>/schnorr-from-scratch/python/

# テスト
bash scripts/test-python-submission.sh week3 schnorr-from-scratch <github-username>
```

PR title は `[week3] <github-username>` の形式にします。初回のみの準備（fork・clone・
upstream 登録）と提出手順の詳細は、リポジトリ直下の [README](../README.md) を参照して
ください。
