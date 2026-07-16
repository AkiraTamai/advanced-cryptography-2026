# Week 1 — Programmable Cryptography Overview

ZK / MPC / FHE を貫く共通の中間表現「**算術回路**（＝有限体 F_p 上の多項式制約の
集合）」を、Circom を学ぶ前に極小の Python DSL で体験します。講義の **Proof-of-Exploit
/ Circuit-Breaker**（「制約は満たすのに、本来守るべき性質を破る witness を突きつける」）
と地続きの課題です。**受講者は Python の `solution.py` を 1 ファイル書くだけ**です。

## この週のゴール

- 回路 ＝ 制約の集合、witness ＝ 各信号への割当、という基本を掴む。
- **アンダー制約（under-constrained）が脆弱性になる**ことを、防御側（健全な回路を
  組む）と攻撃側（壊れた回路を破る）の両方から理解する。

---

## 課題: proof-of-exploit

題材はアクセス制御。資格情報 `(role, clearance, region)`（各 0〜7 の整数）が、
**3 つの許可リストすべてに入っているときだけ** アクセスを許可（`granted = 1`）する
回路を扱います。これは講義の「ハッキングの 54% はアクセス制御の不備」と地続きです。

許可リスト（公開・固定、`week1/problems/spec.py`）:

```text
ROLE_OK      = {2, 5, 6}
CLEARANCE_OK = {3, 4, 7}
REGION_OK    = {1, 6}
authorized(role, clearance, region) := role∈ROLE_OK ∧ clearance∈CLEARANCE_OK ∧ region∈REGION_OK
```

`solution.py` に 2 つの関数を実装します。

### Part A — `build(cs, role, clearance, region)`

次を満たす回路を組みます。

> `granted == 1` を満たす割当が存在する **⇔** `(role, clearance, region)` が
> `authorized(...)` を満たす。

- 資格信号は **必ず** `"role"`, `"clearance"`, `"region"` の名前で `cs.input(name, value)` として宣言する。
- 補助信号は `cs.aux(name, value)`、制約は `cs.assert_zero(expr)`、出力は `cs.set_output(granted)`。
- **信号・制約の集合は入力の値に依存してはいけない**（許可リストにのみ依存）。

**ヒント（メンバーシップ・フラグ）**: 許可リスト `S = {a1, a2, ...}` について、ブール
値フラグ `f` に `f * (x-a1) * (x-a2) * ... == 0` を課すと `f == 1 ⇒ x ∈ S` が保証
されます。3 つのフラグの AND を `granted` に。フラグをビットに固定する制約を忘れずに。

### Part B — `attack()`

`week1/problems/challenge.py` は同じ回路ですが、**3 フィールドのうち 1 つが許可リストに
固定されていません**（アンダー制約のバグが 1 つ仕込んであります）。`challenge.py` を
読んで欠けている制約を見つけ、次を満たす witness（全信号名 → 値の `dict`）を返します。

- `challenge.py` の **すべての制約を満たす**、`granted == 1`、しかし資格情報は
  `authorized(...)` を **満たさない**（＝不正アクセス）。
- `challenge.honest_witness(role, clearance, region)` を出発点に「改ざん」すると作りやすいです。

### DSL（`week1/problems/aclib.py`）

```python
r = cs.input("role", role)     # 資格信号
f = cs.aux("f_role", 1)        # 補助信号（フラグ等）
cs.assert_zero(f * f - f)      # 制約: f は 0 か 1
cs.assert_zero(f * (r - 2) * (r - 5) * (r - 6))   # f=1 なら r∈{2,5,6}
cs.set_output(granted)         # 出力信号を宣言
```

信号どうし・信号と `int` は `+ - *` で自由に組み合わせられます（F_p 上の多項式）。

### 採点（すべて公開・`week1/problems/grader.py`）

「決まった答えとの一致」ではなく **性質**を検査します（＝コピペや AI 丸投げでは
soundness を通せません）。`week1/problems/solver.py` が悪意ある prover として反例を
探索します。

1. **completeness**: すべての authorized な資格で `granted = 1` が成立する。
2. **structure**: 制約の集合が入力値に依存しない。
3. **soundness**: どの **unauthorized** な資格でも `granted = 1` にはできない。
4. **exploit (Part B)**: あなたの `attack()` が challenge を破っている。

---

## 進め方（3 ステップ・[uv](https://docs.astral.sh/uv/) で実行）

uv を未インストールなら: `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
# 1. 提出フォルダとテンプレートを作成
uv run python week1/problems/grade.py --new <github-username>

# 2. 実装する
#    week1/submissions/<github-username>/solution.py を編集

# 3. テスト（すべて緑になれば提出可）
uv run python week1/problems/grade.py <github-username>
```

編集してよいのは `week1/submissions/<github-username>/solution.py` **だけ**です。
`week1/problems/`、`.github/`、`scripts/` は編集しないでください。

## 提出（Pull Request）

```bash
git switch -c submit/week1-<github-username>
git add week1/submissions/<github-username>/solution.py
git commit -m "submit week1"
git push -u origin submit/week1-<github-username>
```

fork から `zk-tokyo/advanced-cryptography-2026` の `main` に PR を作成します。PR title
は `[week1] <github-username>`。CI（`uv run python week1/problems/grade.py <github-username>`）
が緑になれば提出完了です。初回のみの準備（fork / clone / upstream 登録）はリポジトリ
直下の [README](../README.md) を参照してください。
