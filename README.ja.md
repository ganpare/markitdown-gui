# MarkItDown

[![PyPI](https://img.shields.io/pypi/v/markitdown.svg)](https://pypi.org/project/markitdown/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/markitdown)
[![Built by AutoGen Team](https://img.shields.io/badge/Built%20by-AutoGen%20Team-blue)](https://github.com/microsoft/autogen)

> [!TIP]
> MarkItDownはClaudeデスクトップなどのLLMアプリケーションと統合するためのMCP（Model Context Protocol）サーバーを提供するようになりました。詳細は[markitdown-mcp](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp)をご覧ください。

> [!IMPORTANT]
> バージョン0.0.1から0.1.0への重要な変更点：
> * 依存関係が機能グループ別に整理されました（詳細は以下）。以前の動作を維持するには `pip install 'markitdown[all]'` を使用してください。
> * convert_stream()がバイナリファイルライクオブジェクト（バイナリモードで開かれたファイル、またはio.BytesIOオブジェクト）を必要とするようになりました。以前のバージョンではio.StringIOのようなテキストファイルライクオブジェクトも受け付けていましたが、これは変更されました。
> * DocumentConverterクラスのインターフェースが、ファイルパスではなくファイルライクストリームから読み込むように変更されました。*一時ファイルは作成されなくなりました*。プラグインやカスタムDocumentConverterの開発者は、コードの更新が必要かもしれません。ただし、MarkItDownクラスやCLIを使用している場合（以下の例のように）は、変更の必要はありません。

MarkItDownは、LLMや関連するテキスト分析パイプラインで使用するために、様々なファイルをMarkdownに変換する軽量なPythonユーティリティです。[textract](https://github.com/deanmalmgren/textract)と同様のツールですが、文書構造やコンテンツ（見出し、リスト、表、リンクなど）をMarkdownとして保持することに重点を置いています。出力は人間にとっても十分に読みやすいものですが、主にテキスト分析ツールでの使用を想定しており、人間が読むための高忠実度な文書変換には最適ではないかもしれません。

現在、MarkItDownは以下のフォーマットをサポートしています：

- PDF
- PowerPoint
- Word
- Excel
- 画像（EXIFメタデータとOCR）
- 音声（EXIFメタデータと音声認識）
- HTML
- テキストベースのフォーマット（CSV、JSON、XML）
- ZIPファイル（内容を順次処理）
- YouTubeのURL
- EPUB
- その他多数！

## なぜMarkdownなのか？

Markdownはプレーンテキストに非常に近く、最小限のマークアップやフォーマットで、なおかつ重要な文書構造を表現する方法を提供します。OpenAIのGPT-4oなどの主要なLLMは、Markdownを「ネイティブに理解」し、プロンプトなしでもMarkdownを応答に組み込むことがよくあります。これは、大量のMarkdown形式のテキストで学習され、それをよく理解していることを示しています。副次的な利点として、Markdownの規約はトークン効率も高くなっています。

## インストール

MarkItDownをインストールするには、pipを使用します: `pip install 'markitdown[all]'`。または、ソースからインストールすることもできます：

```bash
git clone git@github.com:microsoft/markitdown.git
cd markitdown
pip install -e 'packages/markitdown[all]'
```

## 使用方法

### コマンドライン

```bash
markitdown path-to-file.pdf > document.md
```

または `-o` を使用して出力ファイルを指定：

```bash
markitdown path-to-file.pdf -o document.md
```

パイプを使用することもできます：

```bash
cat path-to-file.pdf | markitdown
```

### オプションの依存関係
MarkItDownには、様々なファイル形式に対応するためのオプションの依存関係があります。先ほどの例では `[all]` オプションですべての依存関係をインストールしましたが、個別にインストールすることもできます。例えば：

```bash
pip install 'markitdown[pdf, docx, pptx]'
```

これはPDF、DOCX、PPTXファイルの依存関係のみをインストールします。

現在、以下のオプションの依存関係が利用可能です：

* `[all]` すべてのオプションの依存関係をインストール
* `[pptx]` PowerPointファイル用の依存関係
* `[docx]` Wordファイル用の依存関係
* `[xlsx]` Excelファイル用の依存関係
* `[xls]` 古いExcelファイル用の依存関係
* `[pdf]` PDFファイル用の依存関係
* `[outlook]` Outlookメッセージ用の依存関係
* `[az-doc-intel]` Azure Document Intelligence用の依存関係
* `[audio-transcription]` wavとmp3ファイルの音声認識用の依存関係
* `[youtube-transcription]` YouTubeビデオの字幕取得用の依存関係

### プラグイン

MarkItDownは、サードパーティ製のプラグインもサポートしています。プラグインはデフォルトでは無効になっています。インストールされているプラグインを一覧表示するには：

```bash
markitdown --list-plugins
```

プラグインを有効にするには：

```bash
markitdown --use-plugins path-to-file.pdf
```

利用可能なプラグインを探すには、GitHubでハッシュタグ `#markitdown-plugin` を検索してください。プラグインの開発については、`packages/markitdown-sample-plugin` を参照してください。

### Azure Document Intelligence

Microsoft Document Intelligenceを変換に使用するには：

```bash
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

Azure Document Intelligenceリソースのセットアップ方法については[こちら](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/create-document-intelligence-resource?view=doc-intel-4.0.0)をご覧ください。

### Python API

基本的な使用方法：

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False) # プラグインを有効にする場合はTrueに設定
result = md.convert("test.xlsx")
print(result.text_content)
```

Document Intelligenceを使用する場合：

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

画像の説明にLLMを使用する場合：

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("example.jpg")
print(result.text_content)
```

### Docker

```sh
docker build -t markitdown:latest .
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```
