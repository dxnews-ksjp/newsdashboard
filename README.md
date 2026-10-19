# DXニュースダッシュボード

「物流DX」「生成AI」「航空貨物」「港湾」などのトピックごとに、Googleニュース（日本語版）の最新見出しを
カード形式で表示するページです。毎朝7時ごろ（日本時間）に自動で更新され、スマホからも見られます。

## しくみ

```
毎朝7時（GitHub Actions が自動実行）
  └─ scripts/build.py が Googleニュースの RSS を取得
       └─ public/index.html（ページ）を作成
            └─ GitHub Pages で公開 → スマホ・PCのブラウザで閲覧
```

| ファイル | 役割 |
|---|---|
| `topics.toml` | **トピックの設定（ここだけ書き換えればOK）** |
| `scripts/build.py` | ニュースを集めてページを作るプログラム |
| `templates/style.css` | ページのデザイン |
| `public/` | 自動で作られるページ（手で編集しない） |
| `.github/workflows/update.yml` | 毎朝の自動実行の設定 |

---

## 最初に1回だけやる設定（GitHubの画面で操作）

### ① リポジトリを「Public（公開）」にする
無料プランの GitHub Pages は Public リポジトリでのみ使えます。
（ニュースの見出しだけなので公開しても問題ない内容です）

1. リポジトリ画面上部の **⚙ Settings** をクリック
2. **General** ページを一番下までスクロール → **Danger Zone** の **Change visibility** をクリック
3. **Change to public** を選び、確認画面の指示に従って確定
   （すでに Public の場合は「Change to private」と表示されるので、何もしなくてOK）

### ② メインのブランチ名を「main」にする（おすすめ）
1. リポジトリのトップ画面で、ファイル一覧の上にあるブランチ名のボタン（`claude/...` と書かれたもの）をクリック
2. **View all branches** をクリック
3. 該当ブランチの右端にある **…**（または鉛筆アイコン）→ **Rename branch** を選び、`main` と入力して **Rename branch**

※ すでに `main` ブランチがあり、作業ブランチが別にある場合は、**Pull requests** タブ →
**New pull request** → 作業ブランチを選んで **Create pull request** → **Merge pull request** で `main` に取り込んでください。

### ③ GitHub Pages を有効にする
1. **⚙ Settings** → 左メニューの **Pages** をクリック
2. **Build and deployment** の **Source** を **GitHub Actions** に変更（選ぶだけで自動保存されます）

### ④ 初回の更新を手動で実行する
1. リポジトリ上部の **Actions** タブをクリック
   （「Workflows aren't being run on this repository」と出たら **I understand my workflows, go ahead and enable them** をクリック）
2. 左側の **ニュース更新** をクリック
3. 右側の **Run workflow** ボタン → 緑の **Run workflow** をクリック
4. 1〜2分待ち、一覧に ✅（緑のチェック）が付けば成功です
   （❌ の場合は、その行をクリックすると原因が表示されます）

### ⑤ ページを開く
- **⚙ Settings → Pages** の上部に「Your site is live at …」とURLが表示されます
- 通常は **https://ksharyobuisiness-jpg.github.io/newsdashboard/** です
- スマホで開いて、ブックマークや「ホーム画面に追加」をしておくと便利です

以後は毎朝7時ごろに自動で更新されます（GitHub側の混雑で数分〜数十分遅れることがあります）。

---

## トピックを追加・削除・変更するには

GitHub の画面だけでできます。

1. リポジトリのファイル一覧から **`topics.toml`** をクリック
2. 右上の **鉛筆アイコン（Edit this file）** をクリック
3. 内容を書き換える
   - **追加**：次の3行を一番下に貼り付けて、`name` と `query` を書き換える
     ```toml
     [[topics]]
     name = "冷凍冷蔵倉庫"
     query = "冷凍倉庫 OR 冷蔵倉庫"
     ```
   - **削除**：消したいトピックの3行（`[[topics]]`・`name`・`query`）を消す
   - **件数を変える**：`max_items = 10` の数字を変える
4. 右上の緑の **Commit changes...** → もう一度 **Commit changes** をクリック
5. 自動で再作成が始まり、1〜2分でページに反映されます（**Actions** タブで進み具合を確認できます）

### 検索ワード（query）のコツ
| 書き方 | 意味 |
|---|---|
| `物流 DX` | 両方を含む記事 |
| `港湾 OR 港運` | どちらかを含む記事 |
| `"国際物流"` | その言葉をそのまま含む記事 |
| `港湾 -ベトナム` | 「ベトナム」を含む記事を除く |
| `港湾 when:7d` | 直近7日間の記事に限る |

※ `"` を検索ワードに入れたいときは、`query = '"国際物流"'` のように外側を `'`（シングルクォーテーション）で囲みます。

---

## 手元のパソコンで試す場合（任意）
Python 3.11 以上が入っていれば、追加インストールなしで動きます。
```
python scripts/build.py
```
`public/index.html` をブラウザで開くと確認できます。
