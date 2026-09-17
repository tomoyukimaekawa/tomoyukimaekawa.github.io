# tomoyukimaekawa.github.io

個人ウェブサイトです。本文は `data/` のJSON、表示の共通部分は
`templates/` で管理し、Pythonで静的HTMLを生成します。
Python 3.9以降を使用します。追加パッケージは不要です。

## 編集するファイル

| ファイル | 内容 |
| --- | --- |
| `data/home.json` | 所属、学歴、職歴、授業、受賞、助成、講演、学会活動、査読、アウトリーチ、報道 |
| `data/publications.json` | 論文・解説・報告記事の書誌情報と業績一覧の分類・掲載順 |
| `data/research.json` | 研究テーマ、説明、画像、関連論文の参照 |
| `data/site.json` | ページタイトル、共通見出し、ナビゲーション |
| `templates/page.html` | 全ページ共通のHTMLレイアウト |
| `templates/styles.css` | 全ページ共通のCSS |
| `templates/research.css` | 研究ページにだけ追加するCSS |
| `imgs/` | 研究紹介の画像 |

ルートの `index.html`、`research.html`、`publications.html` は生成物です。
これらを直接編集せず、データまたはテンプレートを変更してください。
表示順はJSONの配列順です。年やIDによる自動ソートは行いません。

## 通常の更新

1. 該当するJSONを編集します（UTF-8、末尾カンマ・コメント不可）。
2. リポジトリのルートでHTMLを生成します。

   ```sh
   python3 scripts/build.py
   python3 scripts/build.py --check
   ```

3. 生成されたHTMLをブラウザで開き、差分と表示を確認します。
4. 編集したデータと生成されたHTMLを一緒にコミットします。

既存のHTMLファイル名と画像パスを維持しています。
GitHub Pagesには生成済みHTMLをそのまま配信できるため、公開設定の変更や
閲覧時のJavaScript、データ取得通信は不要です。CSSも生成時に埋め込みます。

## 経歴・講演などの追記

`data/home.json` の該当セクションの `items` 配列に項目を追加します。
`title` は任意の小見出し、`paragraphs` は段落の配列です。
既存項目をコピーし、文字列だけを編集できます。
所属セクションのように箇条書きでない場合は、セクション直下に
`paragraphs` を置きます。

段落は通常の文字列です。リンクや改行が必要な段落だけ、文字列と
リンクオブジェクト（`text`, `href`、任意の `target`, `rel`）、
改行オブジェクト（`{"break": true}`）を並べた配列にします。
リンクの前後の空白は文字列に含めます。HTMLタグは文字として表示されます。

## 論文の追記・編集

1. `data/publications.json` の `entries` に一意のIDを追加します。
   IDは固定の参照キーです。既存IDを振り直す必要はありません。
   新規IDは `maekawa-2027-short-title` など、識別しやすい名前で構いません。
2. `authors`（著者）、`title`（題名）、`publication`（掲載誌・巻号・ページ・年）を入力します。
   元の表記をそのまま再現するため、著者末尾のカンマや題名の引用符などの
   句読点もデータに含めます。`link` は省略可能です。
3. `categories` の該当分類の `publications` 配列に、そのIDを希望の位置で追加します。
   各論文は業績一覧のいずれか1分類に1回だけ登録します。
4. 研究紹介にも載せる場合は、`data/research.json` の該当テーマの
   `related_work` に `{"id": "追加したID"}` を追加します。

同じ論文の書誌情報は原則 `entries` の1か所で編集します。
研究ページにだけ別の表記を使う場合は、その参照に `overrides` を指定できます。
現在のPassStylesの参照には、移行前からの著者区切りの表記差を保つため
`authors` の上書きがあります。このフィールドは共通情報の変更より優先されます。

研究テーマの画像は `images` 配列で管理し、`src`、`alt`、`width` を指定します。
`group_images: true` は既存の2枚組画像用のラッパーを生成します。

## 検証

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
```

生成漏れ、確認済みの内容・構造の保持、文字列のエスケープ、論文参照切れ、
分類への未登録をテストします。ビルド自体も論文の重複登録、参照切れ、
画像の欠落、JSONのキー重複などを検出し、全ページの生成に成功してから書き込みます。

`tests/expected_fingerprints.json` は確認済みの最新HTMLから取得した比較基準です。
整形用の空白と省略可能な閉じタグを除き、本文・要素・属性・CSSを比較します。
**今後、意図的に公開内容やデザインを変更した場合**は、生成結果の差分と表示を
確認したうえで、次のコマンドで比較基準を更新し、テストを再実行してください。
構造整理だけの変更では基準を更新せず、一致することを確認します。

```sh
python3 - <<'PY'
import json
import sys
from pathlib import Path
sys.path.insert(0, 'tests')
from test_build import fingerprint
pages = ('index.html', 'research.html', 'publications.html')
Path('tests/expected_fingerprints.json').write_text(
    json.dumps({name: fingerprint(Path(name).read_text(encoding='utf-8'))
                for name in pages}, indent=2) + '\n', encoding='utf-8')
PY
python3 -m unittest discover -s tests -v
```

公開情報に基づく追記の出典・英訳方針は [docs/content-sources.md](docs/content-sources.md) に記録しています。
